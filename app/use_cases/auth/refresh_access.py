from app.use_cases.ports import JWTService, UnitOfWork


class RefreshAccess:
    """Handles refreshing the access token."""

    def __init__(self, uow: UnitOfWork, jwt: JWTService):
        self.uow, self.jwt = uow, jwt

    async def execute(self, refresh_token: str):
        """Refresh the access token."""
        payload = self.jwt.parse_refresh(refresh_token)  # raises if invalid
        user_id = int(payload["sub"])
        jti = payload["jti"]

        async with self.uow:
            rt = await self.uow.refresh_repo.get_by_jti(jti)
            if not rt or rt.revoked:
                raise ValueError("Refresh inválido")
            user = await self.uow.user_repo.get_by_id(user_id)
            if not user:
                raise ValueError("Usuario no encontrado")

            access = self.jwt.make_access(user)
            # (optional rotation) keep the same refresh cookie for simplicity now
            return access
