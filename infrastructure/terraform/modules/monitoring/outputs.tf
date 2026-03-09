# ============================================
# Monitoring Module - Outputs
# ============================================

output "uptime_check_id" {
  description = "ID of the uptime check"
  value       = google_monitoring_uptime_check_config.auth_api_uptime.uptime_check_id
}

output "dashboard_url" {
  description = "URL of the monitoring dashboard"
  value       = "https://console.cloud.google.com/monitoring/dashboards/custom/${google_monitoring_dashboard.auth_api.id}?project=${var.project_id}"
}

output "logs_dataset_id" {
  description = "BigQuery dataset ID for logs"
  value       = google_bigquery_dataset.logs.dataset_id
}

output "notification_channel_name" {
  description = "Name of the notification channel"
  value       = var.alert_email != null ? google_monitoring_notification_channel.email[0].name : null
}
