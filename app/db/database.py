"""
Подключение к PostgreSQL через SQLAlchemy async + asyncpg.

Используем async-подход потому что FastAPI асинхронный —
блокирующие запросы к БД замедлили бы весь сервер.

При старте приложения вызывается init_db() который создаёт
таблицы если они ещё не существуют.
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


def _build_async_url(url: str) -> str:
    """
    Railway даёт DATABASE_URL в формате postgresql://...
    SQLAlchemy async требует postgresql+asyncpg://...
    Конвертируем автоматически.
    """
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    return url


engine = create_async_engine(
    _build_async_url(settings.database_url),
    echo=False,       # True — выводит SQL в логи (удобно при дебаге, шумно в проде)
    pool_size=5,      # максимум 5 постоянных соединений
    max_overflow=10,  # ещё 10 временных при пике нагрузки
)

# Фабрика сессий — используем в routers/services через dependency injection
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # объекты остаются доступны после commit()
)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей SQLAlchemy."""
    pass


async def init_db() -> None:
    """
    Создаёт все таблицы в БД если они ещё не существуют.
    Вызывается один раз при старте приложения (lifespan в main.py).
    """
    async with engine.begin() as conn:
        # import нужен здесь чтобы Base.metadata знала о моделях
        from app.db import models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """
    Dependency для FastAPI — даёт сессию БД в роутеры/сервисы.
    Автоматически закрывает сессию после завершения запроса.
    """
    async with AsyncSessionLocal() as session:
        yield session
