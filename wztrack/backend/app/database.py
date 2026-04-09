from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.models.base import Base

engine = create_async_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def init_db() -> None:
    """Create schema and all tables on startup. Safe to call repeatedly."""
    async with engine.begin() as conn:
        await conn.execute(
            __import__("sqlalchemy").text(f"CREATE SCHEMA IF NOT EXISTS {settings.db_schema}")
        )
        await conn.run_sync(Base.metadata.create_all)

    await _seed_admin()


async def _seed_admin() -> None:
    """Create the default admin account if no users exist."""
    from app.models.user import User
    from app.security import hash_password
    from sqlalchemy import select
    import uuid

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).limit(1))
        if result.scalar_one_or_none() is not None:
            return

        admin = User(
            id=uuid.uuid4(),
            email=settings.admin_email,
            display_name=settings.admin_display_name,
            password_hash=hash_password(settings.admin_password),
            role="admin",
            is_active=True,
        )
        session.add(admin)
        await session.commit()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
