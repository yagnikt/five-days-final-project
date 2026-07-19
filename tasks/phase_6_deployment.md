# Phase 6: Cloud Deployment via Vertex AI Agent Engine (The ADK Refactor)

To fully leverage the Google Agents CLI (`agents-cli`) and deploy to Vertex AI Agent Runtime natively, we must migrate the existing monolithic FastAPI orchestration (`main.py`) into the standard ADK directory structure. 

## Phase 6.1: Scaffold Enhancement & File Restructuring
- [x] Move into the `backend/` directory.
- [x] Run `agents-cli scaffold enhance . --deployment-target agent_runtime` to generate the ADK boilerplate (`app/fast_api_app.py`, `app/app_utils/`, `Dockerfile`, and `deployment/terraform/`).
- [x] Create the `backend/app/` directory if it wasn't fully populated.
- [x] Move the custom agents (`itinerary_agent.py`, `evaluator_agent.py`) and tools into the `backend/app/` directory.
- [x] Ensure `backend/app/__init__.py` properly defines the `App(name="app", root_agent=...)` instance.

## Phase 6.2: Refactoring Core Agents to ADK Primitives
- [x] Refactor `itinerary_agent.py` to define an `Agent(name="itinerary_agent", model="gemini-flash-latest", ...)`.
- [x] Migrate any tools (like Google Search) to use ADK's `FunctionTool` or built-in tools.
- [x] Refactor `evaluator_agent.py` to define an `Agent(name="evaluator_agent", ...)`.
- [x] Configure structured output using Pydantic via the `output_schema` parameter to enforce the evaluation schema (pass/fail grading).

## Phase 6.3: Orchestration Migration (ADK Workflow)
- [x] In `backend/app/agent.py`, create a `LoopAgent` or `SequentialAgent` to manage the interaction between the `itinerary_agent` and the `evaluator_agent`.
- [x] If using a `LoopAgent` for the generate-evaluate-refine loop, implement an `EscalationChecker` (a custom `BaseAgent` or callback) to break the loop when the evaluator returns a "pass" grade.

## Phase 6.4: Migrating HITL & Custom REST APIs
- [x] Extract `/api/request`, `/api/status`, `/api/pending`, `/api/approve`, and `/api/reject` from the old `main.py`.
- [x] Open the ADK-generated `app/fast_api_app.py`.
- [x] Mount these custom routes onto the core FastAPI app during its initialization phase, ensuring they still interact with the `database.py` (Firestore) logic.
- [x] Re-wire the background orchestration trigger to use the new ADK `Runner` instead of the old custom orchestrator.

## Phase 6.5: Infrastructure, Terraform, & Configuration Updates
- [x] Modify the generated `backend/deployment/terraform/single-project/iam.tf` (completed dynamically via updating default roles in `variables.tf`).
- [x] Add IAM bindings granting `roles/datastore.user` (or `roles/firebase.admin`) to the agent's runtime service account (`app_sa`) so it can read/write to Firestore.
- [x] Ensure `agents-cli deploy` is passed the correct environment variables (e.g., `GCP_PROJECT`, `FIREBASE_CREDENTIALS` if not using default auth).
- [x] If utilizing Secret Manager, grant `roles/secretmanager.secretAccessor` to the `app_sa` in Terraform (not utilized in current design, marked complete).
- [x] Ensure `backend/agents-cli-manifest.yaml` reflects the new layout (`agent_directory: app`).

## Phase 6.6: Validation, Testing, and Deployment
- [x] Start the server using `uvicorn app.fast_api_app:app --reload` or test via `agents-cli run`.
- [x] Verify the frontend UI still successfully communicates with the HITL endpoints and Firestore.
- [x] Run `agents-cli eval generate` and `agents-cli eval grade` against the existing `.evalset.json` to ensure agent quality hasn't regressed during the refactor.
- [x] Execute `agents-cli deploy` from the `backend/` directory to push the container to Vertex AI Agent Runtime.
