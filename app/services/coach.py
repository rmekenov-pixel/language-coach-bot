"""
Сервис языкового коуча — Этап 4.

Новое:
- Определяет тему сообщения и подбирает материалы по теме
- После ответа проверяет нужно ли повысить уровень ученика
- Поддерживает команду /progress
"""

import logging

from groq import AsyncGroq
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services import memory
from app.services.content_service import format_materials_for_prompt, get_materials_for_student
from app.services.progress_service import detect_topic, get_progress_summary, maybe_update_level
from app.services.user_service import get_or_create_user

logger = logging.getLogger("coach")

_groq_client = AsyncGroq(api_key=settings.groq_api_key)

BASE_SYSTEM_PROMPT = """You are Alex, a friendly and encouraging English language coach for beginners (A1-A2 level).

Your student communicates with you via WhatsApp. They are learning English and may make grammar or vocabulary mistakes.

YOUR COMMUNICATION STYLE:
- Always respond in simple, clear English (A1-A2 level vocabulary)
- Keep responses short: 2-4 sentences maximum (WhatsApp messages should be brief)
- Be warm, patient, and encouraging — never make the student feel bad about mistakes
- Use emojis occasionally to make the chat feel friendly 😊

YOUR TEACHING APPROACH:
- If the student makes a grammar or spelling mistake, gently correct it ONCE at the end of your response
- Format corrections like this: "💡 Small tip: instead of '...' try saying '...'"
- Do not correct every single mistake — focus on the most important one
- Praise effort and progress: "Great try!", "Good job!", "You're improving!"
- If the student writes in Russian or Kazakh, respond in English but acknowledge what they said

YOUR ROLE:
- Have natural conversations on everyday topics (greetings, weather, food, hobbies, work)
- Occasionally suggest a simple practice activity: "Can you tell me about your day in English?"
- If the student seems stuck, offer help: "Would you like me to suggest some words?"
- Your goal is to make the student comfortable speaking English, not to lecture them

COMMANDS the student can use:
- /reset — clear conversation history
- /progress — see their learning progress

IMPORTANT: Keep every response under 100 words. WhatsApp conversations should feel natural."""


async def get_coach_response(
    session: AsyncSession, phone: str, user_message: str
) -> str:
    """
    Основная функция коуча — Этап 4:
    1. Определяем тему сообщения
    2. Подбираем материалы по теме и уровню
    3. Генерируем ответ
    4. Проверяем нужно ли повысить уровень
    """
    user = await get_or_create_user(session, phone)

    # Определяем тему сообщения для подбора релевантных материалов
    topic = await detect_topic(user_message)
    logger.info("Detected topic for %s: %s", phone, topic)

    # Загружаем материалы по теме и уровню
    materials = await get_materials_for_student(
        session, level=user.level, topic=topic, limit=3
    )
    materials_text = format_materials_for_prompt(materials)

    # Формируем системный промпт
    system_prompt = BASE_SYSTEM_PROMPT
    if materials_text:
        system_prompt += f"\n\n{materials_text}"

    # Сохраняем сообщение и загружаем историю
    await memory.add_message(session, phone, "user", user_message)
    history = await memory.get_history(session, phone)

    messages = [
        {"role": "system", "content": system_prompt},
        *history,
    ]

    try:
        response = await _groq_client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            max_tokens=250,
            temperature=0.7,
        )

        assistant_message = response.choices[0].message.content
        await memory.add_message(session, phone, "assistant", assistant_message)

        # Проверяем нужно ли повысить уровень (каждые 10 сообщений)
        level_up = await maybe_update_level(session, phone)
        if level_up:
            assistant_message += f"\n\n🎉 Congratulations! You've been promoted to level {user.level}! Keep it up!"

        logger.info("Coach responded to %s (level=%s topic=%s)", phone, user.level, topic)
        return assistant_message

    except Exception as exc:
        logger.error("Groq API error for %s: %s", phone, exc)
        return "Sorry, I'm having a little trouble right now. Please try again in a moment! 🙏"
