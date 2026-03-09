# ============================================
# Auth API Infrastructure - Main Configuration
# ============================================

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  # Uncomment and configure for remote state storage
  # backend "gcs" {
  #   bucket = "your-terraform-state-bucket"
  #   prefix = "auth-api"
  # }
}

# ============================================
# Provider Configuration
# ============================================
provider "google" {
  project = var.project_id
  region  = var.region
}

provider "google-beta" {
  project = var.project_id
  region  = var.region
}

# ============================================
# Local Values
# ============================================
locals {
  app_name = "auth-api"
  environment = var.environment
  
  # Common labels
  common_labels = {
    project     = local.app_name
    environment = local.environment
    managed_by  = "terraform"
  }
}

# ============================================
# Data Sources
# ============================================
data "google_project" "current" {
  project_id = var.project_id
}

# ============================================
# Modules
# ============================================

# Database module
module "database" {
  source = "./modules/database"
  
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  
  database_name     = "${local.app_name}-${local.environment}"
  database_user     = var.database_user
  database_password = var.database_password
  
  labels = local.common_labels
}

# Cloud Run module
module "cloud_run" {
  source = "./modules/cloud_run"
  
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  
  service_name = "${local.app_name}-${local.environment}"
  image_url    = var.image_url
  
  # Database connection
  database_url = module.database.connection_string
  
  # Environment variables
  environment_variables = var.environment_variables
  
  labels = local.common_labels
}

# IAM module
module "iam" {
  source = "./modules/iam"
  
  project_id  = var.project_id
  environment = var.environment
  
  cloud_run_service_account = module.cloud_run.service_account_email
  
  labels = local.common_labels
}

# Monitoring module
module "monitoring" {
  source = "./modules/monitoring"
  
  project_id  = var.project_id
  region      = var.region
  environment = var.environment
  
  cloud_run_service_name = module.cloud_run.service_name
  database_instance_name = module.database.instance_name
  
  labels = local.common_labels
}
