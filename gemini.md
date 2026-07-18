# Project Goal

The goal of this project is to build an **AI-Driven Travel Itinerary Planner**.

This agent solves the manual and time-intensive process of finding optimal weekend trips. Instead of constantly checking flight timings, layovers, and dates, the user can configure their preferences via natural language. The agent leverages Google Search for research, employs an LLM-as-a-judge to evaluate responses, and ensures all plans receive final authorization through a human-in-the-loop (HITL) review process before presentation.

## Key Features & Architecture
- **Primary Generative Agent**: Built with Gemini 3.1 Pro via the ADK, utilizing the Google Search tool for real-time data grounding.
- **LLM-as-a-Judge & Evaluation**: Built with Gemini 3.5 Flash to score generated itineraries in real-time, plus **`agents-cli eval`** to run automated offline evaluations against test datasets (`.evalset.json`) to prevent quality regression.
- **Backend API**: A Python backend (using FastAPI) to orchestrate the agents, handle real-time evaluator loops, and interact with Google Cloud services.
- **State Management & Database**: Google Cloud Firestore to store operational records (itinerary requests, pending approvals, and approved itineraries).
- **Persistent Context & Memory**: **Google Agent Memory Bank** manages short-term chat histories and long-term user preferences natively, eliminating session bloat in the database.
- **Human-in-the-Loop (HITL) Dashboard**: A built-in web dashboard where administrators must approve itineraries before they are visible to the client.
- **Security**: Vertex AI Safety Settings and backend input sanitization to protect against prompt injection.
- **Infrastructure & Deployment**: Managed via **Terraform** for stateful cloud databases (Firestore) and IAM service accounts, combined with **`agents-cli`** (`agents-cli deploy`) to package and deploy the containerized agent backend directly to Google Cloud Agent Runtime.
- **Frontend UI**: Built with Vite and Vanilla HTML/JS/CSS, featuring async polling to gracefully handle latency during real-time agent evaluation.

---

# Current Status

**Status: Phase 2 Complete. Ready to execute Phase 3.**

The implementation plan has been established and broken down into phases. Task markdown files have been generated in the `/tasks` directory.

## Implementation Phases

- [x] **Phase 1: Environment Setup & Infrastructure**: Terraform init, base project structure (`backend/` and `frontend/`), `agents-cli-manifest.yaml` configuration, documentation, and `.env.example` configurations.
- [x] **Phase 2: Core Agent Logic (Primary Agent)**: Implement Gemini Pro agent, integrate Google Search tool, and define edge case fallbacks for tool failures.
- [ ] **Phase 3: Evaluation Layer (LLM-as-a-Judge) & Security**: Implement Gemini Flash judge, real-time evaluation loop logic, input security guardrails, and offline testing sets using `agents-cli eval`.
- [ ] **Phase 4: State Management & HITL Gateway**: Build FastAPI endpoints, integrate Firestore state management for the HITL approval flow, and configure the **Google Agent Memory Bank** session-state client.
- [ ] **Phase 5: Frontend UI Development & Cloud Deployment**: Build the user-facing Client View and Admin Dashboard with latency-aware polling status updates, and deploy the agent backend using `agents-cli deploy`.
