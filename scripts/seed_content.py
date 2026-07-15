"""
Скрипт для заполнения таблицы content_items начальными данными.

Запускается ОДИН РАЗ вручную:
  python scripts/seed_content.py

Безопасен для повторного запуска — проверяет наличие записей перед вставкой.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import AsyncSessionLocal, engine, init_db
from app.db.models import ContentItem
from sqlalchemy import select


CONTENT = [
    # ── Курсы от пользователя (Stepik) ──────────────────────────────────────
    {
        "title": "A1-A2 Level English for Beginners",
        "url": "https://stepik.org/course/232719",
        "type": "course",
        "level": "A1-A2",
        "topic": "general",
        "description": "Полный курс для начинающих на Stepik. Охватывает базовую грамматику, словарный запас и разговорные навыки. Бесплатно.",
    },
    {
        "title": "Грамматика английского для начинающих (2026)",
        "url": "https://stepik.org/course/94175",
        "type": "course",
        "level": "A1-A2",
        "topic": "grammar",
        "description": "Обновлённый курс грамматики на Stepik. Идеален для понимания базовых правил английского языка. Бесплатно.",
    },
    {
        "title": "Hear 'Em All — развиваем понимание на слух",
        "url": "https://stepik.org/course/123309",
        "type": "course",
        "level": "A1-A2",
        "topic": "listening",
        "description": "Курс на Stepik для развития навыков аудирования. Упражнения на понимание живой английской речи. Бесплатно.",
    },
    {
        "title": "English AI — учи английский с помощью ИИ",
        "url": "https://stepik.org/course/229520",
        "type": "course",
        "level": "A1",
        "topic": "general",
        "description": "Инновационный курс на Stepik с AI-поддержкой. Персонализированное обучение для начинающих. Бесплатно.",
    },
    {
        "title": "English for Computer Science: Введение",
        "url": "https://stepik.org/course/266667",
        "type": "course",
        "level": "A1-A2",
        "topic": "it-english",
        "description": "IT-английский для разработчиков на Stepik. Базовая техническая лексика и термины. Бесплатно.",
    },
    {
        "title": "Английский язык для IT-специалистов",
        "url": "https://stepik.org/course/226887",
        "type": "course",
        "level": "A1-A2",
        "topic": "it-english",
        "description": "Профессиональный английский для IT на Stepik. Словарный запас и фразы для работы в tech-среде. Бесплатно.",
    },
    {
        "title": "IT Английский для митингов",
        "url": "https://stepik.org/course/220073",
        "type": "course",
        "level": "A2",
        "topic": "speaking",
        "description": "Специализированный курс на Stepik: как описывать прогресс на стендапах и митингах по-английски. Бесплатно.",
    },
    {
        "title": "IELTS for Free",
        "url": "https://www.ieltsforfree.com/",
        "type": "website",
        "level": "A2",
        "topic": "general",
        "description": "Бесплатные материалы для подготовки к IELTS. Практика всех навыков: чтение, письмо, аудирование, говорение.",
    },
    {
        "title": "Saylor Academy — Free English Courses",
        "url": "https://www.saylor.org/CourseCatalog",
        "type": "website",
        "level": "A1-A2",
        "topic": "general",
        "description": "Бесплатные академические курсы английского. Структурированное обучение с сертификатами. Без регистрации.",
    },
    # ── Дополнительные проверенные ресурсы ──────────────────────────────────
    {
        "title": "BBC Learning English — Elementary",
        "url": "https://www.bbc.co.uk/learningenglish/english/features/6-minute-english",
        "type": "podcast",
        "level": "A2",
        "topic": "listening",
        "description": "6-минутные подкасты BBC на реальные темы. Транскрипты прилагаются. Отлично для развития аудирования.",
    },
    {
        "title": "Duolingo English",
        "url": "https://www.duolingo.com/",
        "type": "website",
        "level": "A1",
        "topic": "vocabulary",
        "description": "Самое популярное приложение для изучения языка. Игровой формат, 5-10 минут в день. Бесплатная версия очень полная.",
    },
    {
        "title": "British Council — LearnEnglish Beginners",
        "url": "https://learnenglish.britishcouncil.org/english-levels/a1-english",
        "type": "website",
        "level": "A1",
        "topic": "general",
        "description": "Официальные материалы British Council для уровня A1. Грамматика, словарь, аудио, видео. Полностью бесплатно.",
    },
    {
        "title": "ESL Fast — Elementary Reading",
        "url": "https://www.eslfast.com/eslfast/",
        "type": "website",
        "level": "A1-A2",
        "topic": "reading",
        "description": "Короткие простые тексты для начинающих с аудио. Идеально для параллельного чтения и аудирования.",
    },
    {
        "title": "Simple English Wikipedia",
        "url": "https://simple.wikipedia.org/",
        "type": "website",
        "level": "A2",
        "topic": "reading",
        "description": "Wikipedia на простом английском (Basic English). Читай статьи на любые темы — язык специально упрощён для A1-A2.",
    },
    {
        "title": "English Grammar in Use (Cambridge) — Online",
        "url": "https://www.cambridge.org/elt/blog/2019/08/27/free-grammar-exercises/",
        "type": "exercise",
        "level": "A1-A2",
        "topic": "grammar",
        "description": "Бесплатные грамматические упражнения от Cambridge. Основаны на классическом учебнике Murphy.",
    },
]


async def seed():
    await init_db()

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(ContentItem))
        existing = result.scalars().all()

        if existing:
            print(f"Content already seeded: {len(existing)} items found. Skipping.")
            return

        for item in CONTENT:
            session.add(ContentItem(**item))

        await session.commit()
        print(f"Successfully seeded {len(CONTENT)} content items.")


if __name__ == "__main__":
    asyncio.run(seed())
