# Phase 4: State Management & HITL Gateway

**Goal:** Expose the agent workflow via FastAPI and manage state using Firestore for the Human-in-the-Loop gateway.

**Tasks:**
1. Configure and integrate the **Google Agent Memory Bank** service within the backend ADK runner, allowing automatic extraction and persistence of short-term chat logs and long-term user profile preferences (bypassing Firestore session tables).
2. Set up Firestore collections (`itinerary_requests`, `pending_approvals`, `approved_itineraries`) strictly to manage stateful Admin HITL operations.
3. Build FastAPI endpoints in `backend/main.py`:
   - `POST /api/request`: Accept new travel requests, load historical user preferences from the Agent Memory Bank, and trigger the background agent execution thread.
   - `GET /api/status/{id}`: Fetch real-time status and logs of the active evaluation loop.
   - `GET /api/pending`: Fetch pending itineraries for the Admin Dashboard.
   - `POST /api/approve/{id}`: Approve an itinerary.
   - `POST /api/reject/{id}`: Reject an itinerary.
4. Integrate the agent evaluation loop (from Phase 3) into the backend orchestration so successfully scored itineraries are committed to Firestore as `pending`.

**Definition of Done:** A fully functional FastAPI backend interacting with the Google Agent Memory Bank for user preferences/sessions, and Firestore for HITL administrator workflows.
