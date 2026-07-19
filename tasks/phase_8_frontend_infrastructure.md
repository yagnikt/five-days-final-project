# Phase 8: Frontend Infrastructure & Cloud Run Deployment

This phase outlines the steps to containerize the Vite frontend application, deploy it to Google Cloud Run, and use Terraform to define the infrastructure and dynamically link the frontend to the backend API.

## Objective
Package the frontend web app into a Docker container utilizing Nginx as a reverse proxy, and deploy it to Google Cloud Run utilizing Terraform.

## Implementation Steps

### 1. Frontend Containerization
To serve the static Vite application dynamically and handle API requests to the backend (avoiding CORS issues and build-time env var baking), use an Nginx reverse proxy pattern.

- **`frontend/Dockerfile`**: Create a multi-stage Dockerfile.
  - **Build Stage:** Installs Node.js dependencies and runs `npm run build` to generate static files.
  - **Serve Stage:** Uses `nginx:alpine`, copies the static files from the build stage, and sets up a custom entrypoint.
- **`frontend/nginx.conf.template`**: Create a template Nginx configuration file that serves the static files on the root (`/`) and proxies all `/api/` requests to a variable backend URL (`$BACKEND_URL`).
- **`frontend/start.sh`**: Create an entrypoint script that runs `envsubst` to replace the `$BACKEND_URL` placeholder in `nginx.conf.template` with the actual environment variable provided by Cloud Run, then starts Nginx. Make sure it's executable (`chmod +x`).

### 2. Terraform Infrastructure Updates
Update the Infrastructure as Code (IaC) to include the new Cloud Run service for the frontend.

- **`infra/variables.tf`**:
  - Add a new variable `frontend_service_name` (default: `"travel-itinerary-planner-frontend"`).
- **`infra/main.tf`**:
  - Add `google_cloud_run_v2_service` for the frontend.
  - Configure it to use the `frontend_service_name`.
  - Inject the `BACKEND_URL` environment variable dynamically using `google_cloud_run_v2_service.backend.uri`.
  - Add `google_cloud_run_v2_service_iam_member` to grant `allUsers` the `roles/run.invoker` role to make the frontend public.
- **`infra/outputs.tf`**:
  - Add a new output `frontend_url` to return the deployed frontend's public Cloud Run URI.

### 3. Verification & Deployment
- Run `terraform plan` to ensure the new resources are evaluated properly.
- Update CI/CD pipelines or manually build and push the new frontend container alongside the backend.
- Apply Terraform changes and verify the deployed frontend can successfully communicate with the backend API via the Nginx proxy.
