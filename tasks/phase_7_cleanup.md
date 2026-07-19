# Phase 7: Delete Non-ADK Related Code

**Goal:** Remove redundant, non-ADK legacy python files from the backend root folder that have been successfully migrated to the ADK structure under `backend/app/`.

**Tasks:**
1. [x] Delete legacy non-ADK agent logic:
   - [x] Delete `backend/agent.py`
   - [x] Delete `backend/evaluator_agent.py`
   - [x] Delete `backend/itinerary_agent.py`
   - [x] Delete `backend/orchestrator.py`
2. [x] Delete legacy non-ADK API & Run scripts:
   - [x] Delete `backend/main.py`
   - [x] Delete `backend/run_agent_cli.py`
   - [x] Delete `backend/security.py`
   - [x] Delete `backend/database.py`
3. [x] Delete legacy non-ADK tests:
   - [x] Delete `backend/test_agent.py`
   - [x] Delete `backend/test_api.py`
   - [x] Delete `backend/test_orchestrator.py`
4. [x] Validate ADK structure integrity:
   - [x] Ensure that `backend/app/` operates correctly without relying on parent-level files.
   - [x] Verify that imports inside `backend/app/` do not reference parent-level files.
   - [x] Run local development server using the ADK app: `uvicorn app.fast_api_app:app --reload` (from `backend/` directory) to verify routing and functionality.

**Definition of Done:** A clean workspace containing only ADK-compliant backend application files under `backend/app/` with no redundant root-level Python scripts remaining in `backend/`.
