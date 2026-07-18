from google.adk.apps import App
from .itinerary_agent import travel_agent

root_agent = travel_agent

app = App(
    name="app",
    root_agent=root_agent,
)

__all__ = ["app", "root_agent"]
