"""
Сервис для работы с каталогом учебных материалов.

Отвечает за:
- Поиск материалов по теме и уровню ученика
- Получение случайных материалов для рекомендации
"""

import logging
import random

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import ContentItem

logger = logging.getLogger("content_service")


async def get_materials_for_student(
    session: AsyncSession,
    level: str = "A1",
    topic: str | None = None,
    limit: int = 3,
) -> list[ContentItem]:
    """
    Возвращает подходящие материалы для ученика.

    Логика подбора:
    1. Если указана тема — ищем по теме + уровню
    2. Если тема не указана — берём случайные материалы для уровня
    3. Всегда возвращаем не более limit штук
    """
    query = select(ContentItem).where(
        ContentItem.is_active == True,
        ContentItem.level.in_([level, f"{level}-A2", "A1-A2"]),
    )

    if topic:
        query = query.where(ContentItem.topic == topic)

    result = await session.execute(query)
    items = result.scalars().all()

    if not items:
        # Если по теме ничего нет — берём любые активные материалы для уровня
        result = await session.execute(
            select(ContentItem).where(
                ContentItem.is_active == True,
                ContentItem.level.in_([level, "A1-A2"]),
            )
        )
        items = result.scalars().all()

    # Возвращаем случайную выборку чтобы не повторяться
    selected = random.sample(list(items), min(limit, len(items)))
    logger.info("Selected %d materials for level=%s topic=%s", len(selected), level, topic)
    return selected


def format_materials_for_prompt(materials: list[ContentItem]) -> str:
    """
    Форматирует материалы для вставки в системный промпт коуча.
    LLM использует эти данные чтобы рекомендовать конкретные ресурсы.
    """
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
        "\nWhen the student asks for resources, or when you think a specific material "
        "would help them, recommend ONE of the above with the exact URL. "
        "Never invent URLs — only use the ones listed above."
    )

    return "\n".join(lines)
