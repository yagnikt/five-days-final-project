# Phase 1: Environment Setup & Infrastructure

**Goal:** Initialize the project repository, set up Terraform for GCP infrastructure, and establish the base backend/frontend project structures.

**Tasks:**
1. Initialize the project structure (separate `backend` and `frontend` directories).
2. Create `GEMINI.md` files in the root, `backend`, and `frontend` directories to document the project architecture, goals, and rules.
3. **Infrastructure as Code:** Initialize a Terraform configuration in an `infra/` directory to manage stateful GCP resources (Firestore database, IAM roles). Create a `terraform.tfvars.example` file.
4. Set up a Python virtual environment in `backend/` and install necessary dependencies (ADK, FastAPI, Firebase Admin SDK). Create a `.env.example` file in the backend.
5. Create initial `agents-cli-manifest.yaml` configuration in the `backend/` directory for Orchestration and Deployment.
6. Create an initial evaluation set `.evalset.json` under `backend/tests/evalsets/` to define baseline travel test cases.
7. Initialize the Vite Vanilla JS project in `frontend/`. Create a `.env.example` file in the frontend if needed.
8. Configure local GCP credentials.

**Definition of Done:** A base repository ready for development, with Terraform initialized, the `agents-cli` manifest configured, and evaluation datasets set up.
