import logging
from datetime import datetime, timedelta
from secrets import token_urlsafe

from app.domain.entities.email_tokens import EmailToken
from app.domain.entities.user import User
from app.domain.errors import EmailAlreadyExistsError
from app.frameworks.email import send_verification_email
from app.use_cases.ports import EmailSender, PasswordHasher, UnitOfWork

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class RegisterUser:  # noqa: D101
    def __init__(
        self, uow: UnitOfWork, hasher: PasswordHasher, mail: EmailSender, app_url: str
    ) -> None:
        self.uow, self.hasher, self.mail, self.app_url = uow, hasher, mail, app_url

    async def execute(self, email: str, full_name: str, password: str) -> User:
        """Register a new user."""
        logger.info("Starting user registration", extra={"email": email})
        async with self.uow:
            logger.debug("Checking if email already exists", extra={"email": email})
            if await self.uow.user_repo.get_by_email(email):
                logger.warning(
                    "Registration failed: email already registered",
                    extra={"email": email},
                )
                raise EmailAlreadyExistsError("Email ya registrado")

            logger.debug("Hashing password", extra={"email": email})
            user = await self.uow.user_repo.add(
                User(
                    email=email,
                    full_name=full_name,
                    password_hash=self.hasher.hash(password),
                    email_verified=False,
                    created_at=datetime.utcnow(),
                )
            )
            logger.info(
                "User created in repository", extra={"user_id": user.id, "email": email}
            )

            # Generate verification token
            token = token_urlsafe(48)
            verification_url = f"{self.app_url}/verify-email?token={token}"

            logger.debug(
                "Creating email confirmation token",
                extra={"user_id": user.id, "email": email, "purpose": "confirm_email"},
            )

            await self.uow.email_token_repo.add(
                EmailToken(
                    user_id=user.id,
                    token=token,
                    purpose="confirm_email",
                    expires_at=datetime.utcnow() + timedelta(days=1),
                    created_at=datetime.utcnow(),
                )
            )

            await self.uow.commit()

        # Send verification email using Resend
        try:
            await send_verification_email(
                email_to=email,
                username=full_name,
                verification_url=verification_url,
            )

            logger.info(
                "Verification email sent successfully",
                extra={"user_id": user.id, "email": email},
            )

        except Exception as e:
            logger.error(
                "Failed to send verification email",
                extra={"error": str(e), "email": email, "user_id": user.id},
                exc_info=True,
            )
            # Don't fail the registration if email sending fails
            # The user can request a new verification email later

        return user
