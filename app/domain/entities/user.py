from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class User:
    """Represents a user entity."""
    email: str
    full_name: str
    id: int | None = None
    picture_url: str | None = None
    google_sub: str | None = None
    password_hash: str | None = None
    email_verified: bool = False
    last_login_at: datetime | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Onboarding fields
    onboarding_completed: bool = False
    onboarding_completed_at: datetime | None = None
    needs_nutritional_plan: bool | None = None
    sex: str | None = None  # 'male', 'female', 'other'
    height_cm: float | None = None
    weight_kg: float | None = None
    activity_level: str | None = None  # 'sedentary', 'light', 'moderate', 'active', 'very_active'
    sport: str | None = None
    goals: List[str] = field(default_factory=list)
    available_foods: List[str] = field(default_factory=list)
    target_calories: int | None = None

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
        return cls(
            email=model.email,
            full_name=model.full_name,
            id=model.id,
            picture_url=model.picture_url,
            google_sub=model.google_sub,
            password_hash=model.password_hash,
            email_verified=model.email_verified,
            last_login_at=model.last_login_at,
            created_at=model.created_at,
            updated_at=model.updated_at,
            onboarding_completed=getattr(model, 'onboarding_completed', False),
            onboarding_completed_at=getattr(model, 'onboarding_completed_at', None),
            needs_nutritional_plan=getattr(model, 'needs_nutritional_plan', None),
            sex=getattr(model, 'sex', None),
            height_cm=float(model.height_cm) if getattr(model, 'height_cm', None) else None,
            weight_kg=float(model.weight_kg) if getattr(model, 'weight_kg', None) else None,
            activity_level=getattr(model, 'activity_level', None),
            sport=getattr(model, 'sport', None),
            goals=getattr(model, 'goals', None) or [],
            available_foods=getattr(model, 'available_foods', None) or [],
            target_calories=getattr(model, 'target_calories', None),
        )

    def to_model_data(self) -> dict:
        """Convert User entity to dictionary for SQLAlchemy model creation."""
        return {
            "email": self.email,
            "full_name": self.full_name,
            "picture_url": self.picture_url,
            "google_sub": self.google_sub,
            "password_hash": self.password_hash,
            "email_verified": self.email_verified,
            "last_login_at": self.last_login_at,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "onboarding_completed": self.onboarding_completed,
            "onboarding_completed_at": self.onboarding_completed_at,
            "needs_nutritional_plan": self.needs_nutritional_plan,
            "sex": self.sex,
            "height_cm": self.height_cm,
            "weight_kg": self.weight_kg,
            "activity_level": self.activity_level,
            "sport": self.sport,
            "goals": self.goals,
            "available_foods": self.available_foods,
            "target_calories": self.target_calories,
        }
