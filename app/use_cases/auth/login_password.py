# app/use_cases/auth/login_password.py
from datetime import datetime, timedelta

from app.domain.entities.refresh_token import RefreshToken
from app.domain.errors import EmailNotVerifiedError, InvalidCredentialsError
from app.use_cases.ports import JWTService, PasswordHasher, UnitOfWork


class LoginPassword:
    """Handles user authentication using email and password.

    This use case is responsible for authenticating users by verifying their
    email and password combination. It checks for valid credentials and returns
    authentication tokens upon successful login.

    Args:
        uow: Unit of Work instance for database operations
        hasher: Password hashing utility for verifying passwords
        jwt: JWT service for generating authentication tokens
    """

    def __init__(self, uow: UnitOfWork, hasher: PasswordHasher, jwt: JWTService):
        self.uow, self.hasher, self.jwt = uow, hasher, jwt

    async def execute(self, email: str, password: str) -> dict:
        """Authenticate a user using email and password.

        Verifies the provided credentials and returns authentication tokens if successful.
        Updates the user's last login timestamp and creates a new refresh token.

        Args:
            email: User's email address
            password: User's password (plaintext)

        Returns:
            dict: Dictionary containing 'access' and 'refresh' tokens

        Raises:
            InvalidCredentialsError: If email/password is incorrect or user doesn't exist
            EmailNotVerifiedError: If the user's email has not been verified yet
        """
        async with self.uow:
            user = await self.uow.user_repo.get_by_email(email)
            # uniform error to avoid user enumeration
            if not user or not user.password_hash:
                raise InvalidCredentialsError("Credenciales inválidas")
            if not self.hasher.verify(password, user.password_hash):
                raise InvalidCredentialsError("Credenciales inválidas")
            if not user.email_verified:
                raise EmailNotVerifiedError("Email no confirmado")

            user.last_login_at = datetime.utcnow()
            await self.uow.user_repo.update(user)

            access = self.jwt.make_access(user)
            refresh, jti = self.jwt.make_refresh(user)

            await self.uow.refresh_repo.add(
                RefreshToken(
                    user_id=user.id,
                    jti=jti,
                    revoked=False,
                    expires_at=datetime.utcnow() + timedelta(days=30),
                )
            )
            await self.uow.commit()
            return {"user": user, "access": access, "refresh": refresh}
