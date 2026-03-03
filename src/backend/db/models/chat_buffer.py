from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKeyConstraint,
    Index,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class ChatBuffer(Base):
    __tablename__ = "chat_buffer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    message_thread_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)

    message_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )

    processed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    locked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["chat_id", "message_id"],
            ["messages.chat_id", "messages.message_id"],
            ondelete="CASCADE",
        ),
        Index("ix_chat_buffer_chat_processed", "chat_id", "processed"),
        Index("ix_chat_buffer_chat_locked", "chat_id", "locked"),
        Index("ix_chat_buffer_message_thread", "chat_id", "message_thread_id")
    )