# ============================================
# Terraform Configuration - Production Environment
# ============================================

# Basic Configuration
environment = "production"
region      = "us-central1"

# Application Configuration
image_url = "gcr.io/your-project-id/auth-api:production-latest"

# Database Configuration
database_user = "postgres"

# CORS Configuration
allowed_origins = [
  "https://yourdomain.com",
  "https://app.yourdomain.com"
]

# Email Configuration
email_from = "noreply@yourdomain.com"

# Application Environment Variables
environment_variables = {
  APP_NAME                    = "Auth API"
  APP_VERSION                 = "1.0.0"
  LOG_LEVEL                   = "INFO"
  LOG_FORMAT                  = "json"
  JWT_ACCESS_TTL_MIN          = "15"
  JWT_REFRESH_TTL_DAYS        = "30"
  RATE_LIMITER_STORAGE        = "memory://"
  RATE_LIMITER_DEFAULT_LIMIT  = "1000/hour"
}
