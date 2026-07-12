"""
Сервис языкового коуча.

На Этапе 2 история диалога читается из PostgreSQL через memory.py
"""

import logging

from groq import AsyncGroq
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services import memory
from app.services.user_service import get_or_create_user

logger = logging.getLogger("coach")

_groq_client = AsyncGroq(api_key=settings.groq_api_key)

SYSTEM_PROMPT = """You are Alex, a friendly and encouraging English language coach for beginners (A1-A2 level).

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
- Remember: your goal is to make the student comfortable speaking English, not to lecture them

IMPORTANT: Keep every response under 100 words. WhatsApp conversations should feel natural, not like a textbook."""


async def get_coach_response(
    session: AsyncSession, phone: str, user_message: str
) -> str:
    """
    Принимает сессию БД, номер телефона и сообщение пользователя.
    Возвращает ответ коуча, сохраняя оба сообщения в БД.
    """
    # Убеждаемся что ученик существует в БД
    await get_or_create_user(session, phone)

    # Сохраняем сообщение пользователя
    await memory.add_message(session, phone, "user", user_message)

    # Загружаем историю из БД
    history = await memory.get_history(session, phone)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        *history,
    ]

    try:
        response = await _groq_client.chat.completions.create(
            model=settings.groq_model,
            messages=messages,
            max_tokens=200,
            temperature=0.7,
        )

        assistant_message = response.choices[0].message.content

        # Сохраняем ответ коуча в БД
        await memory.add_message(session, phone, "assistant", assistant_message)

        logger.info("Coach responded to %s: %s chars", phone, len(assistant_message))
        return assistant_message

    except Exception as exc:
        logger.error("Groq API error for %s: %s", phone, exc)
        return "Sorry, I'm having a little trouble right now. Please try again in a moment! 🙏"
