from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    """User roles enum for role-based access control."""

    CLIENT = "client"
    RESTAURANT = "restaurant"


@dataclass
class User:
    """Represents a user entity."""

    email: str
    full_name: str
    role: UserRole = UserRole.CLIENT
    id: int | None = None
    picture_url: str | None = None
    google_sub: str | None = None
    password_hash: str | None = None
    email_verified: bool = False
    last_login_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def first_name(self) -> str:
        """Extract first name from full_name."""
        return self.full_name.split(" ", 1)[0] if self.full_name else ""

    @property
    def last_name(self) -> str:
        """Extract last name from full_name."""
        parts = self.full_name.split(" ", 1)
        return parts[1] if len(parts) > 1 else ""

    @classmethod
    def from_model(cls, model) -> "User":
        """Create User entity from SQLAlchemy model."""
        role = UserRole.CLIENT  # default fallback
        if hasattr(model, "role") and model.role:
            role = UserRole(model.role)

        return cls(
            email=model.email,
            full_name=model.full_name,
            role=role,
            id=model.id,
            picture_url=model.picture_url,
            google_sub=model.google_sub,
            password_hash=model.password_hash,
            email_verified=model.email_verified,
            last_login_at=model.last_login_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def to_model_data(self) -> dict:
        """Convert User entity to dictionary for SQLAlchemy model creation."""
        return {
            "email": self.email,
            "full_name": self.full_name,
            "role": self.role.value,
            "picture_url": self.picture_url,
            "google_sub": self.google_sub,
            "password_hash": self.password_hash,
            "email_verified": self.email_verified,
            "last_login_at": self.last_login_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @property
    def is_restaurant(self) -> bool:
        """Check if user has restaurant role."""
        return self.role == UserRole.RESTAURANT

    @property
    def is_client(self) -> bool:
        """Check if user has client role."""
        return self.role == UserRole.CLIENT
