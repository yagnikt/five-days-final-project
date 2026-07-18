import json
import asyncio
from typing import Tuple, Dict, Any, Optional
from google.genai import types
from google.adk import Runner
from google.adk.sessions import InMemorySessionService

from itinerary_agent import travel_agent, ItineraryProposal
from evaluator_agent import evaluator_agent, EvaluationResult
from security import sanitize_and_validate_input


def _log_to_firestore(request_id: Optional[str], message: str) -> None:
    """
    Utility helper to log messages both to the server console and to Firestore.
    """
    print(message)
    if request_id:
        try:
            from database import add_request_log
            add_request_log(request_id, message)
        except Exception as e:
            print(f"⚠️ Failed to write log to Firestore: {e}")


async def orchestrate_itinerary_generation(
    query: str,
    user_id: str,
    session_id: str,
    session_service: Optional[Any] = None,
    max_retries: int = 3,
    request_id: Optional[str] = None
) -> Tuple[Dict[str, Any], Dict[str, Any], int]:
    """
    Orchestrates the generation of a travel itinerary using a primary agent,
    running a feedback and self-correction loop powered by an LLM-as-a-judge evaluator.
    
    Args:
        query: The user's travel preferences.
        user_id: The ID of the user requesting the itinerary.
        session_id: The active session ID.
        session_service: An optional session service instance. If None, an InMemorySessionService is created.
        max_retries: Maximum number of correction retries if evaluation fails.
        request_id: An optional ID tracking the request's state and logs in Firestore.
        
    Returns:
        A tuple of (final_itinerary_dict, evaluation_details_dict, retry_count).
    """
    # 0. Validate and Sanitize Input
    _log_to_firestore(request_id, "Validating and sanitizing user inputs...")
    is_safe, validation_result = sanitize_and_validate_input(query)
    if not is_safe:
        _log_to_firestore(request_id, f"⚠️ Input Validation Failed: {validation_result}")
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
        
        if request_id:
            try:
                from database import update_request_status
                update_request_status(request_id, "failed", fallback_itinerary, fallback_eval)
            except Exception as e:
                print(f"⚠️ Failed to update failed status in Firestore: {e}")
                
        return fallback_itinerary, fallback_eval, 0

    # Use sanitized query for subsequent calls
    query = validation_result

    # 1. Initialize Session Service if not provided, and ensure session is created
    if session_service is None:
        session_service = InMemorySessionService()
        
    try:
        await session_service.get_session(app_name="agents", user_id=user_id, session_id=session_id)
    except Exception:
        await session_service.create_session(app_name="agents", user_id=user_id, session_id=session_id)
        
    # Create the primary agent runner
    primary_runner = Runner(agent=travel_agent, session_service=session_service, app_name="agents")
    
    # We also create an isolated session service and runner for the evaluator agent
    eval_session_service = InMemorySessionService()
    eval_session_id = f"eval_{session_id}"
    await eval_session_service.create_session(app_name="agents", user_id="eval_system", session_id=eval_session_id)
    evaluator_runner = Runner(agent=evaluator_agent, session_service=eval_session_service, app_name="agents")
    
    # Package the initial user query
    current_user_message = types.Content(
        role="user",
        parts=[types.Part(text=query)]
    )
    
    retry_count = 0
    last_itinerary_proposal = {}
    last_evaluation = {}
    
    _log_to_firestore(request_id, f"🎬 Starting Orchestrated Generation. User Query: '{query}'")
    
    while retry_count <= max_retries:
        _log_to_firestore(request_id, f"🔄 [Iteration {retry_count} / Max {max_retries}]")
        _log_to_firestore(request_id, "⏳ running primary planning agent...")
        
        # Run primary agent to get itinerary proposal
        event_generator = primary_runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=current_user_message
        )
        
        proposal_text = ""
        for event in event_generator:
            func_calls = event.get_function_calls()
            if func_calls:
                for fc in func_calls:
                    _log_to_firestore(request_id, f"   🔍 [AGENT TOOL CALL]: {fc.name} with args: {fc.args}")
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        proposal_text += part.text
                        
        proposal_text = proposal_text.strip()
        
        # Clean any markdown block wrappers around the JSON
        if proposal_text.startswith("```json"):
            proposal_text = proposal_text[7:]
        if proposal_text.endswith("```"):
            proposal_text = proposal_text[:-3]
        proposal_text = proposal_text.strip()
        
        try:
            itinerary_dict = json.loads(proposal_text)
            last_itinerary_proposal = itinerary_dict
        except json.JSONDecodeError:
            _log_to_firestore(request_id, "❌ Failed to parse proposal text as JSON.")
            itinerary_dict = {
                "destination": "Unknown",
                "summary": "Failed to parse itinerary",
                "total_estimated_cost": 0.0,
                "fallback_requested": True,
                "fallback_message": "The system generated an invalid response. Please try again with different preferences."
            }
            last_itinerary_proposal = itinerary_dict
            
        # Check if the primary agent itself raised a fallback
        if itinerary_dict.get("fallback_requested"):
            _log_to_firestore(request_id, "⚠️ Primary agent triggered fallback pathway directly.")
            last_evaluation = {
                "score": 1.0,
                "feasibility_rating": 1.0,
                "quality_rating": 1.0,
                "constraint_adherence": 1.0,
                "feedback": "Valid fallback explanation provided.",
                "passed": True
            }
            
            if request_id:
                try:
                    from database import move_to_pending_approval
                    move_to_pending_approval(request_id, user_id, session_id, query, last_itinerary_proposal, last_evaluation)
                except Exception as e:
                    print(f"⚠️ Failed to commit fallback to pending_approvals: {e}")
                    
            return last_itinerary_proposal, last_evaluation, retry_count
            
        _log_to_firestore(request_id, "⏳ running LLM-as-a-judge evaluation...")
        
        # Evaluate the generated itinerary proposal using the evaluator agent
        eval_input = (
            f"User Preferences / Query: {query}\n\n"
            f"Generated Itinerary Proposal (JSON):\n{json.dumps(itinerary_dict, indent=2)}"
        )
        
        eval_message = types.Content(
            role="user",
            parts=[types.Part(text=eval_input)]
        )
        
        eval_event_generator = evaluator_runner.run(
            user_id="eval_system",
            session_id=eval_session_id,
            new_message=eval_message
        )
        
        eval_text = ""
        for event in eval_event_generator:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        eval_text += part.text
                        
        eval_text = eval_text.strip()
        
        if eval_text.startswith("```json"):
            eval_text = eval_text[7:]
        if eval_text.endswith("```"):
            eval_text = eval_text[:-3]
        eval_text = eval_text.strip()
        
        try:
            eval_dict = json.loads(eval_text)
            last_evaluation = eval_dict
        except json.JSONDecodeError:
            _log_to_firestore(request_id, "❌ Failed to parse evaluation response as JSON.")
            eval_dict = {
                "score": 0.5,
                "feasibility_rating": 0.5,
                "quality_rating": 0.5,
                "constraint_adherence": 0.5,
                "feedback": "Evaluation model produced non-JSON format. Requesting regeneration.",
                "passed": False
            }
            last_evaluation = eval_dict
            
        _log_to_firestore(request_id, f"📈 Evaluation Score: {eval_dict.get('score')} | Passed: {eval_dict.get('passed')}")
        _log_to_firestore(request_id, f"💬 Feedback: {eval_dict.get('feedback')}")
        
        if eval_dict.get("passed"):
            _log_to_firestore(request_id, "🎉 Success! Itinerary passed quality evaluation threshold.")
            
            if request_id:
                try:
                    from database import move_to_pending_approval
                    move_to_pending_approval(request_id, user_id, session_id, query, last_itinerary_proposal, last_evaluation)
                except Exception as e:
                    print(f"⚠️ Failed to commit proposal to pending_approvals: {e}")
                    
            return last_itinerary_proposal, last_evaluation, retry_count
            
        # If we failed to pass, prepare feedback message to refine the itinerary in the next iteration
        retry_count += 1
        if retry_count <= max_retries:
            refinement_prompt = (
                f"Your previous itinerary proposal was evaluated and DID NOT pass our quality standards (Score: {eval_dict.get('score')}).\n"
                f"Please refine and correct the itinerary to address the following feedback:\n"
                f"--- FEEDBACK ---\n"
                f"{eval_dict.get('feedback')}\n"
                f"----------------\n"
                f"Ensure your next output is a fully complete, improved ItineraryProposal JSON addressing these points precisely."
            )
            current_user_message = types.Content(
                role="user",
                parts=[types.Part(text=refinement_prompt)]
            )
            
    _log_to_firestore(request_id, "⚠️ Reached max retries without a passing score. Committing best available proposal as pending review.")
    if request_id:
        try:
            from database import move_to_pending_approval
            move_to_pending_approval(request_id, user_id, session_id, query, last_itinerary_proposal, last_evaluation)
        except Exception as e:
            print(f"⚠️ Failed to commit fallback to pending_approvals: {e}")
            
    return last_itinerary_proposal, last_evaluation, retry_count
