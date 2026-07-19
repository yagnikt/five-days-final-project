# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import contextlib
import os
import uuid
from collections.abc import AsyncIterator
from typing import Optional, List, Dict, Any

import google.auth
from a2a.server.tasks import InMemoryTaskStore
from dotenv import load_dotenv
from fastapi import FastAPI, BackgroundTasks, HTTPException, status, Request
from pydantic import BaseModel, Field
from google.adk.cli.fast_api import get_fast_api_app
from google.adk.runners import Runner
from google.cloud import logging as google_cloud_logging

from backend.app.app_utils import services
from backend.app.app_utils.a2a import attach_a2a_routes
from backend.app.app_utils.reasoning_engine_adapter import (
    attach_reasoning_engine_routes,
)
from backend.app.app_utils.telemetry import (
    setup_agent_engine_telemetry,
    setup_telemetry,
)
from backend.app.app_utils.typing import Feedback

from backend.app import database as db
from backend.app.security import sanitize_and_validate_input

load_dotenv()
setup_telemetry()
# Must run before get_fast_api_app to set the tracer provider resource.
setup_agent_engine_telemetry()
_, project_id = google.auth.default()
logging_client = google_cloud_logging.Client()
logger = logging_client.logger(__name__)
allow_origins = (
    os.getenv("ALLOW_ORIGINS", "").split(",") if os.getenv("ALLOW_ORIGINS") else None
)

AGENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Runner for the A2A path, sharing the same session/artifact services as the
    # adk_api and reasoning_engine paths (see services.py). Imported here so the
    # agent is built after env/telemetry setup.
    from backend.app import backend as adk_app
    from backend.app import root_agent

    runner = Runner(
        app=adk_app,
        session_service=services.get_session_service(),
        artifact_service=services.get_artifact_service(),
        auto_create_session=True,
    )
    # Shared by the A2A path and the reasoning_engine adapter routes.
    app.state.runner = runner
    app.state.agent_app_name = adk_app.name
    await attach_a2a_routes(
        app,
        agent=root_agent,
        runner=runner,
        task_store=InMemoryTaskStore(),
        rpc_path=f"/a2a/{adk_app.name}",
    )
    yield


app: FastAPI = get_fast_api_app(
    agents_dir=AGENT_DIR,
    web=True,
    artifact_service_uri=services.ARTIFACT_SERVICE_URI,
    allow_origins=allow_origins,
    session_service_uri=services.SESSION_SERVICE_URI,
    otel_to_cloud=False,
    lifespan=lifespan,
)
app.title = "backend"
app.description = "API for interacting with the Agent backend"


# Proxy routes so the Vertex AI Console Playground (reasoning_engine SDK) can
# talk to this agent alongside the native adk_api routes.
attach_reasoning_engine_routes(app)


# Custom REST API Models
class TravelRequest(BaseModel):
    query: str = Field(..., description="The user's travel preferences.")
    user_id: str = Field(..., description="Unique client identifier.")
    session_id: str = Field(..., description="Active session ID for the user's conversational profile.")


class RejectRequest(BaseModel):
    reason: Optional[str] = Field(None, description="Optional explanation for rejecting the proposal.")


