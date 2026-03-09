# app/use_cases/ports.py
from typing import Protocol

from app.domain.entities.email_tokens import EmailToken
from app.domain.entities.refresh_token import RefreshToken
from app.domain.entities.user import User


class UserRepo(Protocol):
    """Protocol defining the interface for user repository operations.

    This protocol defines the contract that any user repository implementation
    must follow to be compatible with the application's use cases.
    """

    async def get_by_email(self, email: str) -> User | None: ...
    async def get_by_google_sub(self, sub: str) -> User | None: ...
    async def get_by_id(self, user_id: int) -> User | None: ...
    async def add(self, user: User) -> User: ...
    async def update(self, user: User) -> None: ...
    async def delete(self, user_id: int) -> None: ...


class RefreshTokenRepo(Protocol):
    """Protocol defining the interface for refresh token repository operations.

    This protocol defines the contract that any refresh token repository implementation
    must follow to be compatible with the application's use cases.
    """

    async def add(self, rt: RefreshToken) -> RefreshToken: ...
    async def get_by_jti(self, jti: str) -> RefreshToken | None: ...
    async def revoke_all_for_user(self, user_id: int) -> int: ...
    async def mark_revoked(self, jti: str) -> None: ...


class EmailTokenRepo(Protocol):
    """Protocol defining the interface for email token repository operations.

    This protocol defines the contract that any email token repository implementation
    must follow to be compatible with the application's use cases.
    """

    async def add(self, et: EmailToken) -> EmailToken: ...
    async def get_valid(self, token: str, purpose: str) -> EmailToken | None: ...
    async def mark_used(self, email_token_id: int) -> None: ...


class JWTService(Protocol):
    """Protocol defining the interface for JWT service operations.

    This protocol defines the contract that any JWT service implementation
    must follow to be compatible with the application's use cases.
    """

    def make_access(self, user: User) -> str: ...
    def make_refresh(self, user: User) -> tuple[str, str]: ...  # returns (jwt, jti)
    def parse_refresh(self, token: str) -> dict: ...  # raises on invalid
    def parse_access(self, token: str) -> dict: ...  # raises on invalid


class PasswordHasher(Protocol):
    """Protocol defining the interface for password hasher operations.

    This protocol defines the contract that any password hasher implementation
    must follow to be compatible with the application's use cases.
    """

    def hash(self, password: str) -> str: ...
    def verify(self, password: str, password_hash: str) -> bool: ...


class EmailSender(Protocol):
    """Protocol defining the interface for email sender operations.

    This protocol defines the contract that any email sender implementation
    must follow to be compatible with the application's use cases.
    """

    async def send(self, to: str, subject: str, html: str) -> None: ...


class GoogleTokenVerifier(Protocol):
    """Protocol defining the interface for Google token verifier operations.

    This protocol defines the contract that any Google token verifier implementation
    must follow to be compatible with the application's use cases.
    """

    async def verify(
        self, id_token: str
    ) -> dict: ...  # returns {sub, email, name, picture, email_verified}


class UnitOfWork(Protocol):
    """Protocol defining the interface for unit of work operations.

    This protocol defines the contract that any unit of work implementation
    must follow to be compatible with the application's use cases.
    """

    user_repo: UserRepo
    refresh_repo: RefreshTokenRepo
    email_token_repo: EmailTokenRepo

    async def __aenter__(self): ...
    async def __aexit__(self, exc_type, exc, tb): ...
    async def commit(self): ...
    async def rollback(self): ...
