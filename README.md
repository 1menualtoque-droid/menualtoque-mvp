# MenuAltoque API

An API built with FastAPI, PostgreSQL, and clean architecture principles. Designed for easy deployment with Docker, CI/CD, and infrastructure automation.

## 🚀 Features

- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Google OAuth**: Single sign-on with Google accounts
- **Email Verification**: Account verification and password reset via email
- **User Management**: Registration, profile management, and password changes
- **Clean Architecture**: Domain-driven design with clear separation of concerns
- **Production Ready**: Docker, CI/CD, monitoring, and infrastructure as code

## 📋 Prerequisites

- Python 3.12+
- Docker & Docker Compose
- PostgreSQL (optional, if not using Docker)
- Google Cloud Platform account (for deployment)

## 🏁 Quick Start

### 1. Clone and Setup

```bash
git clone <your-repository-url>
cd menualtoque-mvp
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```bash
# Database
POSTGRES_DB=auth-db
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_secure_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# JWT Configuration
JWT_SECRET=your_very_long_and_secure_jwt_secret_key
JWT_ISSUER=auth-api
JWT_AUDIENCE=auth-client

# Application
APP_URL=http://localhost:3000
EMAIL_FROM=noreply@yourdomain.com

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your_google_client_id

# Email Service (optional)
RESEND_API_KEY=your_resend_api_key
```

### 3. Start with Docker

```bash
docker-compose up -d
```

### 4. Run Migrations

```bash
alembic upgrade head
```

### 5. Start Development Server

```bash
uvicorn app.frameworks.http.api:app --reload
```

The API will be available at:

- **API**: `http://localhost:8000`
- **Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health/db`

## Database Migrations

### Creating Migrations

When you make changes to your SQLAlchemy models:

1. After changing your models, create a new migration:

   ```bash
   alembic revision --autogenerate -m "description of changes"
   ```

2. Review the generated migration file in `alembic/versions/`

3. Apply the migration:
   ```bash
   alembic upgrade head
   ```

### Common Migration Commands

- Create a new migration: `alembic revision --autogenerate -m "description"`
- Apply all pending migrations: `alembic upgrade head`
- Rollback last migration: `alembic downgrade -1`
- Check current migration: `alembic current`

## Development Workflow

1. Make your code changes
2. If you modified models, create and apply migrations
3. Test your changes locally
4. Commit your changes with a descriptive message

## 🏗️ Architecture & Project Structure

```
auth-api/
├── 📁 app/
│   ├── 📁 domain/               # Domain entities and business logic
│   │   ├── 📁 entities/         # User, EmailToken, RefreshToken
│   │   └── errors.py           # Domain exceptions
│   ├── 📁 use_cases/           # Application business logic
│   │   ├── 📁 auth/            # Authentication use cases
│   │   ├── 📁 user/            # User management use cases
│   │   └── ports.py            # Repository interfaces
│   ├── 📁 frameworks/          # External framework integrations
│   │   ├── 📁 http/            # FastAPI routes, schemas, middleware
│   │   └── 📁 persistence/     # Database implementations
│   └── 📁 interfaces/          # Dependency injection interfaces
├── 📁 infrastructure/          # Infrastructure as Code
│   └── 📁 terraform/           # GCP infrastructure modules
├── 📁 .github/workflows/       # CI/CD pipelines
├── 📁 config/environments/     # Environment-specific configs
├── 📁 scripts/                 # Deployment and utility scripts
├── 📁 alembic/                # Database migrations
└── 📁 tests/                  # Test suites
```

## 🧪 Testing

Run the full test suite:

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run tests with coverage
python -m pytest tests/ -v --cov=app --cov-report=html

# Run specific test file
python -m pytest tests/test_auth.py -v

# Run with database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/auth_db_test python -m pytest
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build production image
docker build --target production -t auth-api:latest .

# Run with environment-specific config
ENV_FILE=./config/environments/production.env docker-compose up -d
```

### Google Cloud Run Deployment

1. **Setup Infrastructure** (using Terraform):

```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values
terraform init
terraform plan
terraform apply
```

2. **Deploy via CI/CD**: Push to `main` branch for production or `develop` for staging

### Manual Deployment

```bash
# Build and push image
docker build -t gcr.io/your-project/auth-api:latest .
docker push gcr.io/your-project/auth-api:latest

# Deploy to Cloud Run
gcloud run deploy auth-api \
  --image gcr.io/your-project/auth-api:latest \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated
```

## 📊 API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login/password` - Login with password
- `POST /api/v1/auth/google` - Login with Google OAuth
- `POST /api/v1/auth/refresh` - Refresh access token
- `POST /api/v1/auth/logout` - Logout (revoke tokens)
- `POST /api/v1/auth/request-password-reset` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password
- `POST /api/v1/auth/confirm-email` - Confirm email address

### User Management

- `GET /api/v1/users/profile` - Get user profile
- `PUT /api/v1/users/profile` - Update user profile
- `POST /api/v1/users/complete-onboarding` - Complete user onboarding
- `POST /api/v1/users/change-password` - Change password

### Health & Monitoring

- `GET /health/db` - Database connectivity check
- `GET /docs` - API documentation (Swagger UI)
- `GET /redoc` - Alternative API documentation

## 🔧 Environment Configuration

### Development

Use `config/environments/development.env` for local development.

### Staging/Production

Environment variables are managed through:

- **Local**: Environment-specific `.env` files
- **Cloud Run**: Environment variables and Secret Manager
- **CI/CD**: GitHub Secrets

### Key Environment Variables

| Variable           | Description                         | Required |
| ------------------ | ----------------------------------- | -------- |
| `DATABASE_URL`     | PostgreSQL connection string        | ✅       |
| `JWT_SECRET`       | Secret key for JWT tokens           | ✅       |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID              | ⭕       |
| `RESEND_API_KEY`   | Email service API key               | ⭕       |
| `CORS_ORIGINS`     | Allowed CORS origins                | ✅       |
| `ENVIRONMENT`      | Environment name (dev/staging/prod) | ✅       |

## 🔄 CI/CD Pipeline

The project includes automated workflows for:

### Continuous Integration (`.github/workflows/ci.yml`)

- Code quality checks (Ruff formatting/linting)
- Security scanning (Safety, Bandit)
- Unit and integration tests
- Docker build validation

### Continuous Deployment

- **Staging** (`.github/workflows/cd-staging.yml`): Auto-deploy on `develop` branch
- **Production** (`.github/workflows/cd-production.yml`): Manual approval required

### Infrastructure (`.github/workflows/infrastructure.yml`)

- Terraform plan/apply automation
- Infrastructure security scanning
- Multi-environment support

## 📈 Monitoring & Observability

### Built-in Monitoring

- Health checks with database connectivity
- Structured JSON logging
- Request/response metrics
- Error tracking and alerting

### Google Cloud Monitoring

- Uptime monitoring
- Performance metrics dashboard
- Alert policies for errors and downtime
- Log aggregation in BigQuery

## 🔒 Security Features

- **JWT Authentication**: Stateless token-based auth
- **Refresh Token Rotation**: Secure token management
- **Password Hashing**: bcrypt with salt
- **Rate Limiting**: Prevent abuse and brute force
- **CORS Protection**: Configurable origin restrictions
- **SQL Injection Protection**: SQLAlchemy ORM
- **Input Validation**: Pydantic schema validation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Run tests and ensure they pass
6. Commit changes (`git commit -m 'Add amazing feature'`)
7. Push to branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## 📝 License

This project is licensed under the MIT License.
