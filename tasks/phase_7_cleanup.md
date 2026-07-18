# Phase 7: Delete Non-ADK Related Code

**Goal:** Remove redundant, non-ADK legacy python files from the backend root folder that have been successfully migrated to the ADK structure under `backend/app/`.

**Tasks:**
1. [ ] Delete legacy non-ADK agent logic:
   - [ ] Delete `backend/agent.py`
   - [ ] Delete `backend/evaluator_agent.py`
   - [ ] Delete `backend/itinerary_agent.py`
   - [ ] Delete `backend/orchestrator.py`
2. [ ] Delete legacy non-ADK API & Run scripts:
   - [ ] Delete `backend/main.py`
   - [ ] Delete `backend/run_agent_cli.py`
   - [ ] Delete `backend/security.py`
   - [ ] Delete `backend/database.py`
3. [ ] Delete legacy non-ADK tests:
   - [ ] Delete `backend/test_agent.py`
   - [ ] Delete `backend/test_api.py`
   - [ ] Delete `backend/test_orchestrator.py`
4. [ ] Validate ADK structure integrity:
   - [ ] Ensure that `backend/app/` operates correctly without relying on parent-level files.
   - [ ] Verify that imports inside `backend/app/` do not reference parent-level files.
   - [ ] Run local development server using the ADK app: `uvicorn app.fast_api_app:app --reload` (from `backend/` directory) to verify routing and functionality.

**Definition of Done:** A clean workspace containing only ADK-compliant backend application files under `backend/app/` with no redundant root-level Python scripts remaining in `backend/`.
