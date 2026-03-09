# ============================================
# Cloud Run Module
# ============================================

# Service Account for Cloud Run
resource "google_service_account" "cloud_run" {
  account_id   = "${var.service_name}-sa"
  display_name = "Service Account for ${var.service_name}"
  description  = "Service account used by the ${var.service_name} Cloud Run service"
}

# Cloud Run Service
resource "google_cloud_run_v2_service" "main" {
  name     = var.service_name
  location = var.region
  
  deletion_protection = var.environment == "prod" ? true : false

  template {
    service_account = google_service_account.cloud_run.email
    
    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.image_url
      
      ports {
        container_port = 8000
      }

      resources {
        limits = {
          cpu    = var.cpu_limit
          memory = var.memory_limit
        }
        cpu_idle = var.cpu_idle
      }

      # Environment variables
      dynamic "env" {
        for_each = local.all_environment_variables
        content {
          name  = env.key
          value = env.value
        }
      }

      # Sensitive environment variables from Secret Manager
      dynamic "env" {
        for_each = var.secret_environment_variables
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value.secret_name
              version = env.value.version
            }
          }
        }
      }

      startup_probe {
        http_get {
          path = "/health/db"
          port = 8000
        }
        initial_delay_seconds = 30
        timeout_seconds      = 10
        period_seconds       = 30
        failure_threshold    = 3
      }

      liveness_probe {
        http_get {
          path = "/health/db"
          port = 8000
        }
        initial_delay_seconds = 60
        timeout_seconds      = 10
        period_seconds       = 60
        failure_threshold    = 3
      }
    }
  }

  traffic {
    percent = 100
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
  }

  lifecycle {
    ignore_changes = [
      template[0].containers[0].image
    ]
  }

  depends_on = [
    google_service_account.cloud_run
  ]
}

# IAM policy for Cloud Run service
resource "google_cloud_run_service_iam_member" "public_access" {
  count = var.allow_public_access ? 1 : 0

  location = google_cloud_run_v2_service.main.location
  service  = google_cloud_run_v2_service.main.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Custom domain mapping (optional)
resource "google_cloud_run_domain_mapping" "main" {
  count = var.custom_domain != null ? 1 : 0

  location = google_cloud_run_v2_service.main.location
  name     = var.custom_domain

  spec {
    route_name = google_cloud_run_v2_service.main.name
  }

  metadata {
    namespace = var.project_id
  }
}
