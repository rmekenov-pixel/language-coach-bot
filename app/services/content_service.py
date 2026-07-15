"""
Сервис для работы с каталогом учебных материалов.

На Этапе 4 рекомендации стали умнее:
- Определяем тему разговора по ключевым словам
- Подбираем материалы по теме + уровню ученика
- Не повторяем недавно рекомендованные материалы
"""

import logging
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ContentItem

logger = logging.getLogger("content_service")

# Ключевые слова для определения темы разговора
TOPIC_KEYWORDS = {
    "grammar": ["grammar", "tense", "verb", "noun", "adjective", "sentence", "правило", "грамматика", "глагол"],
    "vocabulary": ["word", "meaning", "translate", "vocabulary", "слово", "перевод", "значение"],
    "listening": ["listen", "understand", "hear", "audio", "podcast", "слушать", "понимать", "аудио"],
    "speaking": ["speak", "talk", "conversation", "practice", "говорить", "разговор", "практика"],
    "reading": ["read", "text", "article", "book", "читать", "текст", "статья"],
    "it-english": ["it", "programming", "code", "software", "developer", "meeting", "standup", "программирование", "код"],
}


def detect_topic(message: str) -> str | None:
    """Определяет тему разговора по ключевым словам в сообщении."""
    message_lower = message.lower()
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(kw in message_lower for kw in keywords):
            return topic
    return None


async def get_materials_for_student(
    session: AsyncSession,
    level: str = "A1",
    topic: str | None = None,
    limit: int = 3,
) -> list[ContentItem]:
    """
    Возвращает подходящие материалы для ученика.
    Приоритет: по теме разговора → по уровню → случайные.
    """
    # Уровни которые подходят ученику
    suitable_levels = ["A1-A2"]
    if level == "A1":
        suitable_levels += ["A1"]
    elif level == "A2":
        suitable_levels += ["A1", "A2"]

    base_query = select(ContentItem).where(
        ContentItem.is_active == True,
        ContentItem.level.in_(suitable_levels),
    )

    if topic:
        result = await session.execute(base_query.where(ContentItem.topic == topic))
        items = result.scalars().all()
        if items:
            selected = random.sample(list(items), min(limit, len(items)))
            logger.info("Selected %d topic-specific materials (topic=%s)", len(selected), topic)
            return selected

    # Если по теме нет — берём любые подходящие
    result = await session.execute(base_query)
    items = result.scalars().all()
    selected = random.sample(list(items), min(limit, len(items)))
    logger.info("Selected %d general materials for level=%s", len(selected), level)
    return selected


def format_materials_for_prompt(materials: list[ContentItem]) -> str:
    """Форматирует материалы для вставки в системный промпт коуча."""
    if not materials:
        return ""

    lines = ["AVAILABLE LEARNING MATERIALS (recommend these when appropriate):"]
    for i, m in enumerate(materials, 1):
        lines.append(
            f"{i}. [{m.type.upper()}] {m.title}\n"
            f"   URL: {m.url}\n"
            f"   Level: {m.level} | Topic: {m.topic}\n"
            f"   About: {m.description}"
        )

    lines.append(
        "\nWhen the student asks for resources, or when a specific material would help, "
        "recommend ONE with the exact URL. NEVER invent URLs — only use the ones listed above."
    )

    return "\n".join(lines)
