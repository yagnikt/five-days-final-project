# Backend Architecture & Rules

This is the backend service for the **AI-Driven Travel Itinerary Planner**.

## Tech Stack
- **Framework:** FastAPI
- **AI Orchestration:** Google Agent Development Kit (ADK) & `google-genai` SDK
- **Database / State:** Firebase Firestore (via `firebase-admin` SDK)
- **Security:** Vertex AI Safety Settings & backend input sanitization

## Guidelines & Best Practices
1. **Separation of Concerns:** Keep routing (FastAPI endpoints), agent coordination logic, database service layer, and safety validation strictly separate.
2. **State & Conversation Flow:** Ensure all requests from clients are immediately written to Firestore with a status of `pending`. Background worker/polling endpoints must read and update this state.
3. **Safety Settings:** Always define explicit `google-genai` Vertex AI safety settings (e.g. block thresholds for hate speech, harassment, etc.) to prevent jailbreaking/injection.
4. **Environment Variables:** Never hardcode secrets. Always read from `.env` or system environment variables, matching the schema defined in `.env.example`.
