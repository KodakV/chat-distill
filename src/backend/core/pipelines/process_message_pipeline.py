from __future__ import annotations

import logging

from backend.db.models.messages import Messages
from backend.db.storages.message_storage import MessageStorage
from backend.db.storages.chat_buffer_storage import ChatBufferStorage


logger = logging.getLogger(__name__)


class ProcessMessagePipeline:
    def __init__(self,
                 message_storage: MessageStorage,
                 chat_buffer_storage: ChatBufferStorage):
        self.message_storage = message_storage
        self.chat_buffer_storage = chat_buffer_storage

    def run(self, chat_id: int, message_id: int) -> None:
        message = self.message_storage.get_by_chat_and_message_id(chat_id, message_id)
        if not message or not message.text:
            return
        self.chat_buffer_storage.add(chat_id, message_id, message.message_thread_id)
