# Phase 5: Frontend UI Development

**Goal:** Build the user-facing Client View and the Admin Dashboard.

**Tasks:**
1. **Client View:** Build the UI to input travel preferences, load long-term settings from the Agent Memory Bank, and display approved itineraries.
2. **Admin Dashboard:** Build the HITL interface to fetch, display, review LLM-as-a-judge scores, and approve/reject pending itineraries.
3. **UX & Latency Handling:** Implement async polling pointing to `/api/status/{id}` to display beautiful progress bar states (e.g., `"Initializing Agent..."`, `"Querying Google Search..."`, `"Running Evaluator Check..."`, `"Awaiting Admin Review..."`).
4. Apply premium styling (dark-mode theme, glassmorphism, dynamic transitions) using Vanilla CSS.
5. **Cloud Deployment**: Package and deploy the final containerized FastAPI backend to Google Cloud Agent Runtime using `agents-cli deploy`.

**Definition of Done:** A complete, interactive web interface connected to a live FastAPI backend fully deployed to Google Cloud via `agents-cli`.
