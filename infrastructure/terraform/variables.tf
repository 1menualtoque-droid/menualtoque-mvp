# ============================================
# Auth API Infrastructure - Variables
# ============================================

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "image_url" {
  description = "Container image URL for Cloud Run deployment"
  type        = string
}

variable "database_user" {
  description = "Database user name"
  type        = string
  default     = "postgres"
}

variable "database_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "environment_variables" {
  description = "Environment variables for the application"
  type = map(string)
  default = {}
  sensitive = true
}

variable "allowed_origins" {
  description = "CORS allowed origins"
  type        = list(string)
  default     = []
}

variable "jwt_secret" {
  description = "JWT secret key"
  type        = string
  sensitive   = true
}

variable "google_client_id" {
  description = "Google OAuth client ID"
  type        = string
  default     = ""
}

variable "resend_api_key" {
  description = "Resend API key for email sending"
  type        = string
  sensitive   = true
  default     = ""
}

variable "email_from" {
  description = "Email from address"
  type        = string
  default     = "noreply@example.com"
}
