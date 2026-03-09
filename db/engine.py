"""
Async database engine configuration with WAL mode and checkpoint management.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession
from sqlalchemy.pool import NullPool, AsyncAdaptedQueuePool
from sqlalchemy import event, text

from config import config

logger = logging.getLogger(__name__)

_engine: Optional[AsyncEngine] = None


def get_database_url() -> str:
    """Convert sync database URL to async with aiosqlite."""
    url = config.DATABASE_URL
    if url.startswith("sqlite:///"):
        # Replace with aiosqlite
        return url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
    # For PostgreSQL, we'd use asyncpg, but keep as is for now
    return url.replace("postgresql://", "postgresql+asyncpg://", 1)


async def init_engine() -> AsyncEngine:
    """Initialize the async engine with WAL settings."""
    global _engine
    if _engine is not None:
        return _engine

    db_url = get_database_url()
    
    # Create engine with connection pooling
    _engine = create_async_engine(
        db_url,
        echo=config.DEBUG,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,  # verify connections before using
    )
    
    # Test connection and set up WAL for SQLite
    async with _engine.begin() as conn:
        if db_url.startswith("sqlite"):
            # Enable WAL mode
            await conn.execute(text("PRAGMA journal_mode=WAL"))
            # Set automatic checkpoint size (e.g., 1000 pages)
            await conn.execute(text("PRAGMA wal_autocheckpoint=1000"))
            
            # Get the current page size and calculate checkpoint threshold
            result = await conn.execute(text("PRAGMA page_size"))
            page_size = result.scalar() or 4096
            # Schedule periodic checkpoint task
            asyncio.create_task(_periodic_checkpoint(_engine, page_size))
    
    logger.info("Async database engine initialized with WAL mode")
    return _engine


async def _periodic_checkpoint(engine: AsyncEngine, page_size: int, interval_days: int = 7):
    """
    Periodically run WAL checkpoint to move data into main DB.
    """
    while True:
        try:
            await asyncio.sleep(interval_days * 24 * 3600)  # days to seconds
            
            async with engine.begin() as conn:
                # Check WAL file size
                result = await conn.execute(text("PRAGMA wal_checkpoint(TRUNCATE)"))
                # result returns (busy, log, checkpointed)
                logger.info(f"WAL checkpoint executed: {result.fetchall()}")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Checkpoint failed: {e}")


async def close_engine():
    """Close the database engine properly."""
    global _engine
    if _engine is None:
        return
    await _engine.dispose()
    _engine = None
    logger.info("Database engine closed")


def get_engine() -> AsyncEngine:
    """Return the engine instance (must be initialized first)."""
    if _engine is None:
        raise RuntimeError("Database engine not initialized. Call init_engine() first.")
    return _engine