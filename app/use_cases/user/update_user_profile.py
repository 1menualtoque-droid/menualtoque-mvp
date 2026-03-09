"""Update user profile use case."""
from typing import Dict, List, Optional

from app.use_cases.ports import UnitOfWork
from app.domain.entities.user import User
from app.use_cases.user.complete_onboarding import calculate_bmr, get_activity_multiplier


class UpdateUserProfile:
    """Use case for partially updating user profile."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the use case.
        
        Args:
            uow: Unit of work for database operations.
        """
        self.uow = uow

    async def execute(
        self,
        user_id: int,
        full_name: Optional[str] = None,
        weight_kg: Optional[float] = None,
        height_cm: Optional[float] = None,
        activity_level: Optional[str] = None,
        sport: Optional[str] = None,
        goals: Optional[List[str]] = None,
        available_foods: Optional[List[str]] = None
    ) -> User:
        """Execute the update user profile use case.
        
        Args:
            user_id: ID of the user to update
            full_name: New full name (optional)
            weight_kg: New weight (optional)
            height_cm: New height (optional)
            activity_level: New activity level (optional)
            sport: New sport (optional)
            goals: New goals list (optional)
            available_foods: New available foods list (optional)
            
        Returns:
            The updated User entity
            
        Raises:
            ValueError: If user not found
        """
        async with self.uow:
            user = await self.uow.user_repo.get_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            # Update fields if provided
            if full_name is not None:
                user.full_name = full_name
            
            if weight_kg is not None:
                user.weight_kg = weight_kg
            
            if height_cm is not None:
                user.height_cm = height_cm
            
            if activity_level is not None:
                user.activity_level = activity_level
            
            if sport is not None:
                user.sport = sport
            
            if goals is not None:
                user.goals = goals
            
            if available_foods is not None:
                user.available_foods = available_foods
            
            # Recalculate target_calories if any of the relevant fields changed
            if any([weight_kg, height_cm, activity_level]) and user.onboarding_completed:
                if user.sex and user.weight_kg and user.height_cm and user.activity_level:
                    bmr = calculate_bmr(user.sex, user.weight_kg, user.height_cm)
                    user.target_calories = int(bmr * get_activity_multiplier(user.activity_level))
            
            await self.uow.user_repo.update(user)
            await self.uow.commit()
            
            return user
