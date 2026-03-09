# app/use_cases/auth/confirm_email.py
from app.use_cases.ports import UnitOfWork


class ConfirmEmail:
    """Handles email confirmation."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, token: str):
        """Confirm the user's email address."""
        async with self.uow:
            et = await self.uow.email_token_repo.get_valid(token, "confirm_email")
            if not et:
                raise ValueError("Token inválido o expirado")
            user = await self.uow.user_repo.get_by_id(et.user_id)
            user.email_verified = True
            await self.uow.user_repo.update(user)
            await self.uow.email_token_repo.mark_used(et.id)
            await self.uow.commit()
            return {"user": user}
