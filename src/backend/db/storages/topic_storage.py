from sqlalchemy.orm import Session
from sqlalchemy import func, desc, distinct
from typing import List
from datetime import datetime, timedelta
from backend.db.models.topics import Topics
import logging

logger = logging.getLogger(__name__)


class TopicStorage:
    def __init__(self, db: Session):
        self.db = db

    def create_topic(
        self,
        chat_id: int,
        message_thread_id: int | None,
        title: str | None,
        summary: str | None,
        embedding: List[float] | None,
    ) -> Topics:
        now = datetime.utcnow()

        topic = Topics(
            chat_id=chat_id,
            message_thread_id=message_thread_id,
            title=title,
            summary=summary,
            embeddings=embedding,
            message_count=1,
            status="active",
            created_at=now,
            updated_at=now,
        )

        self.db.add(topic)
        self.db.flush()

        logger.info("Topic created id=%s title=%s", topic.id, title)

        return topic

    def get_topic(self, topic_id: int) -> Topics | None:
        return (
            self.db.query(Topics)
            .filter(Topics.id == topic_id)
            .first()
        )

    def get_active_topics(
            self,
            chat_id: int,
            message_thread_id: int | None = None,
    ) -> List[Topics]:

        query = (
            self.db.query(Topics)
            .filter(
                Topics.chat_id == chat_id,
                Topics.status == "active",
            )
        )

        if message_thread_id is not None:
            query = query.filter(
                Topics.message_thread_id == message_thread_id
            )

        return query.all()

    def get_last_active_topics(
        self,
        chat_id: int,
        message_thread_id: int | None,
        limit: int = 20,
    ) -> List[Topics]:
        return (
            self.db.query(Topics)
            .filter(
                Topics.chat_id == chat_id,
                Topics.message_thread_id == message_thread_id,
                Topics.status == "active",
            )
            .order_by(desc(Topics.updated_at))
            .limit(limit)
            .all()
        )

    def search_similar(
        self,
        chat_id: int,
        message_thread_id: int | None,
        embedding: List[float],
        limit: int = 5,
        threshold: float | None = None,
    ) -> List[tuple[Topics, float]]:

        distance_expr = Topics.embeddings.cosine_distance(embedding)
        similarity_expr = (1 - distance_expr).label("similarity")

        query = (
            self.db.query(
                Topics,
                similarity_expr,
            )
            .filter(
                Topics.chat_id == chat_id,
                Topics.message_thread_id == message_thread_id,
                Topics.status == "active",
                Topics.embeddings.isnot(None),
            )
        )

        if threshold is not None:
            query = query.filter(distance_expr <= (1 - threshold))

        results = (
            query
            .order_by(distance_expr)
            .limit(limit)
            .all()
        )

        logger.info("search_similar found %s topics", len(results))

        return results

    def search_similar_recent(
        self,
        chat_id: int,
        message_thread_id: int | None,
        embedding: List[float],
        hours: int = 4,
        limit: int = 5,
        threshold: float | None = None,
    ) -> List[tuple[Topics, float]]:

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        distance_expr = Topics.embeddings.cosine_distance(embedding)
        similarity_expr = (1 - distance_expr).label("similarity")

        query = (
            self.db.query(
                Topics,
                similarity_expr,
            )
            .filter(
                Topics.chat_id == chat_id,
                Topics.message_thread_id == message_thread_id,
                Topics.status == "active",
                Topics.embeddings.isnot(None),
                Topics.updated_at >= cutoff_time,
                func.date(Topics.created_at) == func.current_date(),
            )
        )

        if threshold is not None:
            query = query.filter(distance_expr <= (1 - threshold))

        results = (
            query
            .order_by(distance_expr)
            .limit(limit)
            .all()
        )

        logger.info("search_similar_recent found %s topics", len(results))

        return results

    def update_topic_embedding_centroid(
            self,
            topic_id: int,
            new_message_embedding: List[float],
    ) -> None:

        topic = self.get_topic(topic_id)
        if not topic:
            logger.warning("update_topic_embedding_centroid: topic not found id=%s", topic_id)
            return

        old_embedding = topic.embeddings
        old_count = topic.message_count or 0

        if old_embedding is None or len(old_embedding) == 0:
            logger.info("No previous embedding, setting new as topic embedding topic_id=%s", topic_id)
            topic.embeddings = new_message_embedding
            topic.updated_at = datetime.utcnow()
            self.db.flush()
            return

        if len(old_embedding) != len(new_message_embedding):
            logger.error(
                "Embedding size mismatch topic_id=%s old=%s new=%s",
                topic_id,
                len(old_embedding),
                len(new_message_embedding),
            )
            return

        new_count = old_count + 1

        updated_embedding = [
            (old_embedding[i] * old_count + new_message_embedding[i]) / new_count
            for i in range(len(old_embedding))
        ]

        topic.embeddings = updated_embedding
        topic.updated_at = datetime.utcnow()
        self.db.flush()

        logger.info(
            "Topic centroid updated topic_id=%s old_count=%s new_count=%s",
            topic_id,
            old_count,
            new_count,
        )

    def increment_message_count(
        self,
        topic_id: int,
        increment: int = 1,
    ) -> int | None:
        topic = self.get_topic(topic_id)
        if not topic:
            return None

        topic.message_count = (topic.message_count or 0) + increment
        topic.updated_at = datetime.utcnow()
        self.db.flush()

        logger.info(
            "Topic message_count incremented topic_id=%s increment=%s new_count=%s",
            topic_id,
            increment,
            topic.message_count,
        )

        return topic.message_count

    def close_topic(self, topic_id: int) -> None:
        topic = self.get_topic(topic_id)
        if topic:
            topic.status = "closed"
            topic.updated_at = datetime.utcnow()
            self.db.flush()
            logger.info("Topic closed topic_id=%s", topic_id)

    def update_summary(
            self,
            topic_id: int,
            summary: str | None,
    ) -> None:
        topic = self.get_topic(topic_id)
        if not topic:
            logger.warning("update_summary: topic not found id=%s", topic_id)
            return

        topic.summary = summary
        topic.updated_at = datetime.utcnow()
        self.db.flush()

        logger.info(
            "Topic summary updated topic_id=%s",
            topic_id,
        )

    def get_recent_active_topics(
        self,
        chat_id: int,
        message_thread_id: int | None,
        hours: int = 24,
    ) -> List[Topics]:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return (
            self.db.query(Topics)
            .filter(
                Topics.chat_id == chat_id,
                Topics.message_thread_id == message_thread_id,
                Topics.status == "active",
                Topics.updated_at >= cutoff_time,
            )
            .order_by(desc(Topics.message_count))
            .all()
        )

    def get_active_chat_thread_pairs(
        self,
        hours: int = 24,
    ) -> List[tuple[int, int | None]]:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        rows = (
            self.db.query(
                distinct(Topics.chat_id),
                Topics.message_thread_id,
            )
            .filter(
                Topics.status == "active",
                Topics.updated_at >= cutoff_time,
            )
            .all()
        )
        return [(row[0], row[1]) for row in rows]

    def search_similar_for_merge(
        self,
        chat_id: int,
        message_thread_id: int | None,
        embedding: List[float],
        exclude_ids: set[int],
        hours: int = 24,
        limit: int = 10,
        threshold: float = 0.85,
    ) -> List[tuple[Topics, float]]:
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        distance_expr = Topics.embeddings.cosine_distance(embedding)
        similarity_expr = (1 - distance_expr).label("similarity")

        query = (
            self.db.query(Topics, similarity_expr)
            .filter(
                Topics.chat_id == chat_id,
                Topics.message_thread_id == message_thread_id,
                Topics.status == "active",
                Topics.embeddings.isnot(None),
                Topics.updated_at >= cutoff_time,
                distance_expr <= (1 - threshold),
            )
        )

        if exclude_ids:
            query = query.filter(Topics.id.notin_(exclude_ids))

        results = (
            query
            .order_by(distance_expr)
            .limit(limit)
            .all()
        )

        logger.info(
            "search_similar_for_merge found %s candidates chat_id=%s",
            len(results),
            chat_id,
        )

        return results

    def set_message_count(self, topic_id: int, count: int) -> None:
        topic = self.get_topic(topic_id)
        if not topic:
            return
        topic.message_count = count
        topic.updated_at = datetime.utcnow()
        self.db.flush()
        logger.info("Topic message_count set topic_id=%s count=%s", topic_id, count)

    def set_embedding(self, topic_id: int, embedding: List[float]) -> None:
        topic = self.get_topic(topic_id)
        if not topic:
            return
        topic.embeddings = embedding
        topic.updated_at = datetime.utcnow()
        self.db.flush()
        logger.info("Topic embedding updated topic_id=%s", topic_id)