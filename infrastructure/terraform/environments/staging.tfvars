# ============================================
# Terraform Configuration - Staging Environment
# ============================================

# Basic Configuration
environment = "staging"
region      = "us-central1"

# Application Configuration
image_url = "gcr.io/your-project-id/auth-api:staging-latest"

# Database Configuration
database_user = "postgres"

# CORS Configuration
allowed_origins = [
  "https://staging.yourdomain.com",
  "https://staging-app.yourdomain.com",
  "http://localhost:3000",
  "http://localhost:5173"
]

# Email Configuration
email_from = "noreply-staging@yourdomain.com"

# Application Environment Variables
environment_variables = {
  APP_NAME                    = "Auth API (Staging)"
  APP_VERSION                 = "staging"
  LOG_LEVEL                   = "INFO"
  LOG_FORMAT                  = "json"
  JWT_ACCESS_TTL_MIN          = "15"
  JWT_REFRESH_TTL_DAYS        = "7"
  RATE_LIMITER_STORAGE        = "memory://"
  RATE_LIMITER_DEFAULT_LIMIT  = "5000/hour"
}
