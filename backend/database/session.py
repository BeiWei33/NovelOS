"""
SQLAlchemy engine and session factory for NovelOS.

Engine is lazily created on first use to allow import-time loading
without a running database.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

from core.config import settings


_engine = None
_async_session_factory = None


def get_engine():
    global _engine
    if _engine is None:
        from sqlalchemy.ext.asyncio import create_async_engine
        _engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
    return _engine


def get_session_factory():
    global _async_session_factory
    if _async_session_factory is None:
        from sqlalchemy.ext.asyncio import AsyncSession as _AsyncSession
        _async_session_factory = async_sessionmaker(
            get_engine(), class_=_AsyncSession, expire_on_commit=False
        )
    return _async_session_factory


class Base(DeclarativeBase):
    pass


async def get_session() -> AsyncSession:  # type: ignore
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    finally:
        await session.close()