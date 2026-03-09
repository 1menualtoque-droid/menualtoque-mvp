#!/bin/bash
set -e

echo "Starting Auth API..."

# Get port from Cloud Run environment variable, default to 8000
PORT=${PORT:-8000}
echo "Using port: ${PORT}"

# Wait for database to be ready (useful for containerized deployments)
# Add timeout to prevent infinite waiting
if [ -n "${POSTGRES_HOST}" ] && [ "${POSTGRES_HOST}" != "localhost" ]; then
    echo "Waiting for database to be ready at ${POSTGRES_HOST}:${POSTGRES_PORT:-5432}..."
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    until pg_isready -h "${POSTGRES_HOST}" -p "${POSTGRES_PORT:-5432}" -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" 2>/dev/null; do
        RETRY_COUNT=$((RETRY_COUNT + 1))
        if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
            echo "WARNING: Database connection check failed after ${MAX_RETRIES} attempts. Continuing anyway..."
            break
        fi
        echo "Database is unavailable - sleeping (attempt ${RETRY_COUNT}/${MAX_RETRIES})"
        sleep 2
    done
    
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
        echo "Database is ready!"
    fi
else
    echo "Skipping database readiness check (localhost or no POSTGRES_HOST set)"
fi

# Run database migrations
echo "=========================================="
echo "DEPLOYMENT STATE: Starting migrations"
echo "=========================================="
echo "Timestamp: $(date)"
echo "Database Host: ${POSTGRES_HOST}"
echo "Database Name: ${POSTGRES_DB}"
echo "Database User: ${POSTGRES_USER}"
echo "Port: ${POSTGRES_PORT}"
echo ""

echo "STEP 1: Checking current alembic version..."
alembic current || echo "No alembic version found (fresh database)"
echo ""

echo "STEP 2: Running alembic upgrade head..."
if alembic upgrade head 2>&1; then
    echo ""
    echo "=========================================="
    echo "✓ MIGRATIONS COMPLETED SUCCESSFULLY"
    echo "=========================================="
    echo "STEP 3: Verifying final alembic version..."
    alembic current
else
    EXIT_CODE=$?
    echo ""
    echo "=========================================="
    echo "✗ MIGRATION FAILED! Exit code: ${EXIT_CODE}"
    echo "=========================================="
    echo "Current alembic state:"
    alembic current || true
    echo ""
    echo "Database connection test:"
    python -c "from app.frameworks.settings import Settings; s=Settings(); print(f'Sync URL: {s.sync_database_url}')" || true
    exit 1
fi
echo ""

# Start the application
echo "Starting application server on port ${PORT}..."
exec uvicorn app.frameworks.http.api:app --host 0.0.0.0 --port "${PORT}"

