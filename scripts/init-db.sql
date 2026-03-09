-- Database initialization script for Auth API
-- This script runs when the PostgreSQL container starts up

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Create application user if it doesn't exist
DO $$ 
BEGIN 
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'auth_app') THEN
        CREATE ROLE auth_app LOGIN PASSWORD 'secure_app_password';
    END IF;
END
$$;

-- Grant necessary permissions
GRANT CONNECT ON DATABASE auth_db TO auth_app;
GRANT USAGE ON SCHEMA public TO auth_app;
GRANT CREATE ON SCHEMA public TO auth_app;

-- Set default privileges for future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO auth_app;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT ON SEQUENCES TO auth_app;

-- Optimize PostgreSQL settings for the application
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET log_statement = 'all';
ALTER SYSTEM SET log_min_duration_statement = 1000;
ALTER SYSTEM SET log_line_prefix = '%t [%p]: [%l-1] user=%u,db=%d,app=%a,client=%h ';

-- Create indexes for common queries (will be created by Alembic migrations too)
-- These are here as documentation and backup

COMMENT ON DATABASE auth_db IS 'Authentication API database';
