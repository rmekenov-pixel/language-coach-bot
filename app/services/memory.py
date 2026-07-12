"""
Хранение истории диалога в PostgreSQL.

На Этапе 2 история сохраняется в БД и переживает перезапуски сервера.
Максимум MAX_HISTORY последних сообщений загружается для каждого запроса к LLM.
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message

logger = logging.getLogger("memory")

# Сколько последних сообщений передаём в Groq.
# Чем больше — тем лучше контекст, но дороже по токенам.
MAX_HISTORY = 20


async def get_history(session: AsyncSession, phone: str) -> list[dict]:
    """
    Загружает последние MAX_HISTORY сообщений из БД.
    Возвращает в формате Groq/OpenAI: [{"role": "user", "content": "..."}]
    """
    result = await session.execute(
        select(Message)
        .where(Message.phone == phone)
        .order_by(Message.created_at.desc())
        .limit(MAX_HISTORY)
    )
    messages = result.scalars().all()

    # Разворачиваем — в БД последние сверху, нам нужно хронологически
    return [
        {"role": msg.role, "content": msg.content}
        for msg in reversed(messages)
    ]


async def add_message(
    session: AsyncSession, phone: str, role: str, content: str
) -> None:
    """Сохраняет новое сообщение в БД."""
    message = Message(phone=phone, role=role, content=content)
    session.add(message)
    await session.commit()
    logger.debug("Saved message for %s (role=%s)", phone, role)


async def clear_history(session: AsyncSession, phone: str) -> None:
    """Удаляет всю историю диалога для ученика (команда /reset)."""
    from sqlalchemy import delete
    await session.execute(delete(Message).where(Message.phone == phone))
    await session.commit()
    logger.info("History cleared for %s", phone)
