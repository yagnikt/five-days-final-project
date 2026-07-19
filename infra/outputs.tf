output "cloud_run_url" {
  description = "The public URL of the Cloud Run backend service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "firestore_database_id" {
  description = "The database ID of the created Firestore instance"
  value       = google_firestore_database.database.id
}

output "service_account_email" {
  description = "The email of the Cloud Run Service Account"
  value       = google_service_account.cloud_run_sa.email
}

output "frontend_url" {
  description = "The public URL of the Cloud Run frontend service"
  value       = google_cloud_run_v2_service.frontend.uri
}

