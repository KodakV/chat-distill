import logging
from typing import List

from backend.db.models.messages import Messages
from backend.db.models.topics import Topics
from backend.db.storages.topic_message_storage import TopicMessageStorage
from backend.db.storages.topic_storage import TopicStorage
from backend.core.services.llm.embedding_service import EmbeddingService
from backend.core.services.llm.summarization_service import SummarizationService
from backend.core.services.llm.topic_extraction_service import TopicExtractService
from backend.core.services.llm.topic_split_service import TopicSplitService

logger = logging.getLogger(__name__)


class SplitTopicsPipeline:

    MAX_MESSAGES_TO_LLM = 30

    def __init__(
        self,
        topic_storage: TopicStorage,
        topic_message_storage: TopicMessageStorage,
        embedding_service: EmbeddingService,
        summarization_service: SummarizationService,
        topic_extraction_service: TopicExtractService,
        topic_split_service: TopicSplitService,
        min_messages: int = 20,
        hours: int = 24,
    ):
        self.topic_storage = topic_storage
        self.topic_message_storage = topic_message_storage
        self.embedding_service = embedding_service
        self.summarization_service = summarization_service
        self.topic_extraction_service = topic_extraction_service
        self.topic_split_service = topic_split_service
        self.min_messages = min_messages
        self.hours = hours

    async def run(self) -> None:
        logger.info("[SPLIT] Pipeline started")

        pairs = self.topic_storage.get_active_chat_thread_pairs(hours=self.hours)
        logger.info("[SPLIT] Active chat/thread pairs: %s", len(pairs))

        for chat_id, message_thread_id in pairs:
            try:
                await self._process_chat_thread(chat_id, message_thread_id)
            except Exception:
                logger.exception(
                    "[SPLIT] Error processing chat_id=%s thread=%s",
                    chat_id,
                    message_thread_id,
                )

        logger.info("[SPLIT] Pipeline finished")

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

        for topic in topics:
            if (topic.message_count or 0) < self.min_messages:
                continue
            try:
                await self._process_topic(topic, chat_id)
            except Exception:
                logger.exception("[SPLIT] Error processing topic_id=%s", topic.id)

    async def _process_topic(self, topic: Topics, chat_id: int) -> None:
        messages = self.topic_message_storage.get_messages_for_topic(topic.id)
        if len(messages) < self.min_messages:
            return

        sample = messages[-self.MAX_MESSAGES_TO_LLM:]

        logger.info(
            "[SPLIT] topic_id=%s: sending %s/%s messages to LLM",
            topic.id, len(sample), len(messages),
        )

        try:
            result = await self.topic_split_service.should_split(topic, sample)
        except Exception:
            logger.exception("[SPLIT] LLM error for topic_id=%s, skipping", topic.id)
            return

        if not result.should_split:
            logger.info("[SPLIT] topic_id=%s: LLM decided NOT to split", topic.id)
            return

        if not result.groups or len(result.groups) < 2:
            logger.warning(
                "[SPLIT] topic_id=%s: should_split=true but no valid groups returned",
                topic.id,
            )
            return

        clusters = self._resolve_groups(result.groups, sample)
        if not clusters or len(clusters) < 2:
            logger.warning("[SPLIT] topic_id=%s: could not resolve groups from LLM indices", topic.id)
            return

        logger.info(
            "[SPLIT] topic_id=%s: LLM approved split into %s topics",
            topic.id, len(clusters),
        )

        await self._do_split(topic, chat_id, clusters)

    def _resolve_groups(
        self,
        groups: List[List[int]],
        messages: List[Messages],
    ) -> List[List[Messages]] | None:
        """Maps 1-based LLM indices to actual Messages objects. Skips invalid indices."""
        id_map = {idx + 1: m for idx, m in enumerate(messages)}
        clusters = []
        for group in groups:
            cluster = [id_map[i] for i in group if i in id_map]
            if cluster:
                clusters.append(cluster)
        return clusters if len(clusters) >= 2 else None

    async def _do_split(
        self,
        original_topic: Topics,
        chat_id: int,
        clusters: list[list[Messages]],
    ) -> None:
        for idx, cluster_messages in enumerate(clusters):
            if not cluster_messages:
                continue

            cluster_msg_ids = [m.id for m in cluster_messages]
            rendered_text = self.summarization_service._render_messages_for_llm(cluster_messages)
            raw_text = " ".join(
                (m.text or m.caption or "").strip()
                for m in cluster_messages
                if (m.text or m.caption or "").strip()
            )

            try:
                title = await self.topic_extraction_service.extract(rendered_text)
            except Exception:
                logger.exception(
                    "[SPLIT] Title extraction failed for cluster %s topic_id=%s",
                    idx, original_topic.id,
                )
                title = original_topic.title

            try:
                summary = await self.summarization_service.summarize_messages(cluster_messages)
            except Exception:
                logger.exception(
                    "[SPLIT] Summarization failed for cluster %s topic_id=%s",
                    idx, original_topic.id,
                )
                summary = None

            embedding = None
            if raw_text:
                try:
                    embedding = await self.embedding_service.generate_embedding(raw_text)
                except Exception:
                    logger.exception(
                        "[SPLIT] Embedding failed for cluster %s topic_id=%s",
                        idx, original_topic.id,
                    )

            new_topic = self.topic_storage.create_topic(
                chat_id=chat_id,
                message_thread_id=original_topic.message_thread_id,
                title=title,
                summary=summary,
                embedding=embedding,
            )
            self.topic_storage.set_message_count(new_topic.id, len(cluster_messages))

            reassigned = self.topic_message_storage.reassign_specific_messages(
                from_topic_id=original_topic.id,
                to_topic_id=new_topic.id,
                chat_id=chat_id,
                message_ids=cluster_msg_ids,
            )

            logger.info(
                "[SPLIT] Cluster %s → new topic_id=%s title=%r reassigned=%s messages",
                idx, new_topic.id, title, reassigned,
            )

        self.topic_storage.close_topic(original_topic.id)
        logger.info("[SPLIT] Original topic_id=%s closed", original_topic.id)
