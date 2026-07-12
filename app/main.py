from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import webhook


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan — код который выполняется при старте и остановке приложения.
    При старте: создаём таблицы в БД если их нет.
    При остановке: ничего особенного не делаем.
    """
    from app.db.database import init_db
    await init_db()
    yield


app = FastAPI(title="Language Coach Bot", lifespan=lifespan)

app.include_router(webhook.router)


@app.get("/")
async def root() -> dict[str, str]:
    return {"status": "ok", "service": "language-coach-bot"}
