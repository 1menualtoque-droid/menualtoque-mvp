"""Delete user use case."""
from app.use_cases.ports import UnitOfWork


class DeleteUser:
    """Use case for deleting a user account."""

    def __init__(self, uow: UnitOfWork) -> None:
        """Initialize the use case.
        
        Args:
            uow: Unit of work for database operations.
        """
        self.uow = uow

    async def execute(self, user_id: int) -> None:
        """Execute the delete user use case.
        
        This performs a hard delete, removing the user and all related data
        (consumptions, summaries, tokens, etc.) through cascade deletes.
        
        Args:
            user_id: ID of the user to delete
            
        Raises:
            ValueError: If user not found
        """
        async with self.uow:
            user = await self.uow.user_repo.get_by_id(user_id)
            if not user:
                raise ValueError("User not found")
            
            await self.uow.user_repo.delete(user_id)
            await self.uow.commit()
