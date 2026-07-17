# Project Goal

The goal of this project is to build an **AI-Driven Travel Itinerary Planner**.

This agent solves the manual and time-intensive process of finding optimal weekend trips. Instead of constantly checking flight timings, layovers, and dates, the user can configure their preferences via natural language. The agent leverages Google Search for research, employs an LLM-as-a-judge to evaluate responses, and ensures all plans receive final authorization through a human-in-the-loop (HITL) review process before presentation.

## Key Features & Architecture
- **Primary Generative Agent**: Built with Gemini 3.1 Pro via the ADK, utilizing the Google Search tool for real-time data grounding.
- **LLM-as-a-Judge**: Built with Gemini 3.5 Flash to score the generated itineraries based on feasibility, quality, and user constraints, with loop control (`max_retries`) to manage costs.
- **Backend API**: A Python backend (using FastAPI) to orchestrate the agents and manage state.
- **State Management & Database**: Google Cloud Firestore to store itinerary requests, pending approvals, and approved itineraries.
- **Human-in-the-Loop (HITL) Dashboard**: A built-in web dashboard where administrators must approve itineraries before they are visible to the client.
- **Security**: Vertex AI Safety Settings and backend input sanitization to protect against prompt injection.
- **Infrastructure as Code (IaC)**: Terraform to deploy the API to Google Cloud Run and provision Firestore.
- **Frontend UI**: Built with Vite and Vanilla HTML/JS/CSS, featuring async polling/WebSockets to gracefully handle latency during agent evaluation.

---

# Current Status

**Status: Planning Complete. Ready to execute Phase 1.**

The implementation plan has been established and broken down into phases. Task markdown files have been generated in the `/tasks` directory.

## Implementation Phases

- [x] **Phase 1: Environment Setup & Infrastructure**: Terraform init, base project structure (`backend/` and `frontend/`), documentation, and `.env.example` configurations.
- [ ] **Phase 2: Core Agent Logic (Primary Agent)**: Implement Gemini Pro agent, integrate Google Search tool, and define edge case fallbacks for tool failures.
- [ ] **Phase 3: Evaluation Layer (LLM-as-a-Judge) & Security**: Implement Gemini Flash judge, evaluation loop logic, and input security guardrails.
- [ ] **Phase 4: State Management & HITL Gateway**: Build FastAPI endpoints and integrate Firestore state management for the evaluation loop.
- [ ] **Phase 5: Frontend UI Development**: Build the user-facing Client View and Admin Dashboard, implementing latency UX handling.
