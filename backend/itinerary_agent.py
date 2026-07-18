import os
from typing import List, Optional
from pydantic import BaseModel, Field, AliasChoices
from google.genai import types
from google.genai.types import SafetySetting, HarmCategory, HarmBlockThreshold
from google.adk.agents import Agent
from google.adk.tools import google_search

# ----------------------------------------------------------------------
# 1. Define Pydantic output schemas for structured itinerary responses
# ----------------------------------------------------------------------

class FlightDetails(BaseModel):
    """Detailed information for a single flight leg."""
    flight_number: str = Field(description="The flight number (e.g., UA1234 or AA456).")
    airline: str = Field(description="Name of the airline operating the flight.")
    departure_time: str = Field(description="Departure time with timezone if known (e.g., 2026-08-14T18:30:00).")
    arrival_time: str = Field(description="Arrival time with timezone if known (e.g., 2026-08-14T21:45:00).")
    departure_airport: str = Field(description="IATA code and name of the departure airport.")
    arrival_airport: str = Field(description="IATA code and name of the arrival airport.")
    price: float = Field(description="Estimated price of the flight leg in USD.")

class HotelDetails(BaseModel):
    """Detailed information for hotel accommodations."""
    name: str = Field(
        validation_alias=AliasChoices('name', 'hotel_name'),
        description="Name of the hotel or accommodation."
    )
    address: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices('address', 'location'),
        description="Physical address or location of the hotel. If full street address is not found, specify the neighborhood or region."
    )
    price_per_night: Optional[float] = Field(
        default=0.0,
        validation_alias=AliasChoices('price_per_night', 'cost_per_night'),
        description="Estimated price per night in USD."
    )
    rating: Optional[float] = Field(default=None, description="Average guest rating of the hotel (e.g., 4.5).")
    booking_link: Optional[str] = Field(default=None, description="A direct booking or reference link, if found.")

class ActivityDetails(BaseModel):
    """Details of a scheduled activity or attraction."""
    time: str = Field(description="Approximate start time or range (e.g., '09:00 AM' or 'Afternoon').")
    title: str = Field(description="Name of the activity or attraction.")
    description: str = Field(description="Brief explanation of the activity and what makes it special.")
    location: str = Field(description="Name/address of where the activity takes place.")
    cost: Optional[float] = Field(default=0.0, description="Cost of entry or ticket in USD, or 0 if free.")

class DayItinerary(BaseModel):
    """Itinerary for a single day of the weekend trip."""
    day_number: int = Field(description="The sequential day number (e.g., 1 for Friday, 2 for Saturday, etc.).")
    date: str = Field(description="The date of this itinerary day (e.g., 'Friday, August 14, 2026').")
    activities: List[ActivityDetails] = Field(description="Chronological list of activities for this day.")

class ItineraryProposal(BaseModel):
    """The final structured travel itinerary proposal or fallback notification."""
    destination: str = Field(description="The destination city/region of the getaway.")
    summary: str = Field(description="A brief, engaging summary of the weekend trip experience.")
    total_estimated_cost: float = Field(description="Sum of all flights, hotel nights, and activities in USD.")
    flights: List[FlightDetails] = Field(default_factory=list, description="A list of suggested flight options or travel legs.")
    accommodation: Optional[HotelDetails] = Field(default=None, description="Suggested lodging option.")
    itinerary_days: List[DayItinerary] = Field(default_factory=list, description="Day-by-day weekend schedule.")
    
    # Fallback Handling
    fallback_requested: bool = Field(
        default=False, 
        description="Must be set to True if Google Search returns no results, if constraints are physically impossible (e.g., fly NYC to Paris for $10 tomorrow), or if you are unable to construct a high-quality, grounded itinerary."
    )
    fallback_message: Optional[str] = Field(
        default=None, 
        description="If fallback_requested is True, provide a helpful and polite explanation describing what search criteria or budgets were too tight and recommend how the user can broaden their preferences (e.g., larger budget, different dates)."
    )

from google.adk.agents.callback_context import CallbackContext

# ----------------------------------------------------------------------
# 2. Define System Prompt & Instructions
# ----------------------------------------------------------------------

SYSTEM_INSTRUCTION = (
    "You are an expert, premium AI Travel Itinerary Planner. Your goal is to construct "
    "highly feasible, comprehensive, and engaging weekend getaway plans based on user preferences.\n\n"
    
    "{feedback_instruction}\n\n"
    
    "CRITICAL RULES & OPERATING PROCEDURES:\n"
    "1. REAL-WORLD DATA GROUNDING: You MUST run the google_search tool to find accurate, real, "
    "and up-to-date options for flights, events, hotels, and timings. Do not invent flight numbers, "
    "hotel names, prices, or activity availability.\n"
    "2. DATE FEASIBILITY: Ensure the flight schedules, lodging, and activities align. For a typical "
    "weekend getaway, focus on a Friday evening to Sunday afternoon/evening schedule.\n"
    "3. COST ACCURACY: Give realistic prices and keep the total cost within the user's requested budget. "
    "Sum the prices of flights, accommodations (multiplied by the number of nights), and activity ticket "
    "costs to calculate 'total_estimated_cost'.\n"
    "4. NO HALLUCINATION / FALLBACK HANDLING:\n"
    "   - If your google_search queries return no results, or if the user's budget and constraints are "
    "     completely unrealistic (e.g., $10 flights, flying halfway around the world in 1 hour, etc.), "
    "     you MUST NOT hallucinate fake prices or flights.\n"
    "   - Instead, you must trigger the fallback path: set `fallback_requested` to `True` in your structured "
    "     response, specify `fallback_message` explaining exactly why (e.g., 'We couldn't find any flights "
    "     matching your $50 budget from New York to Tokyo. Please increase your budget or choose a closer destination.'), "
    "     and leave the flights, accommodation, and daily activities empty or minimal.\n"
    "5. STRICT STRUCTURED OUTPUT: All outputs must strictly conform to the ItineraryProposal JSON structure."
)

# ----------------------------------------------------------------------
# 3. Configure safety settings
# ----------------------------------------------------------------------

safety_settings = [
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
    SafetySetting(
        category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    ),
]

# ----------------------------------------------------------------------
# 4. Initialize the Google ADK Agent
# ----------------------------------------------------------------------

# We configure GenerateContentConfig for general options like safety settings
content_config = types.GenerateContentConfig(
    safety_settings=safety_settings,
    temperature=0.2, # Low temperature for reliable structured JSON and minimal drift
)

async def init_itinerary_state(callback_context: CallbackContext) -> None:
    if "feedback_instruction" not in callback_context.state:
        callback_context.state["feedback_instruction"] = ""
    # Extract user_query from the first user event if not set
    if "user_query" not in callback_context.state:
        for event in callback_context.session.events:
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        callback_context.state["user_query"] = part.text
                        break
            if "user_query" in callback_context.state:
                break

itinerary_agent = Agent(
    name="itinerary_agent",
    model="gemini-flash-latest", # Efficient flash model for planning
    instruction=SYSTEM_INSTRUCTION,
    tools=[google_search],
    output_schema=ItineraryProposal,
    output_key="itinerary_proposal",
    before_agent_callback=init_itinerary_state,
    generate_content_config=content_config,
)

# Alias for backwards compatibility
travel_agent = itinerary_agent
