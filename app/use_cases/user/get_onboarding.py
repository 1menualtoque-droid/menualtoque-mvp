"""Get onboarding data use case."""
from typing import Dict, Optional

from app.use_cases.ports import UnitOfWork


class GetOnboarding:
    """Use case for retrieving user onboarding data."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the use case.
        
        Args:
            uow: Unit of work for database operations.
        """
        self.uow = uow

    async def execute(self, user_id: int) -> Optional[Dict]:
        """Execute the get onboarding use case.
        
        Args:
            user_id: ID of the user
            
        Returns:
            Dictionary with onboarding data if exists, None otherwise
            
        Raises:
            ValueError: If user not found
        """
        async with self.uow:
            user = await self.uow.user_repo.get_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Return None if no onboarding data
            if not user.onboarding_completed and user.target_calories is None:
                return None
            
            return {
                "needs_nutritional_plan": user.needs_nutritional_plan,
                "sex": user.sex,
                "height_cm": user.height_cm,
                "weight_kg": user.weight_kg,
                "activity_level": user.activity_level,
                "sport": user.sport,
                "goals": user.goals or [],
                "available_foods": user.available_foods or [],
                "target_calories": user.target_calories,
                "completed_at": user.onboarding_completed_at
            }
