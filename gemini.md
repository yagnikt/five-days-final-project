# Project Goal

The goal of this project is to build an **Automated Weekend Travel Assistant** for the "Ai in 5 Days" Assessment. 

This agent solves the manual and time-intensive process of finding optimal weekend trips. Instead of constantly checking flight timings, layovers, and dates, the user can configure their preferences (home airport, bucket-list destinations, maximum price, and ideal departure/return times) via natural language. The agent continuously monitors flight data and automatically alerts the user when a deal matching their exact criteria is found.

## Key Features
- **Natural Language Configuration**: Users can update their preferences by chatting with the agent.
- **Automated Monitoring**: The agent periodically checks flight data against user constraints.
- **Premium Web UI**: A sleek, modern dashboard built with HTML/JS/CSS that visualizes preferences and displays alerts in a beautiful feed.
- **ADK-Style Backend**: A Python backend (using Flask) that encapsulates the agent's state and skills.

---

# Current Status

**Status: Complete (Ready for Submission)**

The agent has been fully developed and broken down into logical git commits. 

## Completed Milestones
- [x] **Agent Concept Defined**: Settled on an automated flight deal monitor for weekend trips.
- [x] **Backend Infrastructure**: Built an ADK-style agent architecture in Python (`agent_backend/travel_agent.py`) that handles state and skills.
- [x] **Data Integration**: Created a mock flight API (`agent_backend/mock_flight_api.py`) to simulate flight searches and validate filtering logic.
- [x] **API Layer**: Developed a Flask REST API (`agent_backend/main.py`) to expose the agent to the frontend.
- [x] **Frontend UI**: Built a premium, responsive Web UI (`web_ui/`) featuring a chat interface and a live deals feed.
- [x] **Version Control**: Structured the implementation into clean, progressive git commits.

## Next Steps (User Action Required)
1. Commit the `gemini.md` file to the repository.
2. Push the codebase to a public GitHub repository.
3. Record a short video demonstrating the Web UI (chatting to update preferences, and clicking to check flights).
4. Submit the Git URL and Video URL to the assessment portal.
