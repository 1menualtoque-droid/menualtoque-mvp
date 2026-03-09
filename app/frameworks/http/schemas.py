from datetime import datetime
from enum import StrEnum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, EmailStr, Field, field_validator

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str = Field(..., description="Machine-readable error code")
    message: str = Field(..., description="Human-readable error message")
    target: str | None = Field(
        None, description="The target of the error (field name, etc.)"
    )
    details: dict[str, Any] | None = Field(None, description="Additional error details")


class Meta(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = "1.0"


class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: T | None = None
    error: ErrorDetail | None = None
    meta: Meta = Field(default_factory=Meta)

    @classmethod
    def create_success(cls, data: T, meta: Meta | None = None) -> "ApiResponse[T]":
        return cls(success=True, data=data, meta=meta or Meta())

    @classmethod
    def create_error(
        cls,
        code: str,
        message: str,
        status_code: int = 400,
        target: str | None = None,
        details: dict[str, Any] | None = None,
        meta: Meta | None = None,
    ) -> "ApiResponse[None]":
        return cls(
            success=False,
            error=ErrorDetail(
                code=code, message=message, target=target, details=details
            ),
            meta=meta or Meta(),
        )


class TokenType(StrEnum):
    BEARER = "bearer"
    REFRESH = "refresh"


class Token(BaseModel):
    """Authentication tokens for API access."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Type of token")
    expires_in: int = Field(default=900, description="Token expiration time in seconds")
    refresh_token: str | None = Field(
        None, description="Refresh token for obtaining new access tokens"
    )

    class Config:  # noqa: D106
        json_schema_extra = {  # noqa: RUF012
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 900,
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            }
        }


class RegisterIn(BaseModel):
    """User registration request model."""

    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(
        ..., min_length=2, max_length=255, description="User's full name"
    )
    role: str = Field("client", description="User role: 'client' or 'restaurant'")
    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one digit",
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:  # noqa: PLR2004
            raise ValueError("Password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v):
        """Validate role is one of the allowed values."""
        allowed = ["client", "restaurant"]
        if v not in allowed:
            raise ValueError(f"Role must be one of: {', '.join(allowed)}")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v):
        if not v.strip():
            raise ValueError("Full name cannot be empty")
        return v.strip()


class LoginIn(BaseModel):
    """User login credentials."""

    email: EmailStr = Field(..., description="Registered email address")
    password: str = Field(..., min_length=1, description="Account password")

    class Config:  # noqa: D106
        json_schema_extra = {  # noqa: RUF012
            "example": {
                "email": "patrick22karusso97@gmail.com",
                "password": "SecurePassword123!",
            }
        }


class UserOut(BaseModel):
    """User profile information."""

    id: int = Field(..., description="Unique user identifier")
    email: EmailStr = Field(..., description="User's email address")
    full_name: str = Field(..., description="User's full name")
    role: str = Field(..., description="User role: client or restaurant")
    picture_url: str | None = Field(None, description="URL to user's profile picture")
    email_verified: bool = Field(..., description="Whether the email has been verified")
    last_login_at: datetime | None = Field(
        None, description="Timestamp of last successful login"
    )
    created_at: datetime = Field(..., description="Account creation timestamp")
    updated_at: datetime = Field(..., description="Last profile update timestamp")

    model_config = {"from_attributes": True}


class UpdateUserProfileIn(BaseModel):
    """Partial user profile update request model."""

    full_name: str | None = Field(
        None, min_length=2, max_length=255, description="User's full name"
    )


class RefreshOut(BaseModel):
    access_token: str


class ChangePasswordIn(BaseModel):
    """Password change request model."""

    current_password: str = Field(
        ..., min_length=1, description="Current account password"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one digit)",
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("New password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("New password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("New password must contain at least one digit")
        return v


class ResetPasswordIn(BaseModel):
    """Password reset request model"""

    token: str = Field(
        ..., min_length=1, description="Password reset token received via email"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
        description="New password (must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one digit)",
    )

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError("New password must be at least 8 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("New password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("New password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("New password must contain at least one digit")
        return v


class ConfirmEmailIn(BaseModel):
    """Email confirmation request model"""

    token: str = Field(
        ..., min_length=1, description="Email confirmation token received via email"
    )

    class Config:
        json_schema_extra = {
            "example": {"token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}
        }


class RequestPasswordResetIn(BaseModel):
    """Password reset request initiation model"""

    email: EmailStr = Field(
        ..., description="Email address to send reset instructions to"
    )

    class Config:
        json_schema_extra = {"example": {"email": "user@example.com"}}


class GoogleSignInIn(BaseModel):
    """Google Sign-In request model"""

    id_token: str = Field(
        ...,
        min_length=1,
        description="Google ID token from the client-side Google Sign-In flow",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjE2MzI1NzQ2NTI0N2Y5Z..."
            }
        }


class LogoutAllIn(BaseModel):
    """Logout from all devices request model"""

    user_id: int = Field(..., gt=0, description="User ID to log out from all devices")

    class Config:
        json_schema_extra = {"example": {"user_id": 1}}


class MessageResponse(BaseModel):
    """Generic API response message"""

    message: str = Field(..., description="Response message")

    class Config:
        json_schema_extra = {"example": {"message": "Operation completed successfully"}}


class ErrorResponse(BaseModel):
    """Standard error response format"""

    error: str = Field(..., description="Error type or category")
    detail: str | None = Field(None, description="Detailed error message")
    code: str | None = Field(None, description="Application-specific error code")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "authentication_error",
                "detail": "Invalid credentials",
                "code": "AUTH_001",
            }
        }
