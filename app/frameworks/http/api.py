# app/frameworks/http/api.py
import logging
import textwrap

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.domain.errors import DomainError
from app.frameworks.http.error_handlers import (
    domain_error_handler,
    general_error_handler,
    validation_error_handler,
)
from app.frameworks.http.rate_limiter import limiter, rate_limit_handler
from slowapi.errors import RateLimitExceeded
from app.frameworks.http.routes import auth as auth_routes
from app.frameworks.http.routes import users as users_routes

# OAuth2 scheme for Swagger UI
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="auth/login/password",
    scheme_name="JWT",
    description="Enter JWT token in the format: Bearer <token>",
)


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add security schemes
    openapi_schema["components"]["securitySchemes"] = {
        "JWT": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter JWT token in the format: Bearer <token>",
        }
    }

    # Add global security
    openapi_schema["security"] = [{"JWT": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema


def create_app() -> FastAPI:
    app = FastAPI(
        title="Auth API Documentation",
        description=textwrap.dedent(
            """
            Welcome to the Auth API documentation. This API provides authentication and user management services.

            ### Authentication
            Most endpoints require authentication using JWT tokens. To authenticate:
            1. Use the `/auth/login/password` or `/auth/google` endpoint to get tokens
            2. Include the access token in the `Authorization` header as `Bearer <token>`
            3. The refresh token is automatically set as an HTTP-only cookie

            ### Rate Limiting
            The API implements rate limiting to prevent abuse. Please be mindful of your request volume.

            ### Error Handling
            The API uses standard HTTP status codes to indicate success or failure.
            - 2xx: Success
            - 4xx: Client errors (invalid input, unauthorized, etc.)
            - 5xx: Server errors
            """
        ),
        version="1.0.0",
        docs_url=None,  # Disable default docs
        redoc_url=None,  # Disable default redoc
        openapi_url="/api/v1/openapi.json",
        contact={"name": "Fitsuyo Support", "email": "support@paperperu.com"},
        license_info={"name": "Proprietary", "url": "https://paperperu.com/terms"},
    )

    # Custom OpenAPI schema
    app.openapi = custom_openapi

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)

    # Register error handlers
    app.add_exception_handler(DomainError, domain_error_handler)
    app.add_exception_handler(ValidationError, validation_error_handler)
    app.add_exception_handler(Exception, general_error_handler)

    # Include routers
    # Include routers with tags and prefixes
    app.include_router(auth_routes.router, prefix="/api/v1", tags=["Authentication"])
    app.include_router(users_routes.router, prefix="/api/v1", tags=["Users"])

    # Database connectivity check on startup
    @app.on_event("startup")
    async def check_database_connection():
        logger = logging.getLogger(__name__)
        try:
            # Use same settings as dependencies
            from app.frameworks.http.deps import settings

            engine = create_async_engine(settings.database_url, pool_pre_ping=True)
            async with engine.begin() as conn:
                await conn.execute(text("SELECT 1"))
            await engine.dispose()
            logger.info("Database connectivity check passed")
        except Exception as e:  # pragma: no cover - startup path
            logger.error("Database connectivity check failed", exc_info=e)
            # Keep app running but you will see clear logs

    # Custom docs endpoints
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url="/api/v1/openapi.json",
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
            swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        )

    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        return get_redoc_html(
            openapi_url="/api/v1/openapi.json",
            title=app.title + " - ReDoc",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
            with_google_fonts=False,
        )

    @app.get(
        "/health/db",
        status_code=status.HTTP_200_OK,
        tags=["Health"],
        summary="Check database connectivity",
        response_description="Database connection status",
    )
    async def check_db_health():
        """Check if the database is accessible."""
        from sqlalchemy.exc import SQLAlchemyError

        from app.frameworks.http.deps import settings

        try:
            engine = create_async_engine(settings.database_url, pool_pre_ping=True)
            async with engine.begin() as conn:
                result = await conn.scalar(text("SELECT 1"))
                if result != 1:
                    raise ValueError("Unexpected database response")

            return {
                "status": "healthy",
                "database": "connected",
                "details": "Successfully connected to the database",
            }
        except SQLAlchemyError as e:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={
                    "status": "unhealthy",
                    "database": "disconnected",
                    "error": str(e),
                    "details": "Failed to connect to the database",
                },
            )
        except Exception as e:
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={
                    "status": "error",
                    "database": "error",
                    "error": str(e),
                    "details": "Unexpected error while checking database connection",
                },
            )

    return app


app = create_app()
