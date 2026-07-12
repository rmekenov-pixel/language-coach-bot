"""
Сервис для работы с профилем ученика.

Отвечает за:
- Получение или создание профиля ученика при первом контакте
- Обновление уровня (будет использоваться на Этапе 5)
"""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User

logger = logging.getLogger("user_service")


async def get_or_create_user(session: AsyncSession, phone: str) -> User:
    """
    Возвращает существующего ученика или создаёт нового.
    Паттерн get-or-create: безопасен при параллельных запросах.
    """
    result = await session.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(phone=phone, level="A1")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("New user created: %s", phone)
    
    return user
