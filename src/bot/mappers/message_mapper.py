from aiogram.types import Message
from bot.schemas.messages import MessageRequest


class MessageMapper:
    def to_dto(self, message: Message) -> MessageRequest:
        chat = message.chat
        from_user = message.from_user

        message_thread_id = message.message_thread_id
        is_topic_message = bool(message_thread_id)

        thread_name = None
        if chat.type == "supergroup" and chat.is_forum:
            if message.forum_topic_created:
                thread_name = message.forum_topic_created.name
            elif message.forum_topic_edited and message.forum_topic_edited.name:
                thread_name = message.forum_topic_edited.name
            elif message.reply_to_message and message.reply_to_message.forum_topic_created:
                thread_name = message.reply_to_message.forum_topic_created.name

        entities = None
        if message.entities:
            entities = [e.model_dump() for e in message.entities]

        reply_to_message_id = None
        reply_to_user_id = None
        reply_to_thread_id = None

        if message.reply_to_message:
            reply_to_message_id = message.reply_to_message.message_id
            reply_to_thread_id = message.reply_to_message.message_thread_id
            if message.reply_to_message.from_user:
                reply_to_user_id = message.reply_to_message.from_user.id

        forward_from_user_id = None
        if message.forward_from:
            forward_from_user_id = message.forward_from.id

        return MessageRequest(
            message_id=message.message_id,
            date=message.date,

            text=message.text,
            caption=message.caption,

            reply_to_message=reply_to_message_id,
            reply_to_user_id=reply_to_user_id,
            reply_to_message_thread_id=reply_to_thread_id,

            forward_from_user_id=forward_from_user_id,

            chat_id=chat.id,
            chat_name=chat.title or chat.username or "private",
            chat_type=chat.type,
            is_forum=bool(chat.is_forum) if chat.type == "supergroup" else False,

            user_id=from_user.id if from_user else None,
            username=from_user.username if from_user else None,

            message_thread_id=message_thread_id,
            thread_name=thread_name,
            is_topic_message=is_topic_message,

            entities=entities,
            edited_at=message.edit_date,
            has_media=bool(
                message.photo
                or message.video
                or message.document
                or message.sticker
                or message.audio
            ),

            raw_payload=message.model_dump(mode="json"),
        )