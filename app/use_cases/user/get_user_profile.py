"""Get user profile use case."""
from app.use_cases.ports import UnitOfWork
from app.domain.entities.user import User


class GetUserProfile:
    """Use case for retrieving user profile with onboarding data."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the use case.
        
        Args:
            uow: Unit of work for database operations.
        """
        self.uow = uow

    async def execute(self, user_id: int) -> User | None:
        """Execute the get user profile use case.
        
        Args:
            user_id: The ID of the user to retrieve.
            
        Returns:
            The User entity if found, None otherwise.
        """
        async with self.uow:
            return await self.uow.user_repo.get_by_id(user_id)
