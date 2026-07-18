# Backend Architecture & Rules

This is the backend service for the **AI-Driven Travel Itinerary Planner**.

## Tech Stack
- **Framework:** FastAPI
- **AI Orchestration:** Google Agent Development Kit (ADK) & `google-genai` SDK
- **Deployment & CLI Orchestration**: **`agents-cli`** (using `agents-cli-manifest.yaml`)
- **Database / State:** Firebase Firestore (via `firebase-admin` SDK)
- **Memory & Session Persistence**: **Google Agent Memory Bank** (via `aiplatform.memories` and session services)
- **Security:** Vertex AI Safety Settings & backend input sanitization

## Guidelines & Best Practices
1. **Separation of Concerns:** Keep routing (FastAPI endpoints), agent coordination logic, database service layer, and safety validation strictly separate.
2. **State & Conversation Flow:** Ensure all requests from clients are immediately written to Firestore with a status of `pending` for HITL tracking. Short-term active conversation context and long-term user preferences should be managed directly through the Google Agent Memory Bank APIs, bypassing manual database tables.
3. **Safety Settings:** Always define explicit `google-genai` Vertex AI safety settings (e.g. block thresholds for hate speech, harassment, etc.) to prevent jailbreaking/injection.
4. **Manifest and Deployment Integrity**: Always maintain the `agents-cli-manifest.yaml` with the correct deployment target (`agent_runtime`) and app settings. All backend cloud deployments must be executed via `agents-cli deploy`.
5. **Pre-commit Evaluation Run**: Run offline evaluation regression testing locally before committing using `agents-cli eval run` to ensure prompt additions or edits maintain a baseline quality threshold of 0.8.
6. **Environment Variables:** Never hardcode secrets. Always read from `.env` or system environment variables, matching the schema defined in `.env.example`.
