"""
Сервис для работы с профилем ученика.

На Этапе 4 добавлено обновление уровня на основе прогресса:
- Коуч анализирует качество ответов
- При достаточном прогрессе уровень повышается A1 → A2
"""

import logging

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message, User

logger = logging.getLogger("user_service")

# Сколько сообщений нужно отправить чтобы проверить прогресс
PROGRESS_CHECK_INTERVAL = 20


async def get_or_create_user(session: AsyncSession, phone: str) -> User:
    """Возвращает существующего ученика или создаёт нового."""
    result = await session.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(phone=phone, level="A1")
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info("New user created: %s", phone)

    return user


async def check_and_update_level(
    session: AsyncSession, phone: str, coach_assessment: str
) -> bool:
    """
    Проверяет нужно ли повысить уровень ученика.
    Возвращает True если уровень был повышен.

    Логика:
    - Каждые PROGRESS_CHECK_INTERVAL сообщений от пользователя
    - Коуч включает в ответ специальный маркер [LEVEL_UP] если видит прогресс
    - Мы ищем этот маркер и обновляем уровень
    """
    if "[LEVEL_UP]" not in coach_assessment:
        return False

    result = await session.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()

    if not user or user.level != "A1":
        return False

    user.level = "A2"
    await session.commit()
    logger.info("User %s leveled up to A2!", phone)
    return True


async def should_check_progress(session: AsyncSession, phone: str) -> bool:
    """Проверяет пора ли оценить прогресс ученика."""
    result = await session.execute(
        select(func.count(Message.id)).where(
            Message.phone == phone,
            Message.role == "user",
        )
    )
    count = result.scalar() or 0
    return count > 0 and count % PROGRESS_CHECK_INTERVAL == 0
