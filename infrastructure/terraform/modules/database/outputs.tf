# ============================================
# Database Module - Outputs
# ============================================

output "instance_name" {
  description = "The name of the Cloud SQL instance"
  value       = google_sql_database_instance.main.name
}

output "connection_name" {
  description = "The connection name of the Cloud SQL instance"
  value       = google_sql_database_instance.main.connection_name
}

output "private_ip_address" {
  description = "The private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.private_ip_address
}

output "public_ip_address" {
  description = "The public IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.main.public_ip_address
}

output "connection_string" {
  description = "Database connection string"
  value       = "postgresql://${var.database_user}:${var.database_password}@${google_sql_database_instance.main.public_ip_address}:5432/${var.database_name}"
  sensitive   = true
}

output "database_name" {
  description = "The name of the database"
  value       = google_sql_database.database.name
}
