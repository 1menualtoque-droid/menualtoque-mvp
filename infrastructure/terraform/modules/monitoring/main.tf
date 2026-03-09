# ============================================
# Monitoring Module - Logging, Monitoring & Alerting
# ============================================

# Log sink for Cloud Run
resource "google_logging_project_sink" "cloud_run_sink" {
  name = "${var.environment}-cloud-run-logs"
  
  destination = "bigquery.googleapis.com/projects/${var.project_id}/datasets/${google_bigquery_dataset.logs.dataset_id}"
  
  filter = <<EOF
resource.type="cloud_run_revision"
resource.labels.service_name="${var.cloud_run_service_name}"
EOF

  unique_writer_identity = true
  
  bigquery_options {
    use_partitioned_tables = true
  }
}

# BigQuery dataset for logs
resource "google_bigquery_dataset" "logs" {
  dataset_id  = "${var.environment}_auth_api_logs"
  location    = var.region
  
  description = "Dataset for Auth API logs (${var.environment})"
  
  labels = var.labels
}

# IAM for log sink
resource "google_bigquery_dataset_iam_member" "log_sink_writer" {
  dataset_id = google_bigquery_dataset.logs.dataset_id
  role       = "roles/bigquery.dataEditor"
  member     = google_logging_project_sink.cloud_run_sink.writer_identity
}

# Custom metrics
resource "google_monitoring_metric_descriptor" "auth_api_requests" {
  description  = "Number of API requests"
  display_name = "Auth API Requests"
  type         = "custom.googleapis.com/auth_api/requests_total"
  metric_kind  = "CUMULATIVE"
  value_type   = "INT64"
  unit         = "1"

  labels {
    key         = "endpoint"
    value_type  = "STRING"
    description = "API endpoint"
  }
  
  labels {
    key         = "status_code"
    value_type  = "STRING"
    description = "HTTP status code"
  }

  labels {
    key         = "environment"
    value_type  = "STRING"
    description = "Environment"
  }
}

# Uptime check
resource "google_monitoring_uptime_check_config" "auth_api_uptime" {
  display_name = "${var.environment}-auth-api-uptime"
  timeout      = "10s"
  period       = "300s"

  http_check {
    path           = "/health/db"
    port           = "443"
    use_ssl        = true
    validate_ssl   = true
    request_method = "GET"
    
    accepted_response_status_codes {
      status_class = "STATUS_CLASS_2XX"
    }
  }

  monitored_resource {
    type = "uptime_url"
    labels = {
      project_id = var.project_id
      host       = replace(var.cloud_run_service_url, "https://", "")
    }
  }

  selected_regions = ["USA", "EUROPE"]
}

# Notification channel (email)
resource "google_monitoring_notification_channel" "email" {
  count = var.alert_email != null ? 1 : 0
  
  display_name = "${var.environment} Auth API Alerts"
  type         = "email"
  
  labels = {
    email_address = var.alert_email
  }
}

# Alert policy for high error rate
resource "google_monitoring_alert_policy" "high_error_rate" {
  display_name = "${var.environment} Auth API - High Error Rate"
  combiner     = "OR"
  
  conditions {
    display_name = "High 4xx/5xx error rate"
    
    condition_threshold {
      filter         = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.cloud_run_service_name}\""
      duration       = "300s"
      comparison     = "COMPARISON_GREATER_THAN"
      threshold_value = 0.1  # 10% error rate
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_MEAN"
        group_by_fields = ["resource.labels.service_name"]
      }
    }
  }
  
  dynamic "notification_channels" {
    for_each = var.alert_email != null ? [google_monitoring_notification_channel.email[0].name] : []
    content {
      name = notification_channels.value
    }
  }
  
  alert_strategy {
    auto_close = "1800s"  # 30 minutes
  }
}

# Alert policy for service down
resource "google_monitoring_alert_policy" "service_down" {
  display_name = "${var.environment} Auth API - Service Down"
  combiner     = "OR"
  
  conditions {
    display_name = "Uptime check failed"
    
    condition_threshold {
      filter         = "resource.type=\"uptime_url\""
      duration       = "300s"
      comparison     = "COMPARISON_LESS_THAN"
      threshold_value = 0.5  # Less than 50% success rate
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_FRACTION_TRUE"
        cross_series_reducer = "REDUCE_MEAN"
        group_by_fields = ["resource.label.host"]
      }
    }
  }
  
  dynamic "notification_channels" {
    for_each = var.alert_email != null ? [google_monitoring_notification_channel.email[0].name] : []
    content {
      name = notification_channels.value
    }
  }
  
  alert_strategy {
    auto_close = "1800s"  # 30 minutes
  }
}

# Alert policy for database connectivity
resource "google_monitoring_alert_policy" "database_down" {
  display_name = "${var.environment} Auth API - Database Connectivity"
  combiner     = "OR"
  
  conditions {
    display_name = "Database connection failures"
    
    condition_threshold {
      filter         = "resource.type=\"cloudsql_database\" AND resource.labels.database_id=\"${var.project_id}:${var.database_instance_name}\""
      duration       = "300s"
      comparison     = "COMPARISON_GREATER_THAN"
      threshold_value = 5  # More than 5 failed connections
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_RATE"
        cross_series_reducer = "REDUCE_SUM"
        group_by_fields = ["resource.labels.database_id"]
      }
    }
  }
  
  dynamic "notification_channels" {
    for_each = var.alert_email != null ? [google_monitoring_notification_channel.email[0].name] : []
    content {
      name = notification_channels.value
    }
  }
  
  alert_strategy {
    auto_close = "1800s"  # 30 minutes
  }
}

# Dashboard
resource "google_monitoring_dashboard" "auth_api" {
  dashboard_json = jsonencode({
    displayName = "${var.environment} Auth API Dashboard"
    mosaicLayout = {
      tiles = [
        {
          width = 6
          height = 4
          widget = {
            title = "Request Rate"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.cloud_run_service_name}\""
                    aggregation = {
                      alignmentPeriod = "60s"
                      perSeriesAligner = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                    }
                  }
                }
                plotType = "LINE"
                targetAxis = "Y1"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Requests/second"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          xPos = 6
          width = 6
          height = 4
          widget = {
            title = "Response Time"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.cloud_run_service_name}\""
                    aggregation = {
                      alignmentPeriod = "60s"
                      perSeriesAligner = "ALIGN_MEAN"
                      crossSeriesReducer = "REDUCE_PERCENTILE_95"
                    }
                  }
                }
                plotType = "LINE"
                targetAxis = "Y1"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Latency (ms)"
                scale = "LINEAR"
              }
            }
          }
        },
        {
          yPos = 4
          width = 12
          height = 4
          widget = {
            title = "Error Rate by Status Code"
            xyChart = {
              dataSets = [{
                timeSeriesQuery = {
                  timeSeriesFilter = {
                    filter = "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${var.cloud_run_service_name}\""
                    aggregation = {
                      alignmentPeriod = "300s"
                      perSeriesAligner = "ALIGN_RATE"
                      crossSeriesReducer = "REDUCE_SUM"
                      groupByFields = ["metric.labels.response_code_class"]
                    }
                  }
                }
                plotType = "STACKED_AREA"
                targetAxis = "Y1"
              }]
              timeshiftDuration = "0s"
              yAxis = {
                label = "Requests/second"
                scale = "LINEAR"
              }
            }
          }
        }
      ]
    }
  })
}
