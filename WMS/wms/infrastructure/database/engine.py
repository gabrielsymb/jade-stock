"""
SQLAlchemy Engine Configuration
Configuração centralizada do engine PostgreSQL com async/await
"""

import os
from typing import AsyncGenerator

from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

# Configurações do banco de dados
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://wms:wms@localhost:5432/wms"
)

# Engine assíncrono PostgreSQL
engine = create_async_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_DEBUG", "false").lower() == "true",
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600,
    future=True,
)

# Session factory assíncrona
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    future=True,
)

# Metadata para Alembic
metadata = MetaData(
    naming_convention={
        "ix": "ix_%(column_0_label)s",
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    }
)

# Base declarativa para models
class Base(DeclarativeBase):
    """Base declarativa para todos os models SQLAlchemy"""
    metadata = metadata


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency injection para FastAPI
    Fornece sessão assíncrona do banco de dados
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Cria todas as tabelas definidas nos models"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables() -> None:
    """Remove todas as tabelas (apenas para testes)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
