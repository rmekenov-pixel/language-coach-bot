"""
Скрипт для заполнения таблицы content_items начальными данными.
Безопасен для повторного запуска — проверяет наличие записей перед вставкой.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import AsyncSessionLocal, init_db
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
        "description": "Полный курс для начинающих на Stepik. Базовая грамматика, словарный запас и разговорные навыки. Бесплатно.",
    },
    {
        "title": "Грамматика английского для начинающих (2026)",
        "url": "https://stepik.org/course/94175",
        "type": "course",
        "level": "A1-A2",
        "topic": "grammar",
        "description": "Обновлённый курс грамматики на Stepik. Базовые правила английского языка. Бесплатно.",
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
        "description": "Курс на Stepik с AI-поддержкой. Персонализированное обучение для начинающих. Бесплатно.",
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
        "description": "Профессиональный английский для IT на Stepik. Словарный запас для работы в tech-среде. Бесплатно.",
    },
    {
        "title": "IT Английский для митингов",
        "url": "https://stepik.org/course/220073",
        "type": "course",
        "level": "A2",
        "topic": "speaking",
        "description": "Как описывать прогресс на стендапах и митингах по-английски. Бесплатно.",
    },
    {
        "title": "IELTS for Free",
        "url": "https://www.ieltsforfree.com/",
        "type": "website",
        "level": "A2",
        "topic": "general",
        "description": "Бесплатные материалы для подготовки к IELTS. Практика всех навыков.",
    },
    {
        "title": "Saylor Academy — Free English Courses",
        "url": "https://www.saylor.org/CourseCatalog",
        "type": "website",
        "level": "A1-A2",
        "topic": "general",
        "description": "Бесплатные академические курсы английского с сертификатами.",
    },
    {
        "title": "BBC Learning English — 6 Minute English",
        "url": "https://www.bbc.co.uk/learningenglish/english/features/6-minute-english",
        "type": "podcast",
        "level": "A2",
        "topic": "listening",
        "description": "6-минутные подкасты BBC на реальные темы с транскриптами. Отлично для аудирования.",
    },
    {
        "title": "Duolingo English",
        "url": "https://www.duolingo.com/",
        "type": "website",
        "level": "A1",
        "topic": "vocabulary",
        "description": "Самое популярное приложение для изучения языка. Игровой формат, 5-10 минут в день.",
    },
    {
        "title": "British Council — LearnEnglish A1",
        "url": "https://learnenglish.britishcouncil.org/english-levels/a1-english",
        "type": "website",
        "level": "A1",
        "topic": "general",
        "description": "Официальные материалы British Council для уровня A1. Грамматика, словарь, аудио, видео.",
    },
    {
        "title": "ESL Fast — Elementary Reading",
        "url": "https://www.eslfast.com/eslfast/",
        "type": "website",
        "level": "A1-A2",
        "topic": "reading",
        "description": "Короткие простые тексты с аудио для начинающих. Идеально для чтения и аудирования.",
    },
    {
        "title": "Simple English Wikipedia",
        "url": "https://simple.wikipedia.org/",
        "type": "website",
        "level": "A2",
        "topic": "reading",
        "description": "Wikipedia на простом английском. Читай статьи на любые темы — язык специально упрощён.",
    },
    {
        "title": "Perfect English Grammar",
        "url": "https://www.perfect-english-grammar.com/",
        "type": "website",
        "level": "A1-A2",
        "topic": "grammar",
        "description": "Лучший бесплатный грамматический сайт. Объяснения + упражнения для всех уровней.",
    },
    # ── 7 новых курсов ───────────────────────────────────────────────────────
    {
        "title": "EnglishClass101",
        "url": "https://www.englishclass101.com/",
        "type": "podcast",
        "level": "A1-A2",
        "topic": "general",
        "description": "Структурированные подкасты и видео с транскриптами для начинающих. Один из лучших ресурсов для A1-A2.",
    },
    {
        "title": "Elllo — English Listening Lessons Online",
        "url": "https://www.elllo.org/",
        "type": "website",
        "level": "A1-A2",
        "topic": "listening",
        "description": "Тысячи коротких аудио с носителями английского языка. Бесплатно, с транскриптами и упражнениями.",
    },
    {
        "title": "VOA Learning English",
        "url": "https://learningenglish.voanews.com/",
        "type": "website",
        "level": "A2",
        "topic": "listening",
        "description": "Новости на медленном простом английском от Voice of America. Реальный язык для A2 уровня.",
    },
    {
        "title": "italki Community — Language Partners",
        "url": "https://www.italki.com/community/",
        "type": "website",
        "level": "A2",
        "topic": "speaking",
        "description": "Бесплатный раздел italki для поиска языковых партнёров. Практика разговорного английского с носителями.",
    },
    {
        "title": "Speakable — English Pronunciation",
        "url": "https://www.speakable.com/",
        "type": "exercise",
        "level": "A1-A2",
        "topic": "speaking",
        "description": "Упражнения на произношение с AI-оценкой. Помогает звучать более естественно по-английски.",
    },
    {
        "title": "English Grammar 4U",
        "url": "https://www.english-grammar.at/",
        "type": "exercise",
        "level": "A1-A2",
        "topic": "grammar",
        "description": "Объяснения грамматики + интерактивные упражнения. Простой интерфейс, удобно для самостоятельной практики.",
    },
    {
        "title": "Cambridge English — Free Practice Tests",
        "url": "https://www.cambridgeenglish.org/learning-english/activities-for-learners/",
        "type": "exercise",
        "level": "A1-A2",
        "topic": "general",
        "description": "Бесплатные практические задания от Cambridge. Охватывают все навыки: чтение, письмо, аудирование.",
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
