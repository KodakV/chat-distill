from typing import List

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from backend.db.models.chat_buffer import ChatBuffer


class ChatBufferStorage:
    def __init__(self, db: Session):
        self.db = db

    def add(self, chat_id: int, message_id: int, message_thread_id: int) -> ChatBuffer:
        record = ChatBuffer(
            chat_id=chat_id,
            message_id=message_id,
            message_thread_id=message_thread_id,
            processed=False,
            locked=False,
        )
        self.db.add(record)
        return record

    def count_unprocessed(self, chat_id: int, message_thread_id: int | None) -> int:
        return (
            self.db.query(ChatBuffer)
            .filter(
                ChatBuffer.chat_id == chat_id,
                ChatBuffer.message_thread_id == message_thread_id,
                ChatBuffer.processed.is_(False),
                ChatBuffer.locked.is_(False),
            )
            .count()
        )

    def is_ready(self, chat_id: int, message_thread_id: int | None,  limit: int = 20) -> bool:
        return self.count_unprocessed(chat_id, message_thread_id) >= limit

    def get_unprocessed_ids(self, chat_id: int, message_thread_id: int,  limit: int) -> List[int]:
        rows = (
            self.db.query(ChatBuffer)
            .filter(
                ChatBuffer.chat_id == chat_id,
                ChatBuffer.message_thread_id == message_thread_id,
                ChatBuffer.processed.is_(False),
                ChatBuffer.locked.is_(False),
            )
            .order_by(ChatBuffer.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
            .all()
        )
        return [row.id for row in rows]

    def lock_and_get_block(self, chat_id: int, message_thread_id: int,  limit: int = 20) -> List[ChatBuffer]:
        rows = (
            self.db.query(ChatBuffer)
            .filter(
                ChatBuffer.chat_id == chat_id,
                ChatBuffer.message_thread_id == message_thread_id,
                ChatBuffer.processed.is_(False),
                ChatBuffer.locked.is_(False),
            )
            .order_by(ChatBuffer.created_at.asc())
            .limit(limit)
            .with_for_update(skip_locked=True)
            .all()
        )

        for row in rows:
            row.locked = True

        return rows

    def mark_processed(self, buffer_ids: List[int]) -> None:
        if not buffer_ids:
            return

        (
            self.db.query(ChatBuffer)
            .filter(ChatBuffer.id.in_(buffer_ids))
            .update(
                {
                    ChatBuffer.processed: True,
                    ChatBuffer.locked: False,
                },
                synchronize_session=False,
            )
        )

    def release_locks(self, buffer_ids: List[int]) -> None:
        if not buffer_ids:
            return

        (
            self.db.query(ChatBuffer)
            .filter(ChatBuffer.id.in_(buffer_ids))
            .update(
                {
                    ChatBuffer.locked: False,
                },
                synchronize_session=False,
            )
        )

    def get_active_pairs(self) -> list[tuple[int, int | None]]:
        rows = (
            self.db.query(ChatBuffer.chat_id, ChatBuffer.message_thread_id)
            .filter(
                ChatBuffer.processed.is_(False),
                ChatBuffer.locked.is_(False),
            )
            .distinct()
            .all()
        )
        return [(row[0], row[1]) for row in rows]

    def cleanup_processed(self, chat_id: int, message_thread_id: int | None) -> None:
        (
            self.db.query(ChatBuffer)
            .filter(
                ChatBuffer.chat_id == chat_id,
                ChatBuffer.message_thread_id == message_thread_id,
                ChatBuffer.processed.is_(True),
            )
            .delete(synchronize_session=False)
        )