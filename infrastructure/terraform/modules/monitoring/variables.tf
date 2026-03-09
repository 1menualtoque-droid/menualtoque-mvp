# ============================================
# Monitoring Module - Variables
# ============================================

variable "project_id" {
  description = "The GCP project ID"
  type        = string
}

variable "region" {
  description = "The GCP region"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "cloud_run_service_name" {
  description = "Name of the Cloud Run service to monitor"
  type        = string
}

variable "cloud_run_service_url" {
  description = "URL of the Cloud Run service"
  type        = string
}

variable "database_instance_name" {
  description = "Name of the database instance to monitor"
  type        = string
}

variable "alert_email" {
  description = "Email address for alerts (optional)"
  type        = string
  default     = null
}

variable "labels" {
  description = "Labels to apply to resources"
  type        = map(string)
  default     = {}
}
