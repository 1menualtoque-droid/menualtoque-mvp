"""Complete onboarding use case."""
from datetime import datetime
from typing import Dict, List

from app.use_cases.ports import UnitOfWork
from app.domain.entities.user import User


def calculate_bmr(sex: str, weight_kg: float, height_cm: float, age: int = 25) -> float:
    """Calculate Basal Metabolic Rate using Harris-Benedict formula.
    
    Args:
        sex: User's sex ('male', 'female', 'other')
        weight_kg: Weight in kilograms
        height_cm: Height in centimeters
        age: Age in years (default 25)
        
    Returns:
        Basal Metabolic Rate in kcal/day
    """
    if sex == "male":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    elif sex == "female":
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    else:  # other
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 78
    return bmr


def get_activity_multiplier(activity_level: str) -> float:
    """Get activity multiplier for TDEE calculation.
    
    Args:
        activity_level: Activity level string
        
    Returns:
        Multiplier value
    """
    return {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9
    }[activity_level]


class CompleteOnboarding:
    """Use case for completing user onboarding."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the use case.
        
        Args:
            uow: Unit of work for database operations.
        """
        self.uow = uow

    async def execute(
        self,
        user_id: int,
        needs_nutritional_plan: bool,
        sex: str,
        height_cm: float,
        weight_kg: float,
        activity_level: str,
        sport: str,
        goals: List[str],
        available_foods: List[str]
    ) -> Dict[str, any]:
        """Execute the complete onboarding use case.
        
        Args:
            user_id: ID of the user completing onboarding
            needs_nutritional_plan: Whether user needs a nutritional plan
            sex: User's sex
            height_cm: Height in centimeters
            weight_kg: Weight in kilograms
            activity_level: Activity level
            sport: Primary sport or activity
            goals: List of fitness goals
            available_foods: List of available foods
            
        Returns:
            Dictionary with success message and target_calories
            
        Raises:
            ValueError: If user not found or onboarding already completed
        """
        async with self.uow:
            user = await self.uow.user_repo.get_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            if user.onboarding_completed:
                raise ValueError("Onboarding already completed")
            
            # Calculate target calories
            bmr = calculate_bmr(sex, weight_kg, height_cm)
            target_calories = int(bmr * get_activity_multiplier(activity_level))
            
            # Update user with onboarding data
            user.onboarding_completed = True
            user.onboarding_completed_at = datetime.utcnow()
            user.needs_nutritional_plan = needs_nutritional_plan
            user.sex = sex
            user.height_cm = height_cm
            user.weight_kg = weight_kg
            user.activity_level = activity_level
            user.sport = sport
            user.goals = goals
            user.available_foods = available_foods
            user.target_calories = target_calories
            
            await self.uow.user_repo.update(user)
            await self.uow.commit()
            
            return {
                "message": "Onboarding completed successfully",
                "target_calories": target_calories
            }
