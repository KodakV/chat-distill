import asyncio
import logging
from typing import List

from backend.db.models.messages import Messages
from backend.db.storages.chat_buffer_storage import ChatBufferStorage
from backend.db.storages.message_storage import MessageStorage
from backend.db.storages.topic_storage import TopicStorage
from backend.db.storages.topic_message_storage import TopicMessageStorage
from backend.db.storages.message_embedding_storage import MessageEmbeddingStorage

from backend.core.services.llm.embedding_service import EmbeddingService
from backend.core.services.llm.topic_matching_service import TopicMatchingService
from backend.core.services.llm.summarization_service import SummarizationService
from backend.core.services.llm.topic_extraction_service import TopicExtractService
from backend.core.services.llm.batch_segmentation_service import BatchSegmentationService
from backend.core.services.llm.topic_importance_service import TopicImportanceService

logger = logging.getLogger(__name__)


class ProcessChatBlockPipeline:

    def __init__(
        self,
        chat_buffer_storage: ChatBufferStorage,
        message_storage: MessageStorage,
        topic_storage: TopicStorage,
        topic_message_storage: TopicMessageStorage,
        message_embedding_storage: MessageEmbeddingStorage,
        embedding_service: EmbeddingService,
        topic_matching_service: TopicMatchingService,
        summarization_service: SummarizationService,
        topic_extraction_service: TopicExtractService,
        batch_segmentation_service: BatchSegmentationService,
        topic_importance_service: TopicImportanceService,
        min_topic_importance: int = 6,
        match_candidate_threshold: float = 0.82,
        match_high_confidence_threshold: float = 0.92,
    ):
        self.chat_buffer_storage = chat_buffer_storage
        self.message_storage = message_storage
        self.topic_storage = topic_storage
        self.topic_message_storage = topic_message_storage
        self.message_embedding_storage = message_embedding_storage
        self.embedding_service = embedding_service
        self.topic_matching_service = topic_matching_service
        self.summarization_service = summarization_service
        self.topic_extraction_service = topic_extraction_service
        self.batch_segmentation_service = batch_segmentation_service
        self.topic_importance_service = topic_importance_service
        self.min_topic_importance = min_topic_importance
        self.match_candidate_threshold = match_candidate_threshold
        self.match_high_confidence_threshold = match_high_confidence_threshold

    async def run(self, chat_id: int, message_thread_id: int | None):
        logger.info("[PIPELINE] Start processing chat_id=%s", chat_id)

        buffer_rows = self.chat_buffer_storage.lock_and_get_block(chat_id, message_thread_id)
        if not buffer_rows:
            logger.info("[PIPELINE] No buffer rows for chat_id=%s", chat_id)
            return

        buffer_ids = [row.id for row in buffer_rows]
        telegram_message_ids = [row.message_id for row in buffer_rows]

        logger.info("[PIPELINE] Locked buffer rows count=%s ids=%s", len(buffer_rows), buffer_ids)

        try:
            messages = self.message_storage.get_by_chat_and_message_ids(
                chat_id,
                telegram_message_ids,
            )

            if not messages:
                logger.info("[PIPELINE] No messages found, releasing locks")
                self.chat_buffer_storage.release_locks(buffer_ids)
                return

            logger.info("[PIPELINE] Loaded messages count=%s", len(messages))

            segmented_groups = await self._batch_segmentation(messages)
            logger.info("[SEGMENTATION] Groups count=%s", len(segmented_groups))

            for idx, group in enumerate(segmented_groups, start=1):
                logger.info("[SEGMENTATION] Processing group #%s size=%s", idx, len(group))
                await self._process_group(chat_id, group, message_thread_id)

            self.chat_buffer_storage.mark_processed(buffer_ids)
            logger.info("[PIPELINE] Marked processed buffer_ids=%s", buffer_ids)

            self.chat_buffer_storage.cleanup_processed(chat_id, message_thread_id)
            logger.info("[PIPELINE] Cleanup processed for chat_id=%s", chat_id)

        except Exception:
            logger.exception("[PIPELINE] Exception occurred")
            self.chat_buffer_storage.release_locks(buffer_ids)
            raise

    async def _process_group(self, chat_id: int, messages: List[Messages], message_thread_id):
        if not messages:
            logger.info("[GROUP] Empty group skipped")
            return

        internal_message_ids = [m.id for m in messages]
        logger.info("[GROUP] Start group processing chat_id=%s message_ids=%s", chat_id, internal_message_ids)

        reply_message_ids = [m.reply_to_message for m in messages if m.reply_to_message]
        reply_messages = []
        if reply_message_ids:
            reply_messages = self.message_storage.get_by_chat_and_message_ids(
                chat_id,
                reply_message_ids,
            )

        text = self._format_block_for_llm(messages, reply_messages)
        if not text:
            logger.info("[GROUP] Empty formatted text, skipping group")
            return

        importance = await self.topic_importance_service.evaluate(text)
        logger.info("[GROUP] Importance score=%s (min=%s)", importance, self.min_topic_importance)
        if importance < self.min_topic_importance:
            logger.info("[GROUP] Low importance, skipping group")
            return

        logger.info("[EMBEDDING] Generating embedding for group size=%s", len(messages))

        embedding = await self.embedding_service.generate_embedding(
            self._raw_text_for_embedding(messages)
        )
        if not embedding:
            logger.info("[EMBEDDING] Embedding generation failed, skipping group")
            return

        logger.info("[EMBEDDING] Embedding generated successfully")

        await self._store_message_embeddings(chat_id, messages)

        candidate_topics = self.topic_storage.search_similar_recent(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            embedding=embedding,
            threshold=self.match_candidate_threshold,
        )

        logger.info("[MATCHING] Candidate topics found=%s", len(candidate_topics) if candidate_topics else 0)

        if candidate_topics:
            high_confidence = [
                (topic, score)
                for topic, score in candidate_topics
                if score >= self.match_high_confidence_threshold
            ]

            logger.info("[MATCHING] High confidence candidates=%s", len(high_confidence))

            await self._handle_existing_topics(
                chat_id,
                message_thread_id,
                messages,
                internal_message_ids,
                text,
                embedding,
                high_confidence if high_confidence else candidate_topics,
            )
        else:
            logger.info("[MATCHING] No candidates found, creating new topic")
            await self._create_new_topic(
                chat_id,
                message_thread_id,
                messages,
                internal_message_ids,
                text,
                embedding,
            )

    async def _handle_existing_topics(
        self,
        chat_id: int,
        message_thread_id: int | None,
        messages: List[Messages],
        internal_message_ids: List[int],
        text: str,
        embedding: List[float],
        candidate_topics,
    ):
        logger.info("[MATCHING] Running topic matching service")

        match_result = await self.topic_matching_service.match(text, candidate_topics)
        logger.info("[MATCHING] Match result: topic_id=%s is_match=%s", match_result.topic_id, match_result.is_match)

        topic = next(
            (t for t, _ in candidate_topics if t.id == match_result.topic_id),
            None,
        )

        if match_result.is_match and topic:
            logger.info("[MATCHING] Matched existing topic_id=%s", topic.id)

            score = next((s for t, s in candidate_topics if t.id == topic.id), 1.0)

            previous_messages = self.topic_message_storage.get_messages_for_topic(topic.id)
            previous_text = self._format_block_for_llm(previous_messages)

            self.topic_message_storage.assign_messages_bulk(
                chat_id=chat_id,
                topic_id=topic.id,
                message_ids=internal_message_ids,
                similarity_score=score,
            )
            logger.info("[TOPIC] Assigned messages to topic_id=%s", topic.id)

            self.topic_storage.update_topic_embedding_centroid(
                topic_id=topic.id,
                new_message_embedding=embedding,
            )
            logger.info("[TOPIC] Updated centroid for topic_id=%s", topic.id)

            self.topic_storage.increment_message_count(
                topic_id=topic.id,
                increment=len(messages),
            )
            logger.info("[TOPIC] Incremented message count topic_id=%s by %s", topic.id, len(messages))

            text_for_summarization = self._build_resummarize_input(previous_text, text, topic.summary)
            new_summary = await self.summarization_service.resummarize(text_for_summarization)

            self.topic_storage.update_summary(topic_id=topic.id, summary=new_summary)
            logger.info("[SUMMARY] Updated summary topic_id=%s", topic.id)

        else:
            logger.info("[MATCHING] No valid match, creating new topic")
            await self._create_new_topic(
                chat_id,
                message_thread_id,
                messages,
                internal_message_ids,
                text,
                embedding,
            )

    async def _create_new_topic(
        self,
        chat_id: int,
        message_thread_id: int | None,
        messages: List[Messages],
        internal_message_ids: List[int],
        text: str,
        embedding: List[float],
    ):
        logger.info("[TOPIC] Creating new topic")

        title = await self.topic_extraction_service.extract(text)
        summary = await self.summarization_service.summarize(text)

        topic = self.topic_storage.create_topic(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            title=title,
            summary=summary,
            embedding=embedding,
        )
        logger.info("[TOPIC] New topic created topic_id=%s title=%s", topic.id, title)

        self.topic_storage.increment_message_count(
            topic_id=topic.id,
            increment=len(messages) - 1,
        )

        self.topic_message_storage.assign_messages_bulk(
            chat_id=chat_id,
            topic_id=topic.id,
            message_ids=internal_message_ids,
            similarity_score=1.0,
        )
        logger.info("[TOPIC] Assigned messages to new topic_id=%s", topic.id)

    async def _store_message_embeddings(self, chat_id: int, messages: List[Messages]) -> None:
        msgs_with_text = [
            (m, (m.text or m.caption or "").strip())
            for m in messages
        ]
        msgs_with_text = [(m, t) for m, t in msgs_with_text if t]
        if not msgs_with_text:
            return

        results = await asyncio.gather(
            *[self.embedding_service.generate_embedding(t) for _, t in msgs_with_text],
            return_exceptions=True,
        )

        for (msg, _), result in zip(msgs_with_text, results):
            if isinstance(result, Exception) or not result:
                continue
            self.message_embedding_storage.create_embedding(
                chat_id=chat_id,
                message_id=msg.id,
                embedding=result,
            )

    def _build_resummarize_input(
        self,
        previous_text: str,
        new_text: str,
        summary: str | None,
    ) -> str:
        return "\n".join([
            "Previous topic summary:",
            (summary or "").strip() or "None",
            "",
            "Previously discussed messages:",
            (previous_text or "").strip() or "None",
            "",
            "New messages:",
            (new_text or "").strip() or "None",
        ]).strip()

    def _format_block_for_llm(self, messages: List[Messages], reply_messages: List[Messages] = None) -> str:
        if not messages:
            return ""

        messages = sorted(messages, key=lambda m: m.message_id)
        id_to_index = {m.message_id: idx + 1 for idx, m in enumerate(messages)}

        all_known = list(messages) + list(reply_messages or [])
        message_id_to_author = {
            m.message_id: (m.username or str(m.user_id) or "unknown")
            for m in all_known
        }

        lines: List[str] = ["Discussion block:\n"]

        for idx, message in enumerate(messages, start=1):
            text = (message.text or message.caption or "").strip()
            if not text or len(text) < 3:
                continue

            author = message.username or message.user_id or "unknown"
            parts = [f"[{idx}] (user={author})"]

            forward_author = self.summarization_service._extract_forward_author(message)
            if forward_author:
                parts.append(f"(forwarded from {forward_author})")

            reply_to_id = message.reply_to_message
            if reply_to_id and reply_to_id in id_to_index:
                reply_author = message_id_to_author.get(reply_to_id)
                if reply_author:
                    parts.append(f"(reply to [{id_to_index[reply_to_id]}] by {reply_author})")
                else:
                    parts.append(f"(reply to [{id_to_index[reply_to_id]}])")

            parts.append(f"Text: {text}")
            lines.append("\n".join(parts))
            lines.append("")

        return "\n".join(lines).strip()

    def _raw_text_for_embedding(self, messages: List[Messages]) -> str:
        return " ".join(
            (m.text or m.caption or "").strip()
            for m in messages
            if (m.text or m.caption or "").strip()
        )

    async def _batch_segmentation(self, messages: List[Messages]) -> List[List[Messages]]:
        logger.info("[SEGMENTATION] Starting segmentation for %s messages", len(messages))

        id_groups = await self.batch_segmentation_service.segment(messages)
        logger.info("[SEGMENTATION] Raw id groups: %s", id_groups)

        id_to_message = {m.id: m for m in messages}
        result: List[List[Messages]] = []

        for group in id_groups:
            group_messages = [
                id_to_message[msg_id]
                for msg_id in group
                if msg_id in id_to_message
            ]
            if group_messages:
                result.append(group_messages)

        logger.info("[SEGMENTATION] Final groups count=%s", len(result))

        if not result:
            logger.info("[SEGMENTATION] No valid groups, returning single group")
            return [messages]

        return result
