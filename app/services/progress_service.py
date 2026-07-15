"""
Сервис отслеживания прогресса ученика.

Две задачи:
1. Определить тему текущего сообщения (grammar/vocabulary/listening/speaking/general)
   чтобы подобрать релевантные материалы
2. Оценить уровень ученика каждые 10 сообщений и обновить профиль
"""

import logging

from groq import AsyncGroq
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db.models import Message, User

logger = logging.getLogger("progress_service")

_groq_client = AsyncGroq(api_key=settings.groq_api_key)

# Темы для подбора материалов
TOPICS = ["grammar", "vocabulary", "listening", "speaking", "reading", "it-english", "general"]


async def detect_topic(user_message: str) -> str:
    """
    Быстро определяет тему сообщения ученика.
    Использует Groq с минимальным промптом для скорости.
    """
    try:
        response = await _groq_client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Classify this English learner message into ONE topic: "
                        f"grammar, vocabulary, listening, speaking, reading, it-english, general.\n"
                        f"Message: '{user_message}'\n"
                        f"Reply with ONLY the topic word, nothing else."
                    ),
                }
            ],
            max_tokens=10,
            temperature=0.1,
        )
        topic = response.choices[0].message.content.strip().lower()
        return topic if topic in TOPICS else "general"
    except Exception:
        return "general"


async def maybe_update_level(session: AsyncSession, phone: str) -> bool:
    """
    Проверяет количество сообщений ученика.
    Каждые 10 сообщений — оценивает уровень и обновляет профиль если нужно.
    Возвращает True если уровень был повышен.
    """
    # Считаем сообщения ученика
    result = await session.execute(
        select(func.count(Message.id)).where(
            Message.phone == phone,
            Message.role == "user",
        )
    )
    count = result.scalar_one()

    # Оцениваем только каждые 10 сообщений
    if count % 10 != 0 or count == 0:
        return False

    # Получаем профиль ученика
    result = await session.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    if not user or user.level == "B1":  # уже максимальный уровень в нашем MVP
        return False

    # Берём последние 10 сообщений ученика для оценки
    result = await session.execute(
        select(Message)
        .where(Message.phone == phone, Message.role == "user")
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    recent_messages = result.scalars().all()
    messages_text = "\n".join([m.content for m in reversed(recent_messages)])

    try:
        response = await _groq_client.chat.completions.create(
            model=settings.groq_model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        f"Evaluate these 10 messages from an English learner (current level: {user.level}).\n"
                        f"Messages:\n{messages_text}\n\n"
                        f"Should they be promoted to the next level? "
                        f"Current: {user.level}. Next: {'A2' if user.level == 'A1' else 'B1'}.\n"
                        f"Reply with ONLY 'yes' or 'no'."
                    ),
                }
            ],
            max_tokens=5,
            temperature=0.1,
        )

        answer = response.choices[0].message.content.strip().lower()
        if answer == "yes":
            new_level = "A2" if user.level == "A1" else "B1"
            user.level = new_level
            await session.commit()
            logger.info("Level updated for %s: %s → %s", phone, user.level, new_level)
            return True

    except Exception as exc:
        logger.error("Level evaluation error: %s", exc)

    return False


async def get_progress_summary(session: AsyncSession, phone: str) -> str:
    """
    Возвращает текстовое резюме прогресса ученика.
    Вызывается по команде /progress.
    """
    result = await session.execute(select(User).where(User.phone == phone))
    user = result.scalar_one_or_none()
    if not user:
        return "I don't have your profile yet. Send me a message to get started! 😊"

    result = await session.execute(
        select(func.count(Message.id)).where(
            Message.phone == phone,
            Message.role == "user",
        )
    )
    msg_count = result.scalar_one()

    next_level = "A2" if user.level == "A1" else "B1" if user.level == "A2" else "🎓 You're at the top!"
    messages_to_next = 10 - (msg_count % 10) if msg_count % 10 != 0 else 10

    return (
        f"📊 Your progress:\n"
        f"• Current level: {user.level}\n"
        f"• Messages sent: {msg_count}\n"
        f"• Next level check in: {messages_to_next} messages\n"
        f"• Next level: {next_level}\n\n"
        f"Keep it up! You're doing great! 💪"
    )
