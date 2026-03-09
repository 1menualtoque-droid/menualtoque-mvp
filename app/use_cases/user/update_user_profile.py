"""Update user profile use case."""

from app.domain.entities.user import User
from app.use_cases.ports import UnitOfWork


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
        full_name: str | None = None,
    ) -> User:
        """Execute the update user profile use case.

        Args:
            user_id: ID of the user to update
            full_name: New full name (optional)

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

            await self.uow.user_repo.update(user)
            await self.uow.commit()

            return user
