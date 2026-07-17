variable "project_id" {
  description = "The Google Cloud Platform (GCP) Project ID"
  type        = string
}

variable "region" {
  description = "The GCP region to deploy resources in"
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "The name of the Cloud Run service"
  type        = string
  default     = "travel-itinerary-planner"
}

variable "firestore_database_name" {
  description = "The name of the Firestore Database. Default is (default)"
  type        = string
  default     = "(default)"
}
