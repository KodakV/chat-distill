import logging

from backend.core.services.llm.embedding_service import EmbeddingService
from backend.core.services.llm.summarization_service import SummarizationService
from backend.core.services.llm.topic_merge_service import TopicMergeService
from backend.db.storages.topic_message_storage import TopicMessageStorage
from backend.db.storages.topic_storage import TopicStorage

logger = logging.getLogger(__name__)


class MergeTopicsPipeline:

    def __init__(
        self,
        topic_storage: TopicStorage,
        topic_message_storage: TopicMessageStorage,
        embedding_service: EmbeddingService,
        summarization_service: SummarizationService,
        topic_merge_service: TopicMergeService,
        similarity_threshold: float = 0.90,
        hours: int = 24,
    ):
        self.topic_storage = topic_storage
        self.topic_message_storage = topic_message_storage
        self.embedding_service = embedding_service
        self.summarization_service = summarization_service
        self.topic_merge_service = topic_merge_service
        self.similarity_threshold = similarity_threshold
        self.hours = hours

    async def run(self) -> None:
        logger.info("[MERGE] Pipeline started")

        pairs = self.topic_storage.get_active_chat_thread_pairs(hours=self.hours)
        logger.info("[MERGE] Active chat/thread pairs to process: %s", len(pairs))

        for chat_id, message_thread_id in pairs:
            try:
                await self._process_chat_thread(chat_id, message_thread_id)
            except Exception:
                logger.exception(
                    "[MERGE] Error processing chat_id=%s thread=%s",
                    chat_id,
                    message_thread_id,
                )

        logger.info("[MERGE] Pipeline finished")

    async def _process_chat_thread(
        self,
        chat_id: int,
        message_thread_id: int | None,
    ) -> None:
        topics = self.topic_storage.get_recent_active_topics(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            hours=self.hours,
        )

        if len(topics) < 2:
            return

        logger.info(
            "[MERGE] chat_id=%s thread=%s: found %s active topics",
            chat_id,
            message_thread_id,
            len(topics),
        )

        merged_ids: set[int] = set()
        updated_primary_ids: set[int] = set()

        for topic in topics:
            if topic.id in merged_ids or topic.embeddings is None:
                continue

            candidates = self.topic_storage.search_similar_for_merge(
                chat_id=chat_id,
                message_thread_id=message_thread_id,
                embedding=list(topic.embeddings),
                exclude_ids=merged_ids | {topic.id},
                hours=self.hours,
                threshold=self.similarity_threshold,
            )

            for candidate, score in candidates:
                if candidate.id in merged_ids:
                    continue

                logger.info(
                    "[MERGE] Candidate pair: primary=%s secondary=%s score=%.3f",
                    topic.id,
                    candidate.id,
                    score,
                )

                primary_messages = self.topic_message_storage.get_messages_for_topic(topic.id)
                secondary_messages = self.topic_message_storage.get_messages_for_topic(candidate.id)

                try:
                    result = await self.topic_merge_service.should_merge(
                        topic_a=topic,
                        messages_a=primary_messages,
                        topic_b=candidate,
                        messages_b=secondary_messages,
                    )
                except Exception:
                    logger.exception(
                        "[MERGE] LLM error for pair primary=%s secondary=%s, skipping",
                        topic.id,
                        candidate.id,
                    )
                    continue

                if not result.should_merge:
                    logger.info(
                        "[MERGE] LLM decided NOT to merge primary=%s secondary=%s",
                        topic.id,
                        candidate.id,
                    )
                    continue

                logger.info(
                    "[MERGE] LLM approved merge: secondary=%s → primary=%s",
                    candidate.id,
                    topic.id,
                )

                reassigned = self.topic_message_storage.reassign_topic_messages(
                    from_topic_id=candidate.id,
                    to_topic_id=topic.id,
                    chat_id=chat_id,
                )
                logger.info("[MERGE] Reassigned %s messages to primary=%s", reassigned, topic.id)

                self.topic_storage.close_topic(candidate.id)

                merged_ids.add(candidate.id)
                updated_primary_ids.add(topic.id)

        for topic_id in updated_primary_ids:
            await self._rebuild_primary_topic(topic_id)

    async def _rebuild_primary_topic(self, topic_id: int) -> None:
        logger.info("[MERGE] Rebuilding primary topic_id=%s", topic_id)

        all_messages = self.topic_message_storage.get_messages_for_topic(topic_id)

        self.topic_storage.set_message_count(topic_id, len(all_messages))
        logger.info("[MERGE] Updated message_count=%s for topic_id=%s", len(all_messages), topic_id)

        new_summary = await self.summarization_service.summarize_messages(all_messages)
        self.topic_storage.update_summary(topic_id, new_summary)
        logger.info("[MERGE] Updated summary for topic_id=%s", topic_id)

        text_for_embedding = " ".join(
            (m.text or m.caption or "").strip()
            for m in all_messages
            if (m.text or m.caption or "").strip()
        )
        if text_for_embedding:
            new_embedding = await self.embedding_service.generate_embedding(text_for_embedding)
            if new_embedding:
                self.topic_storage.set_embedding(topic_id, new_embedding)
                logger.info("[MERGE] Updated embedding for topic_id=%s", topic_id)
