# ============================================
# IAM Module - Service Accounts and Permissions
# ============================================

# IAM roles for Cloud Run service account
resource "google_project_iam_member" "cloud_run_sql_client" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${var.cloud_run_service_account}"
}

resource "google_project_iam_member" "cloud_run_secret_accessor" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${var.cloud_run_service_account}"
}

resource "google_project_iam_member" "cloud_run_logging_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${var.cloud_run_service_account}"
}

resource "google_project_iam_member" "cloud_run_monitoring_writer" {
  project = var.project_id
  role    = "roles/monitoring.metricWriter"
  member  = "serviceAccount:${var.cloud_run_service_account}"
}

resource "google_project_iam_member" "cloud_run_trace_agent" {
  project = var.project_id
  role    = "roles/cloudtrace.agent"
  member  = "serviceAccount:${var.cloud_run_service_account}"
}

# CI/CD Service Account (for GitHub Actions)
resource "google_service_account" "cicd" {
  account_id   = "${var.environment}-cicd-sa"
  display_name = "CI/CD Service Account (${var.environment})"
  description  = "Service account used by CI/CD pipeline for ${var.environment} environment"
}

# CI/CD IAM roles
resource "google_project_iam_member" "cicd_cloud_run_developer" {
  project = var.project_id
  role    = "roles/run.developer"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

resource "google_project_iam_member" "cicd_storage_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

resource "google_project_iam_member" "cicd_cloudbuild_builds_builder" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.builder"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

resource "google_project_iam_member" "cicd_container_registry_admin" {
  project = var.project_id
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.cicd.email}"
}

# Service Account Key for CI/CD (to be used in GitHub Secrets)
resource "google_service_account_key" "cicd_key" {
  service_account_id = google_service_account.cicd.name
  public_key_type    = "TYPE_X509_PEM_FILE"
}

# Secret Manager secrets for application configuration
resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "${var.environment}-jwt-secret"

  replication {
    auto {}
  }

  labels = var.labels
}

resource "google_secret_manager_secret" "database_password" {
  secret_id = "${var.environment}-database-password"

  replication {
    auto {}
  }

  labels = var.labels
}

resource "google_secret_manager_secret" "resend_api_key" {
  secret_id = "${var.environment}-resend-api-key"

  replication {
    auto {}
  }

  labels = var.labels
}

resource "google_secret_manager_secret" "google_client_id" {
  secret_id = "${var.environment}-google-client-id"

  replication {
    auto {}
  }

  labels = var.labels
}
