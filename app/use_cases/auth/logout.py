# app/use_cases/auth/logout.py
from app.use_cases.ports import JWTService, UnitOfWork


class Logout:
    """Handles user logout."""

    def __init__(self, uow: UnitOfWork, jwt: JWTService):
        self.uow, self.jwt = uow, jwt

    async def execute(self, refresh_token: str):
        """Logout the user by revoking the refresh token."""
        payload = self.jwt.parse_refresh(refresh_token)
        jti = payload["jti"]
        async with self.uow:
            await self.uow.refresh_repo.mark_revoked(jti)
            await self.uow.commit()
            return True


class LogoutAll:
    """Handles user logout from all devices."""

    def __init__(self, uow: UnitOfWork):
        self.uow = uow

    async def execute(self, user_id: int):
        """Logout the user from all devices by revoking all refresh tokens."""
        async with self.uow:
            await self.uow.refresh_repo.revoke_all_for_user(user_id)
            await self.uow.commit()
            return True
