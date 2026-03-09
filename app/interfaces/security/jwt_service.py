import uuid
from datetime import UTC, datetime, timedelta

import jwt

from app.domain.entities.user import User
from app.use_cases.ports import JWTService


class JWTServiceImpl(JWTService):
    def __init__(self, settings):
        self.s = settings

    def _now(self):
        return datetime.now(UTC)

    def make_access(self, user: User) -> str:
        exp = self._now() + timedelta(minutes=self.s.JWT_ACCESS_TTL_MIN)
        payload = {
            "sub": str(user.id),
            "email": user.email,
            "iss": self.s.JWT_ISSUER,
            "aud": self.s.JWT_AUDIENCE,
            "exp": exp,
            "type": "access",
        }
        return jwt.encode(payload, self.s.JWT_SECRET, algorithm="HS256")

    def make_refresh(self, user: User) -> tuple[str, str]:
        exp = self._now() + timedelta(days=self.s.JWT_REFRESH_TTL_DAYS)
        jti = uuid.uuid4().hex
        payload = {
            "sub": str(user.id),
            "jti": jti,
            "iss": self.s.JWT_ISSUER,
            "aud": self.s.JWT_AUDIENCE,
            "exp": exp,
            "type": "refresh",
        }
        return jwt.encode(payload, self.s.JWT_SECRET, algorithm="HS256"), jti

    def parse_refresh(self, token: str) -> dict:
        payload = jwt.decode(
            token, self.s.JWT_SECRET, audience=self.s.JWT_AUDIENCE, algorithms=["HS256"]
        )
        if payload.get("type") != "refresh":
            raise ValueError("Wrong token type")
        return payload

    def parse_access(self, token: str) -> dict:
        payload = jwt.decode(
            token, self.s.JWT_SECRET, audience=self.s.JWT_AUDIENCE, algorithms=["HS256"]
        )
        if payload.get("type") != "access":
            raise ValueError("Wrong token type")
        return payload
