# ============================================
# Cloud Run Module - Outputs
# ============================================

output "service_name" {
  description = "The name of the Cloud Run service"
  value       = google_cloud_run_v2_service.main.name
}

output "service_url" {
  description = "The URL of the Cloud Run service"
  value       = google_cloud_run_v2_service.main.uri
}

output "service_account_email" {
  description = "Email of the service account used by Cloud Run"
  value       = google_service_account.cloud_run.email
}

output "service_id" {
  description = "The unique identifier of the Cloud Run service"
  value       = google_cloud_run_v2_service.main.id
}

output "latest_created_revision" {
  description = "The latest created revision name"
  value       = google_cloud_run_v2_service.main.latest_created_revision
}

output "custom_domain_url" {
  description = "The custom domain URL (if configured)"
  value       = var.custom_domain != null ? "https://${var.custom_domain}" : null
}
