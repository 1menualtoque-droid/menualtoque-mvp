from datetime import datetime, timedelta

from app.domain.entities.refresh_token import RefreshToken
from app.domain.entities.user import User
from app.use_cases.ports import GoogleTokenVerifier, JWTService, UnitOfWork


class GoogleSignIn:
    """Handles Google sign-in."""

    def __init__(self, uow: UnitOfWork, gv: GoogleTokenVerifier, jwt: JWTService):
        self.uow, self.gv, self.jwt = uow, gv, jwt

    async def execute(self, id_token: str):
        """Sign in the user using Google."""
        payload = await self.gv.verify(id_token)  # raises if invalid
        sub = payload["sub"]
        email = payload["email"]
        name = payload.get("name", "")
        pic = payload.get("picture")

        async with self.uow:
            user = await self.uow.user_repo.get_by_google_sub(sub)
            if not user:
                user = await self.uow.user_repo.get_by_email(email)
            if user:
                user.last_login_at = datetime.utcnow()
                if not user.google_sub:  # link if same email
                    user.google_sub = sub
                if not user.picture_url and pic:
                    user.picture_url = pic
                await self.uow.user_repo.update(user)
            else:
                user = await self.uow.user_repo.add(
                    User(
                        email=email,
                        full_name=name,
                        picture_url=pic,
                        google_sub=sub,
                        email_verified=True,
                        last_login_at=datetime.utcnow(),
                    )
                )
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
            return user, access, refresh
