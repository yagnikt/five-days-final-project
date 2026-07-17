import os
import sys
import json
import argparse
from dotenv import load_dotenv

# Load local environment variables from .env file
load_dotenv()

# Verify that credentials are in place before running
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("ERROR: GEMINI_API_KEY environment variable not found in .env.")
    print("Please make sure you have added it so that the Gemini API can authenticate.")
    sys.exit(1)

try:
    from google.genai import types
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    from itinerary_agent import travel_agent
except ImportError as e:
    print(f"ERROR: Failed to import Google ADK or GenAI modules: {e}")
    sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Test Google ADK Travel Itinerary Planner.")
    parser.add_argument(
        "--query",
        type=str,
        default="Weekend getaway from NYC to Washington DC next month, budget $600, museum tours and nice restaurants",
        help="The travel preferences query to send to the planner."
    )
    args = parser.parse_args()

    print("\n" + "="*80)
    print("🚀 INITIALIZING GOOGLE ADK TRAVEL PLANNER AGENT CLI")
    print("="*80)
    print(f"User Query: '{args.query}'\n")

    import asyncio
    # Initialize in-memory session and runner
    session_service = InMemorySessionService()
    asyncio.run(session_service.create_session(app_name="agents", user_id="test_user", session_id="test_session_1"))
    runner = Runner(agent=travel_agent, session_service=session_service, app_name="agents")

    # Package the query into a Content object
    user_message = types.Content(
        role="user",
        parts=[types.Part(text=args.query)]
    )

    print("⏳ Executing Travel Planning agent (with real-time Google Search grounding)...")
    print("This may take 15-30 seconds depending on flight/hotel searches.\n")

    try:
        # Run the agent in sync mode
        event_generator = runner.run(
            user_id="test_user",
            session_id="test_session_1",
            new_message=user_message
        )

        final_response_text = ""

        for event in event_generator:
            # Let's inspect events
            author = event.author
            
            # Print function calls (like Google Search) if any
            func_calls = event.get_function_calls()
            if func_calls:
                for fc in func_calls:
                    print(f"🔍 [AGENT CALLS TOOL]: {fc.name} with args: {fc.args}")

            # Print function responses if any
            func_responses = event.get_function_responses()
            if func_responses:
                for fr in func_responses:
                    # Grounding results can be large, so we summarize
                    print(f"📥 [TOOL RETURNED DATA] from: {fr.name}")

            # Extract any text generated along the way
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        # Append to our final response holder
                        final_response_text += part.text

        print("\n" + "="*80)
        print("✅ AGENT RUN COMPLETED")
        print("="*80)

        # Parse and pretty print the structured output
        if final_response_text:
            try:
                # Clean up any potential markdown code fences in the text output
                cleaned_text = final_response_text.strip()
                if cleaned_text.startswith("```json"):
                    cleaned_text = cleaned_text[7:]
                if cleaned_text.endswith("```"):
                    cleaned_text = cleaned_text[:-3]
                cleaned_text = cleaned_text.strip()

                parsed_json = json.loads(cleaned_text)
                
                print("\n📋 STRUCTURED ITINERARY PROPOSAL (JSON):")
                print(json.dumps(parsed_json, indent=2))
                
                # Check for fallback
                if parsed_json.get("fallback_requested"):
                    print("\n⚠️  FALLBACK PATH TRIGGERED:")
                    print(f"Message: {parsed_json.get('fallback_message')}")
                else:
                    print("\n🎉 SUCCESSFUL ITINERARY PROPOSAL:")
                    print(f"Destination: {parsed_json.get('destination')}")
                    print(f"Summary: {parsed_json.get('summary')}")
                    print(f"Estimated Cost: ${parsed_json.get('total_estimated_cost')}")
                    print(f"Flights: {len(parsed_json.get('flights', []))} option(s)")
                    print(f"Lodging: {parsed_json.get('accommodation', {}).get('name') if parsed_json.get('accommodation') else 'None'}")
                    print(f"Itinerary: {len(parsed_json.get('itinerary_days', []))} day(s)")
                
            except json.JSONDecodeError:
                print("⚠️ Warning: Output was not valid JSON, raw text response:")
                print(final_response_text)
        else:
            print("⚠️ No output received from the agent.")

    except Exception as e:
        print(f"\n❌ Execution encountered an error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
