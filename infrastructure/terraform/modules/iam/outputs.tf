# ============================================
# IAM Module - Outputs
# ============================================

output "cicd_service_account_email" {
  description = "Email of the CI/CD service account"
  value       = google_service_account.cicd.email
}

output "cicd_service_account_key" {
  description = "Base64 encoded key for the CI/CD service account"
  value       = google_service_account_key.cicd_key.private_key
  sensitive   = true
}

output "jwt_secret_name" {
  description = "Name of the JWT secret in Secret Manager"
  value       = google_secret_manager_secret.jwt_secret.secret_id
}

output "database_password_secret_name" {
  description = "Name of the database password secret in Secret Manager"
  value       = google_secret_manager_secret.database_password.secret_id
}

output "resend_api_key_secret_name" {
  description = "Name of the Resend API key secret in Secret Manager"
  value       = google_secret_manager_secret.resend_api_key.secret_id
}

output "google_client_id_secret_name" {
  description = "Name of the Google client ID secret in Secret Manager"
  value       = google_secret_manager_secret.google_client_id.secret_id
}
