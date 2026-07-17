import os
import sys
from dotenv import load_dotenv

# Load local environment variables from .env file
load_dotenv()

# Verify that credentials are in place before running
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("WARNING: GEMINI_API_KEY environment variable not found in .env.")
    print("Please make sure you have added it so that the Gemini API can authenticate.")

print("Initializing test agent using Google ADK...")

try:
    # Google ADK is designed to build modular, orchestrated agents
    from google.adk.agents import Agent
    from google.adk.tools import google_search

    # Define the primary generative travel planner agent
    travel_agent = Agent(
        name="primary_travel_agent",
        model="gemini-3.1-pro", # Using Pro model for high-reasoning planning tasks
        instruction=(
            "You are an expert AI Travel Itinerary Planner. Your goal is to construct "
            "comprehensive, high-quality, and highly feasible weekend getaway plans based "
            "on user preferences. Always use the google_search tool to find accurate and "
            "up-to-date options for flights, events, hotels, and timings."
        ),
        tools=[google_search]
    )

    print("Success: Google ADK Agent initialized with Google Search tool!")
    print("\n--- Next Steps for Phase 2 ---")
    print("To test the agent with a real prompt, run this script inside your active virtual environment:")
    print("  $ python test_agent.py")
    print("Ensure you have set a valid GEMINI_API_KEY in your backend/.env file.")

except Exception as e:
    print(f"Error during agent initialization: {e}")
    print("\nAttempting fallback check using standard google-genai SDK...")
    try:
        from google import genai
        from google.genai import types

        client = genai.Client()
        print("Success: Raw google-genai Client successfully imported and verified!")
    except Exception as fallback_err:
        print(f"Fallback import check also encountered error: {fallback_err}")
