import os
import uuid
import asyncio
from fastapi import FastAPI, BackgroundTasks, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

from google.adk.sessions import VertexAiSessionService, InMemorySessionService
from orchestrator import orchestrate_itinerary_generation
import database as db

# Initialize FastAPI App
app = FastAPI(
    title="AI-Driven Travel Itinerary Planner API",
    description="Backend orchestration gateway featuring automated LLM-as-a-judge evaluation and stateful HITL administration.",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production security if needed
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure the Google Agent Memory Bank Service (with InMemory fallback for local development)
reasoning_engine_id = os.getenv("REASONING_ENGINE_ID")
if reasoning_engine_id:
    session_service = VertexAiSessionService(
        project=os.getenv("GCP_PROJECT", "five-days-final-project"),
        location=os.getenv("GCP_REGION", "us-central1"),
        agent_engine_id=reasoning_engine_id
    )
else:
    print("ℹ️ REASONING_ENGINE_ID not set. Falling back to InMemorySessionService for local development.")
    session_service = InMemorySessionService()


# Input Schemas
class TravelRequest(BaseModel):
    query: str = Field(..., description="The user's travel preferences.")
    user_id: str = Field(..., description="Unique client identifier.")
    session_id: str = Field(..., description="Active session ID for the user's conversational profile.")


class RejectRequest(BaseModel):
    reason: Optional[str] = Field(None, description="Optional explanation for rejecting the proposal.")


# Background Execution Wrapper
async def run_orchestration_background(request_id: str, query: str, user_id: str, session_id: str):
    try:
        # Run orchestrator, passing our VertexAiSessionService for Agent Memory Bank integration
        await orchestrate_itinerary_generation(
            query=query,
            user_id=user_id,
            session_id=session_id,
            session_service=session_service,
            max_retries=3,
            request_id=request_id
        )
    except Exception as e:
        # Catch unexpected exceptions and update request status
        db.add_request_log(request_id, f"❌ Unexpected Orchestrator Exception: {str(e)}")
        db.update_request_status(request_id, "failed")


# API Routes

@app.get("/")
def read_root():
    """Friendly root endpoint directing users to the frontend application."""
    return {
        "message": "AeroPlan AI Travel Itinerary Planner API is running!",
        "health_check_endpoint": "/health",
        "frontend_app_url": "http://localhost:5173"
    }


@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    """Verify backend API and database connection status."""
    return {"status": "healthy", "project": os.getenv("GCP_PROJECT", "five-days-final-project")}


@app.post("/api/request", status_code=status.HTTP_202_ACCEPTED)
async def create_request(req: TravelRequest, background_tasks: BackgroundTasks):
    """
    Accepts a new travel request, logs it to Firestore, and starts the generation loop in a background thread.
    """
    request_id = str(uuid.uuid4())
    
    # Create request document in Firestore (status is set to 'processing' initially)
    db.create_itinerary_request(request_id, req.user_id, req.session_id, req.query)
    
    # Trigger orchestrator in a background worker task
    background_tasks.add_task(
        run_orchestration_background,
        request_id=request_id,
        query=req.query,
        user_id=req.user_id,
        session_id=req.session_id
    )
    
    return {
        "message": "Itinerary generation started successfully.",
        "request_id": request_id
    }


@app.get("/api/status/{id}")
def get_status(id: str):
    """
    Fetch the real-time status and step-by-step logs of an active request.
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
