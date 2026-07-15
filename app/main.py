from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import webhook


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    При старте:
    1. Создаём таблицы в БД если их нет
    2. Заполняем content_items начальными данными если таблица пустая
    """
    from app.db.database import init_db
    from app.db.database import AsyncSessionLocal
    from app.db.models import ContentItem
    from sqlalchemy import select

    await init_db()

    # Автоматический сидинг контента при первом запуске
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ContentItem).limit(1))
        if result.scalar_one_or_none() is None:
            import sys, os
            sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
            from scripts.seed_content import seed
            await seed()

    yield


app = FastAPI(title="Language Coach Bot", lifespan=lifespan)

app.include_router(webhook.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "service": "language-coach-bot"}
