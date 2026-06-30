from fastapi import FastAPI

from app.routers import webhook

app = FastAPI(title="Language Coach Bot")

app.include_router(webhook.router)


@app.get("/")
async def root() -> dict[str, str]:
    """
    Простой health-check эндпоинт.
    Railway и ты сам можешь использовать его, чтобы убедиться,
    что сервис вообще поднялся и отвечает.
    """
    return {"status": "ok", "service": "language-coach-bot"}
