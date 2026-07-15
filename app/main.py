from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import webhook


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.db.database import AsyncSessionLocal, init_db
    from app.db.models import ContentItem
    from sqlalchemy import select

    await init_db()

    # Автосидинг контента при первом запуске
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ContentItem).limit(1))
        if result.scalar_one_or_none() is None:
            from scripts.seed_content import CONTENT
            for item in CONTENT:
                session.add(ContentItem(**item))
            await session.commit()
            print(f"Successfully seeded {len(CONTENT)} content items.")

    yield


app = FastAPI(title="Language Coach Bot", lifespan=lifespan)
app.include_router(webhook.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "service": "language-coach-bot"}
