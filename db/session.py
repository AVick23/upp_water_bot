"""
Async session management.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from db.engine import get_engine


class DatabaseSessionManager:
    """Manages async sessions with a sessionmaker."""
    
    def __init__(self):
        self._sessionmaker: Optional[async_sessionmaker[AsyncSession]] = None
    
    def init(self):
        """Initialize sessionmaker with engine."""
        engine = get_engine()
        self._sessionmaker = async_sessionmaker(
            engine, expire_on_commit=False, class_=AsyncSession
        )
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Context manager for a session that automatically commits/rollbacks."""
        if self._sessionmaker is None:
            raise RuntimeError("SessionManager not initialized")
        
        session = self._sessionmaker()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    
    @asynccontextmanager
    async def begin_session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Context manager for a session that begins a transaction.
        Useful for when you need to control commit manually.
        """
        if self._sessionmaker is None:
            raise RuntimeError("SessionManager not initialized")
        
        session = self._sessionmaker()
        try:
            async with session.begin():
                yield session
        finally:
            await session.close()


# Global instance
session_manager = DatabaseSessionManager()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI-style dependency for getting a session."""
    async with session_manager.session() as session:
        yield session


# Convenience aliases
get_db = session_manager.session
get_transaction = session_manager.begin_session