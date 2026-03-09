# app/frameworks/settings.py

from pydantic import AnyHttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings and configuration.

    This class handles all configuration settings for the application, including database connection,
    JWT authentication, and third-party service credentials. Settings can be loaded from environment
    variables (with .env file support) or use the default values defined here.

    Attributes:
        POSTGRES_*: Individual database connection parameters
        JWT_*: JWT authentication settings
        APP_URL: Base URL of the frontend application
        GOOGLE_CLIENT_ID: Google OAuth2 client ID
        EMAIL_FROM: Default sender email address
        RESEND_API_KEY: API key for Resend email service
    """

    POSTGRES_USER: str | None = "postgres"
    POSTGRES_PASSWORD: str | None = "postgres"
    POSTGRES_DB: str | None = "fitsuyo"
    POSTGRES_HOST: str | None = "localhost"
    POSTGRES_PORT: str | None = "5432"

    @property
    def database_url(self) -> str:
        """Generate an async PostgreSQL database connection URL.

        This URL is used for async database operations. It uses the asyncpg driver
        for asynchronous PostgreSQL access. The URL is constructed from individual
        POSTGRES_* environment variables to avoid redundancy.

        Returns:
            str: A PostgreSQL connection URL with the asyncpg driver.
        """
        return (
            f"postgresql+asyncpg://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_database_url(self) -> str:
        """Generate a synchronous database connection URL.

        This URL is used for operations that require a synchronous database connection,
        such as Alembic migrations. It uses the psycopg2 driver for synchronous
        PostgreSQL access.

        Returns:
            str: A PostgreSQL connection URL with the psycopg2 driver and UTC timezone setting.
        """
        return (
            f"postgresql+psycopg2://"
            f"{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
            f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            "?options=-c timezone=utc"
        )

    JWT_SECRET: str = "change-me"
    JWT_ISSUER: str = "fitsuyo"
    JWT_AUDIENCE: str = "fitsuyo-client"
    JWT_ACCESS_TTL_MIN: int = 15
    JWT_REFRESH_TTL_DAYS: int = 30

    APP_URL: AnyHttpUrl = "http://localhost:3000"

    GOOGLE_CLIENT_ID: str = "your_client_id.apps.googleusercontent.com"
    EMAIL_FROM: str = "no-reply@paperperu.com"
    RESEND_API_KEY: str | None = None

    class Config:
        """Pydantic model configuration for Settings.

        This nested class configures how the Settings class loads and validates environment variables.

        Attributes:
            env_file: Specifies the .env file to load environment variables from.
            env_file_encoding: Encoding of the .env file.
            extra: Controls handling of extra fields (set to 'allow' to permit extra fields).
        """

        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow extra fields from environment
