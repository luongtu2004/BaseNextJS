import logging
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()

engine_kwargs = {
    "echo": False,
}

# SQLite and StaticPool do not support pool sizing parameters
if not str(settings.database_url).startswith("sqlite"):
    engine_kwargs.update({
        "pool_pre_ping": True,
        "pool_size": settings.db_pool_size,
        "max_overflow": settings.db_max_overflow,
        "pool_timeout": settings.db_pool_timeout,
        "pool_recycle": settings.db_pool_recycle,
    })

engine = create_async_engine(settings.database_url, **engine_kwargs)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


def import_models() -> None:
    """Import side effects: register all ORM models on Base.metadata."""
    logger.debug("Importing ORM models...")
    import app.models  # noqa: F401
    logger.debug("ORM models imported successfully")
