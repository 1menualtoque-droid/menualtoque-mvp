# app/use_cases/auth/request_password_reset.py
from datetime import datetime, timedelta
from secrets import token_urlsafe

from app.domain.entities.email_tokens import EmailToken
from app.frameworks.email import send_password_reset_email
from app.use_cases.ports import EmailSender, UnitOfWork


class RequestPasswordReset:
    """Handles password reset requests."""

    def __init__(self, uow: UnitOfWork, mail: EmailSender, app_url: str):
        self.uow, self.mail, self.app_url = uow, mail, app_url

    async def execute(self, email: str):
        """Request a password reset for the user."""
        async with self.uow:
            user = await self.uow.user_repo.get_by_email(email)
            # Do not reveal user existence; still return OK
            if user:
                token = token_urlsafe(48)

                await self.uow.email_token_repo.add(
                    EmailToken(
                        user_id=user.id,
                        token=token,
                        purpose="reset_password",
                        expires_at=datetime.utcnow() + timedelta(minutes=15),
                    )
                )
                await self.uow.commit()
                link = f"{self.app_url}/reset-password?token={token}"
                await send_password_reset_email(
                    email_to=email,
                    username=user.full_name or email.split("@")[0],
                    reset_url=link,
                )
