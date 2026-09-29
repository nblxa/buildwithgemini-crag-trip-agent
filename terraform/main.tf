terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

data "google_project" "project" {
  project_id = var.project_id
}

# ------------------------------------------------------------------------------
# 1. API Services Enablement
# ------------------------------------------------------------------------------
locals {
  services = [
    "aiplatform.googleapis.com",
    "run.googleapis.com",
    "firestore.googleapis.com",
    "storage.googleapis.com",
    "cloudbuild.googleapis.com",
    "artifactregistry.googleapis.com"
  ]
}

resource "google_project_service" "enabled_apis" {
  for_each           = toset(locals.services)
  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

# ------------------------------------------------------------------------------
# 2. Firestore Database (Native mode)
# ------------------------------------------------------------------------------
resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = "(default)"
  location_id = var.region
  type        = "FIRESTORE_NATIVE"

  depends_on = [google_project_service.enabled_apis["firestore.googleapis.com"]]
}

# ------------------------------------------------------------------------------
# 3. Google Cloud Storage Bucket (Public Media Assets)
# ------------------------------------------------------------------------------
resource "google_storage_bucket" "media_bucket" {
  name                        = var.storage_bucket_name
  location                    = var.region
  uniform_bucket_level_access = true
  force_destroy               = false

  website {
    main_page_suffix = "index.html"
    not_found_page   = "404.html"
  }

  cors {
    origin          = ["*"]
    method          = ["GET", "HEAD", "OPTIONS"]
    response_header = ["*"]
    max_age_seconds = 3600
  }

  depends_on = [google_project_service.enabled_apis["storage.googleapis.com"]]
}

# Grant public read access to all objects
resource "google_storage_bucket_iam_member" "public_read" {
  bucket = google_storage_bucket.media_bucket.name
  role   = "roles/storage.objectViewer"
  member = "allUsers"
}

# ------------------------------------------------------------------------------
# 4. IAM Permissions for Vertex AI Agent Service Agent
# ------------------------------------------------------------------------------
# The Vertex AI reasoning engine service agent requires Datastore User and Storage Object Admin
locals {
  agent_engine_sa = "service-${data.google_project.project.number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "agent_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${locals.agent_engine_sa}"
}

resource "google_storage_bucket_iam_member" "agent_storage_admin" {
  bucket = google_storage_bucket.media_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${locals.agent_engine_sa}"
}

# ------------------------------------------------------------------------------
# 5. Cloud Run Service Identity & Permissions
# ------------------------------------------------------------------------------
# Cloud Run compute identity needs roles/aiplatform.user to invoke Agent Engine
resource "google_project_iam_member" "cloud_run_aiplatform_user" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${data.google_project.project.number}-compute@developer.gserviceaccount.com"
}

# ------------------------------------------------------------------------------
# 6. Cloud Run Frontend Service
# ------------------------------------------------------------------------------
resource "google_cloud_run_v2_service" "frontend" {
  name     = "cragtrip-frontend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = "${data.google_project.project.number}-compute@developer.gserviceaccount.com"

    containers {
      image = "us-east1-docker.pkg.dev/${var.project_id}/cloud-run-source-deploy/cragtrip-frontend:latest"

      resources {
        limits = {
          cpu    = "1000m"
          memory = "512Mi"
        }
      }

      env {
        name  = "AGENT_ENGINE_RESOURCE_NAME"
        value = "projects/${data.google_project.project.number}/locations/${var.region}/reasoningEngines/${var.agent_engine_id}"
      }
      env {
        name  = "AGENT_DIRECTORY"
        value = var.agent_directory
      }
    }
  }

  depends_on = [
    google_project_service.enabled_apis["run.googleapis.com"],
    google_project_iam_member.cloud_run_aiplatform_user
  ]
}

# Allow unauthenticated invocations for public web access
resource "google_cloud_run_v2_service_iam_member" "frontend_public" {
  project  = var.project_id
  location = google_cloud_run_v2_service.frontend.location
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
