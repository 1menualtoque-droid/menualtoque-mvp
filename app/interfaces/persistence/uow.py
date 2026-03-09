# app/interfaces/persistence/uow.py
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.interfaces.persistence.repositories import (
    SQLEmailTokenRepo,
    SQLRefreshTokenRepo,
    SQLUserRepo,
)


class SQLAlchemyUnitOfWork:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._sf = session_factory
        self.session: AsyncSession | None = None
        self.user_repo = None
        self.refresh_repo = None
        self.email_token_repo = None

    async def __aenter__(self):
        self.session = self._sf()
        self.user_repo = SQLUserRepo(self.session)
        self.refresh_repo = SQLRefreshTokenRepo(self.session)
        self.email_token_repo = SQLEmailTokenRepo(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc:
            await self.session.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    async def rollback(self):
        await self.session.rollback()
