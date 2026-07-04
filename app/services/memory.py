"""
Простое хранение истории диалога в памяти процесса.

На Этапе 1 история живёт пока жив процесс — при перезапуске сервера
сбрасывается. Это осознанное упрощение: персистентность (PostgreSQL)
добавим на Этапе 2.

Ключ словаря — номер телефона пользователя (строка, например "77022300157").
Значение — список сообщений в формате OpenAI/Groq:
  [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
"""

from collections import defaultdict

# Максимальное количество сообщений в истории на одного пользователя.
# Чем длиннее история — тем больше токенов тратится на каждый запрос.
# 20 сообщений (10 пар вопрос-ответ) — разумный баланс для A1-A2 ученика.
MAX_HISTORY = 20

# Глобальный словарь: phone_number -> list of messages
_conversations: dict[str, list[dict]] = defaultdict(list)


def get_history(phone: str) -> list[dict]:
    """Возвращает историю диалога для пользователя."""
    return _conversations[phone]


def add_message(phone: str, role: str, content: str) -> None:
    """
    Добавляет сообщение в историю и обрезает её если она превышает MAX_HISTORY.
    role: "user" или "assistant"
    """
    _conversations[phone].append({"role": role, "content": content})

    # Если история стала слишком длинной — удаляем старые сообщения с начала.
    # Важно: удаляем парами (user + assistant), чтобы не нарушить чередование ролей.
    while len(_conversations[phone]) > MAX_HISTORY:
        _conversations[phone].pop(0)


def clear_history(phone: str) -> None:
    """Сбрасывает историю диалога для пользователя (например, по команде /reset)."""
    _conversations[phone] = []
