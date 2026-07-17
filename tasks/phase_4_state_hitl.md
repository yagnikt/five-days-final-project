# Phase 4: State Management & HITL Gateway

**Goal:** Expose the agent workflow via FastAPI and manage state using Firestore for the Human-in-the-Loop gateway.

**Tasks:**
1. Set up Firestore collections (`itinerary_requests`, `pending_approvals`, `approved_itineraries`).
2. Build FastAPI endpoints in `backend/main.py`:
   - `POST /api/request`: Accept new travel requests and trigger the background agent workflow.
   - `GET /api/pending`: Fetch pending itineraries for the Admin Dashboard.
   - `POST /api/approve/{id}`: Approve an itinerary.
   - `POST /api/reject/{id}`: Reject an itinerary.
3. Integrate the agent evaluation loop (from Phase 3) into the backend so successful itineraries are saved to Firestore as `pending`.

**Definition of Done:** A fully functional FastAPI backend interacting with Firestore and the agent logic.
