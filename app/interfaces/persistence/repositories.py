# app/interfaces/persistence/repositories.py
from __future__ import annotations

from typing import Any

from sqlalchemy import and_, delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.entities.email_tokens import EmailToken
from app.domain.entities.refresh_token import RefreshToken
from app.domain.entities.user import User
from app.interfaces.persistence.models import (
    EmailTokenModel,
    RefreshTokenModel,
    UserModel,
)

# ---------------------------------------------------------------------------
# Helpers: map Domain <-> ORM safely (supports Value Objects with `.value`)
# ---------------------------------------------------------------------------


def _val(x: Any) -> Any:
    """Return VO.value if present, else the primitive itself."""
    return getattr(x, "value", x)


def _user_from_model(m: UserModel) -> User:
    return User.from_model(m)


def _user_to_values(u: User) -> dict[str, Any]:
    return {
        "email": _val(u.email),
        "full_name": _val(u.full_name),
        "role": u.role.value,
        "picture_url": u.picture_url,
        "google_sub": u.google_sub,
        "password_hash": _val(u.password_hash) if u.password_hash else None,
        "email_verified": u.email_verified,
        "last_login_at": u.last_login_at,
        # updated_at set on UPDATE using DB clock below
    }


def _rt_from_model(m: RefreshTokenModel) -> RefreshToken:
    return RefreshToken(
        id=m.id,
        user_id=m.user_id,
        jti=m.jti,
        revoked=m.revoked,
        expires_at=m.expires_at,
        created_at=m.created_at,
    )


def _rt_to_values(rt: RefreshToken) -> dict[str, Any]:
    return {
        "user_id": rt.user_id,
        "jti": rt.jti,
        "revoked": rt.revoked,
        "expires_at": rt.expires_at,
    }


def _et_from_model(m: EmailTokenModel) -> EmailToken:
    return EmailToken(
        id=m.id,
        user_id=m.user_id,
        token=m.token,
        purpose=m.purpose,
        used=m.used,
        expires_at=m.expires_at,
        created_at=m.created_at,
    )


def _et_to_values(et: EmailToken) -> dict[str, Any]:
    return {
        "user_id": et.user_id,
        "token": et.token,
        "purpose": et.purpose,
        "used": et.used,
        "expires_at": et.expires_at,
    }


# ---------------------------------------------------------------------------
# User Repository (implements UserRepo port)
# ---------------------------------------------------------------------------


class SQLUserRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def get_by_email(self, email: str) -> User | None:
        q = select(UserModel).where(UserModel.email == email.lower().strip())
        r = await self.s.execute(q)
        m = r.scalar_one_or_none()
        return _user_from_model(m) if m else None

    async def get_by_google_sub(self, sub: str) -> User | None:
        q = select(UserModel).where(UserModel.google_sub == sub)
        r = await self.s.execute(q)
        m = r.scalar_one_or_none()
        return _user_from_model(m) if m else None

    async def get_by_id(self, user_id: int) -> User | None:
        q = select(UserModel).where(UserModel.id == user_id)
        r = await self.s.execute(q)
        m = r.scalar_one_or_none()
        return _user_from_model(m) if m else None

    async def add(self, user: User) -> User:
        m = UserModel(**_user_to_values(user))
        self.s.add(m)
        await self.s.flush()  # assigns PK
        await self.s.refresh(m)
        user.id = m.id
        user.created_at = m.created_at
        user.updated_at = m.updated_at
        return user

    async def update(self, user: User) -> None:
        values = _user_to_values(user)
        # let DB set updated_at = now()
        values["updated_at"] = func.now()
        await self.s.execute(
            update(UserModel).where(UserModel.id == user.id).values(**values)
        )

    async def delete(self, user_id: int) -> None:
        """Hard delete user and all related data (cascades via FK constraints)."""
        await self.s.execute(delete(UserModel).where(UserModel.id == user_id))


# ---------------------------------------------------------------------------
# Refresh Token Repository (implements RefreshTokenRepo port)
# ---------------------------------------------------------------------------


class SQLRefreshTokenRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def add(self, rt: RefreshToken) -> RefreshToken:
        m = RefreshTokenModel(**_rt_to_values(rt))
        self.s.add(m)
        await self.s.flush()
        await self.s.refresh(m)
        rt.id = m.id
        return rt

    async def get_by_jti(self, jti: str) -> RefreshToken | None:
        q = select(RefreshTokenModel).where(RefreshTokenModel.jti == jti)
        r = await self.s.execute(q)
        m = r.scalar_one_or_none()
        return _rt_from_model(m) if m else None

    async def mark_revoked(self, jti: str) -> None:
        await self.s.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.jti == jti)
            .values(revoked=True)
        )

    async def revoke_all_for_user(self, user_id: int) -> int:
        res = await self.s.execute(
            update(RefreshTokenModel)
            .where(RefreshTokenModel.user_id == user_id)
            .values(revoked=True)
        )
        # SQLAlchemy 2.x returns CursorResult; rowcount may be -1 for some drivers.
        return getattr(res, "rowcount", 0) or 0


# ---------------------------------------------------------------------------
# Email Token Repository (implements EmailTokenRepo port)
# ---------------------------------------------------------------------------


class SQLEmailTokenRepo:
    def __init__(self, session: AsyncSession):
        self.s = session

    async def add(self, et: EmailToken) -> EmailToken:
        m = EmailTokenModel(**_et_to_values(et))
        self.s.add(m)
        await self.s.flush()
        await self.s.refresh(m)
        et.id = m.id
        return et

    async def get_valid(self, token: str, purpose: str) -> EmailToken | None:
        q = select(EmailTokenModel).where(
            and_(
                EmailTokenModel.token == token,
                EmailTokenModel.purpose == purpose,
                EmailTokenModel.used.is_(False),
                EmailTokenModel.expires_at > func.now(),
            )
        )
        r = await self.s.execute(q)
        m = r.scalar_one_or_none()
        return _et_from_model(m) if m else None

    async def mark_used(self, email_token_id: int) -> None:
        await self.s.execute(
            update(EmailTokenModel)
            .where(EmailTokenModel.id == email_token_id)
            .values(used=True)
        )
