variable "project_id" {
  description = "The Google Cloud Project ID"
  type        = string
  default     = "qwiklabs-gcp-03-689eef206658"
}

variable "region" {
  description = "Primary GCP region for compute and services"
  type        = string
  default     = "us-east1"
}

variable "storage_bucket_name" {
  description = "The public GCS bucket used for storing compiled itineraries and generated visuals"
  type        = string
  default     = "cragtrip-media-xxl67u"
}

variable "agent_engine_id" {
  description = "Reasoning Engine / Memory Bank ID deployed on Vertex AI"
  type        = string
  default     = "1870064769684209664"
}

variable "agent_directory" {
  description = "The agent module directory name within the deployment"
  type        = string
  default     = "app"
}
