# ============================================
# Database Module - Cloud SQL PostgreSQL
# ============================================

resource "random_id" "db_name_suffix" {
  byte_length = 4
}

# Cloud SQL Instance
resource "google_sql_database_instance" "main" {
  name             = "${var.database_name}-${random_id.db_name_suffix.hex}"
  database_version = "POSTGRES_15"
  region          = var.region
  
  deletion_protection = var.environment == "prod" ? true : false

  settings {
    tier                        = var.database_tier
    disk_size                   = var.disk_size_gb
    disk_type                   = "PD_SSD"
    disk_autoresize            = true
    disk_autoresize_limit      = var.max_disk_size_gb
    availability_type          = var.environment == "prod" ? "REGIONAL" : "ZONAL"
    
    backup_configuration {
      enabled                        = true
      start_time                     = "03:00"
      location                       = var.region
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      backup_retention_settings {
        retained_backups = 7
        retention_unit   = "COUNT"
      }
    }

    maintenance_window {
      day  = 7  # Sunday
      hour = 3
    }

    database_flags {
      name  = "log_statement"
      value = "all"
    }

    database_flags {
      name  = "log_min_duration_statement"
      value = "1000"  # Log queries taking longer than 1 second
    }

    ip_configuration {
      ipv4_enabled    = true
      authorized_networks {
        value = "0.0.0.0/0"
        name  = "all"
      }
    }

    user_labels = var.labels
  }

  lifecycle {
    prevent_destroy = true
  }
}

# Database
resource "google_sql_database" "database" {
  name     = var.database_name
  instance = google_sql_database_instance.main.name
}

# Database User
resource "google_sql_user" "user" {
  name     = var.database_user
  instance = google_sql_database_instance.main.name
  password = var.database_password
}
