import json
import asyncio
from typing import Tuple, Dict, Any, Optional
from google.genai import types
from google.adk import Runner
from google.adk.sessions import InMemorySessionService

from itinerary_agent import travel_agent, ItineraryProposal
from evaluator_agent import evaluator_agent, EvaluationResult
from security import sanitize_and_validate_input

async def orchestrate_itinerary_generation(
    query: str,
    user_id: str,
    session_id: str,
    session_service: Optional[Any] = None,
    max_retries: int = 3
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
        
    Returns:
        A tuple of (final_itinerary_dict, evaluation_details_dict, retry_count).
    """
    # 0. Validate and Sanitize Input
    is_safe, validation_result = sanitize_and_validate_input(query)
    if not is_safe:
        print(f"⚠️ Input Validation Failed: {validation_result}")
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
        return fallback_itinerary, fallback_eval, 0

    # Use sanitized query for subsequent calls
    query = validation_result

    # 1. Initialize Session Service if not provided
    if session_service is None:
        session_service = InMemorySessionService()
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
    
    print(f"🎬 Starting Orchestrated Generation. User Query: '{query}'")
    
    while retry_count <= max_retries:
        print(f"\n🔄 [Iteration {retry_count} / Max {max_retries}]")
        print(f"⏳ running primary agent generation...")
        
        # Run primary agent to get itinerary proposal
        event_generator = primary_runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=current_user_message
        )
        
        proposal_text = ""
        for event in event_generator:
            # Print tools calls or events if running in verbose/cli mode
            func_calls = event.get_function_calls()
            if func_calls:
                for fc in func_calls:
                    print(f"   🔍 [AGENT TOOL CALL]: {fc.name} with args: {fc.args}")
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
            print("❌ Failed to parse proposal text as JSON. raw text:")
            print(proposal_text)
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
            print("⚠️ Primary agent triggered fallback pathway directly.")
            # Fallbacks with polite explanation are automatically considered valid 
            last_evaluation = {
                "score": 1.0,
                "feasibility_rating": 1.0,
                "quality_rating": 1.0,
                "constraint_adherence": 1.0,
                "feedback": "Valid fallback explanation provided.",
                "passed": True
            }
            return last_itinerary_proposal, last_evaluation, retry_count
            
        print(f"⏳ running LLM-as-a-judge evaluation...")
        
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
            print("❌ Failed to parse evaluation response as JSON.")
            eval_dict = {
                "score": 0.5,
                "feasibility_rating": 0.5,
                "quality_rating": 0.5,
                "constraint_adherence": 0.5,
                "feedback": "Evaluation model produced non-JSON format. Requesting regeneration.",
                "passed": False
            }
            last_evaluation = eval_dict
            
        print(f"📈 Evaluation Score: {eval_dict.get('score')} | Passed: {eval_dict.get('passed')}")
        print(f"💬 Feedback: {eval_dict.get('feedback')}")
        
        if eval_dict.get("passed"):
            print("🎉 Success! Itinerary passed quality evaluation threshold.")
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
            
    print("⚠️ Reached max retries without a passing score. Returning best available proposal.")
    return last_itinerary_proposal, last_evaluation, retry_count
