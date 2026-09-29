output "cloud_run_url" {
  description = "The public service URL for the Cloud Run frontend"
  value       = google_cloud_run_v2_service.frontend.uri
}

output "storage_bucket_url" {
  description = "Public GCS bucket URL for media assets"
  value       = "https://storage.googleapis.com/${google_storage_bucket.media_bucket.name}"
}

output "firestore_database" {
  description = "The Firestore database name"
  value       = google_firestore_database.database.name
}

output "agent_engine_resource_name" {
  description = "Full resource name of the deployed Vertex AI Reasoning Engine"
  value       = "projects/${data.google_project.project.number}/locations/${var.region}/reasoningEngines/${var.agent_engine_id}"
}
