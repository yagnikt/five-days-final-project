terraform {
  required_version = ">= 1.3.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable GCP Services
resource "google_project_service" "apis" {
  for_each = toset([
    "run.googleapis.com",
    "firestore.googleapis.com",
    "aiplatform.googleapis.com",
    "iam.googleapis.com"
  ])
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# Create Firestore Database (if not using pre-created '(default)')
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = var.firestore_database_name
  location_id = var.region
  type        = "FIRESTORE_STANDARD"

  # Wait for API activation before creating
  depends_on = [google_project_service.apis]
}

# Service Account for Cloud Run
resource "google_service_account" "cloud_run_sa" {
  project      = var.project_id
  account_id   = "travel-planner-runner"
  display_name = "Service Account for Travel Planner Cloud Run"
  depends_on   = [google_project_service.apis]
}

# IAM Role Bindings for Service Account
resource "google_project_iam_member" "firestore_user" {
  project    = var.project_id
  role       = "roles/datastore.user"
  member     = "serviceAccount:${google_service_account.cloud_run_sa.email}"
  depends_on = [google_project_service.apis]
}

resource "google_project_iam_member" "vertex_user" {
  project    = var.project_id
  role       = "roles/aiplatform.user"
  member     = "serviceAccount:${google_service_account.cloud_run_sa.email}"
  depends_on = [google_project_service.apis]
}

# Cloud Run Service for FastAPI Backend
resource "google_cloud_run_v2_service" "backend" {
  name     = var.service_name
  location = var.region
  project  = var.project_id

  template {
    service_account = google_service_account.cloud_run_sa.email
    containers {
      image = "gcr.io/${var.project_id}/${var.service_name}:latest" # Placeholder image to build during CI/CD

      env {
        name  = "GCP_PROJECT"
        value = var.project_id
      }
      env {
        name  = "GCP_REGION"
        value = var.region
      }
      env {
        name  = "FIRESTORE_DATABASE"
        value = var.firestore_database_name
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_service.apis,
    google_firestore_database.database
  ]
}

# Allow public access to Cloud Run (Unauthenticated users)
resource "google_cloud_run_v2_service_iam_member" "public_access" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
