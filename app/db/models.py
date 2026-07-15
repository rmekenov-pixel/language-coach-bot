"""
SQLAlchemy модели — описание таблиц в БД.

Две таблицы:
- User: профиль ученика (номер телефона, имя, уровень)
- Message: история сообщений (кто написал, что написал, когда)
"""

from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class User(Base):
    __tablename__ = "users"

    # Номер телефона как первичный ключ — он уникален для каждого ученика
    phone: Mapped[str] = mapped_column(String(20), primary_key=True)

    # Имя заполним позже когда добавим онбординг
    name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Текущий уровень ученика — будем обновлять по мере прогресса
    level: Mapped[str] = mapped_column(String(5), default="A1")

    # Когда ученик впервые написал боту
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Связь с сообщениями (один ученик — много сообщений)
    messages: Mapped[list["Message"]] = relationship(
        back_populates="user",
        order_by="Message.created_at",
        lazy="select",
    )

    def __repr__(self) -> str:
        return f"<User phone={self.phone} level={self.level}>"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Ссылка на ученика
    phone: Mapped[str] = mapped_column(
        String(20), ForeignKey("users.phone", ondelete="CASCADE")
    )

    # "user" или "assistant" — формат совместимый с Groq/OpenAI API
    role: Mapped[str] = mapped_column(String(10))

    # Текст сообщения
    content: Mapped[str] = mapped_column(Text)

    # Время сообщения — используем UTC везде
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # Связь с учеником
    user: Mapped["User"] = relationship(back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message id={self.id} role={self.role} phone={self.phone}>"


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(Text)
    url: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(20))       # website, video, podcast, course, exercise
    level: Mapped[str] = mapped_column(String(10))      # A1, A2, A1-A2, B1
    topic: Mapped[str] = mapped_column(String(50))      # grammar, vocabulary, listening, speaking, reading, it-english
    description: Mapped[str] = mapped_column(Text)      # краткое описание для коуча
    is_active: Mapped[bool] = mapped_column(default=True)

    def __repr__(self) -> str:
        return f"<ContentItem id={self.id} title={self.title[:30]} level={self.level}>"