async def run_orchestration_background(
    request_id: str,
    query: str,
    user_id: str,
    session_id: str,
    runner: Runner
):
    """
    Background worker task utilizing ADK Runner.run_async on root_agent (itinerary_refinement_loop)
    to perform safety checks, generate itineraries, run LLM-as-a-judge evaluation,
    and persist results.
    """
    try:
        # 1. Input Safety Validation
        db.add_request_log(request_id, "Validating and sanitizing user inputs...")
        is_safe, validation_result = sanitize_and_validate_input(query)
        if not is_safe:
            db.add_request_log(request_id, f"⚠️ Input Validation Failed: {validation_result}")
            fallback_itinerary = {
                "destination": "Unknown",
                "summary": "Request was blocked by safety validation guardrails.",
                "total_estimated_cost": 0.0,
                "fallback_requested": True,
                "fallback_message": validation_result
            }
            fallback_eval = {
                "score": 0.0,
                "feasibility_rating": 0.0,
                "quality_rating": 0.0,
                "constraint_adherence": 0.0,
                "feedback": f"Input failed safety check: {validation_result}",
                "passed": False
            }
            db.update_request_status(request_id, "failed", fallback_itinerary, fallback_eval)
            return

        sanitized_query = validation_result
        db.add_request_log(request_id, f"🎬 Starting Orchestrated Generation. User Query: '{sanitized_query}'")

        # 2. Package the query into a Content object
        from google.genai import types
        user_message = types.Content(
            role="user",
            parts=[types.Part(text=sanitized_query)]
        )

        current_agent = None
        # Consume the async generator returned by runner.run_async
        async for event in runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=user_message
        ):
            author = event.author or "Agent"
            
            # If the executing agent changes, write a log message to Firestore
            if author != current_agent:
                current_agent = author
                if author == "itinerary_agent":
                    db.add_request_log(request_id, "⏳ Running itinerary planning agent (with real-time Google Search grounding)...")
                elif author == "evaluator_agent":
                    db.add_request_log(request_id, "⏳ Running LLM-as-a-judge quality evaluation agent...")
                elif author == "escalation_checker":
                    db.add_request_log(request_id, "🔍 Analyzing evaluation results and checking escalation criteria...")

            # Log tool calls
            func_calls = event.get_function_calls()
            if func_calls:
                for fc in func_calls:
                    db.add_request_log(request_id, f"   🔍 [AGENT TOOL CALL]: {fc.name} with args: {fc.args}")

            # Log tool responses
            func_responses = event.get_function_responses()
            if func_responses:
                for fr in func_responses:
                    db.add_request_log(request_id, f"   📥 [TOOL RETURNED DATA] from: {fr.name}")

        db.add_request_log(request_id, "🏁 Runner loop completed. Retrieving final state...")

        # 3. Retrieve final session state
        session = await runner.session_service.get_session(
            app_name=runner.app.name,
            user_id=user_id,
            session_id=session_id
        )
        
        final_itinerary = session.state.get("itinerary_proposal")
        final_evaluation = session.state.get("evaluation_result")
        
        if final_evaluation and not isinstance(final_evaluation, dict):
            final_evaluation = final_evaluation.model_dump()
            
        if not final_itinerary:
            final_itinerary = {
                "destination": "Unknown",
                "summary": "No itinerary was successfully generated.",
                "total_estimated_cost": 0.0,
                "fallback_requested": True,
                "fallback_message": "An error occurred and no itinerary was produced."
            }
        if not final_evaluation:
            final_evaluation = {
                "score": 0.0,
                "feasibility_rating": 0.0,
                "quality_rating": 0.0,
                "constraint_adherence": 0.0,
                "feedback": "Evaluation was skipped or failed.",
                "passed": False
            }
            
        passed = final_evaluation.get("passed", False)
        score = final_evaluation.get("score", 0.0)
        feedback = final_evaluation.get("feedback", "")
        
        db.add_request_log(request_id, f"📈 Final Evaluation Score: {score} | Passed: {passed}")
        if feedback:
            db.add_request_log(request_id, f"💬 Judge Feedback: {feedback}")
            
        if passed:
            db.add_request_log(request_id, "🎉 Success! Itinerary passed quality evaluation threshold. Moved to Pending approvals.")
        else:
            db.add_request_log(request_id, "⚠️ Reached max iterations or failed evaluation. Moved to Pending approvals for manual review.")
            
        # Commit results to Firestore pending approvals
        db.move_to_pending_approval(
            request_id=request_id,
            user_id=user_id,
            session_id=session_id,
            query=query,
            itinerary=final_itinerary,
            evaluation=final_evaluation
        )

    except Exception as e:
        import traceback
        error_msg = f"❌ Unexpected Orchestrator Exception: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        db.add_request_log(request_id, f"❌ Unexpected Orchestrator Exception: {str(e)}")
        db.update_request_status(request_id, "failed")


# Custom API Routes

@app.post("/api/request", status_code=status.HTTP_202_ACCEPTED)
async def create_request(
    req: TravelRequest,
    background_tasks: BackgroundTasks,
    request: Request
):
    """
    Accepts a new travel request, logs it to Firestore, and starts the generation loop using
    the ADK Runner inside a background worker task.
    """
    request_id = str(uuid.uuid4())
    
    # Create request document in Firestore (status set to 'processing' initially)
    db.create_itinerary_request(request_id, req.user_id, req.session_id, req.query)
    
    # Grab the active Runner from the FastAPI app state
    runner = request.app.state.runner
    
    # Trigger background worker task
    background_tasks.add_task(
        run_orchestration_background,
        request_id=request_id,
        query=req.query,
        user_id=req.user_id,
        session_id=req.session_id,
        runner=runner
    )
    
    return {
        "message": "Itinerary generation started successfully.",
        "request_id": request_id
    }


@app.get("/api/status/{id}")
def get_status(id: str):
    """
    Fetch the real-time status and step-by-step logs of an active request from Firestore.
    """
    req_data = db.get_itinerary_request(id)
    if not req_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request with ID {id} not found."
        )
    return req_data


@app.get("/api/pending")
def get_pending():
    """
    Fetch the list of all pending proposals waiting for HITL admin review.
    """
    try:
        return db.get_pending_approvals()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pending queue: {str(e)}"
        )


@app.post("/api/approve/{id}")
def approve_proposal(id: str):
    """
    Approve an itinerary proposal, publishing it to the approved list.
    """
    success = db.approve_itinerary(id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pending proposal with ID {id} not found."
        )
    return {"message": f"Proposal {id} successfully approved."}


@app.post("/api/reject/{id}")
def reject_proposal(id: str, req: Optional[RejectRequest] = None):
    """
    Reject an itinerary proposal, with an optional explanation.
    """
    reason = req.reason if req else None
    success = db.reject_itinerary(id, reason=reason)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pending proposal with ID {id} not found."
        )
    return {"message": f"Proposal {id} rejected."}


@app.post("/feedback")
def collect_feedback(feedback: Feedback) -> dict[str, str]:
    """Collect and log feedback.

    Args:
        feedback: The feedback data to log

    Returns:
        Success message
    """
    logger.log_struct(feedback.model_dump(), severity="INFO")
    return {"status": "success"}


# Main execution
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
