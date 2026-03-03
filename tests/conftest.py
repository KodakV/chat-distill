"""
Shared test utilities and fixtures.
"""
import os
from types import SimpleNamespace


_DUMMY_ENV = {
    "DATABASE_URL": "postgresql+psycopg://test:test@localhost/test",
    "REDIS_URL": "redis://localhost:6379/0",
    "CELERY_BROKER_URL": "redis://localhost:6379/0",
    "CELERY_RESULT_BACKEND": "redis://localhost:6379/0",
    "BACKEND_API_KEY": "test-key",
    "BOT_TOKEN": "123456:test_token",
    "BUFFER_DRAIN_INTERVAL_SECONDS": "120",
    "MERGE_TOPICS_INTERVAL_MINUTES": "5",
    "MERGE_TOPICS_LOOKBACK_HOURS": "24",
    "MERGE_SIMILARITY_THRESHOLD": "0.90",
    "SPLIT_TOPICS_INTERVAL_MINUTES": "5",
    "SPLIT_TOPICS_LOOKBACK_HOURS": "24",
    "SPLIT_TOPICS_MIN_MESSAGES": "20",
    "MATCH_CANDIDATE_THRESHOLD": "0.82",
    "MATCH_HIGH_CONFIDENCE_THRESHOLD": "0.92",
    "TOPIC_MIN_IMPORTANCE": "6",
    "LOCAL_LLM_BASE_URL": "http://localhost:8001/v1",
    "LOCAL_LLM_API_KEY": "dummy",
    "LOCAL_LLM_MODEL": "test-model",
    "PROMPT_LANGUAGE": "ru",
    "EMBEDDING_BASE_URL": "http://localhost:8002",
    "EMBEDDING_API_KEY": "dummy",
    "EMBEDDING_MODEL": "nomic-embed-text",
}
for key, value in _DUMMY_ENV.items():
    os.environ.setdefault(key, value)


def make_message(
    *,
    id: int = 1,
    message_id: int = 1,
    text: str | None = None,
    caption: str | None = None,
    username: str | None = None,
    user_id: int | None = None,
    raw_payload: dict | None = None,
    forward_from_user_id: int | None = None,
    reply_to_message: int | None = None,
) -> SimpleNamespace:
    """Return a lightweight stand-in for a Messages ORM object."""
    return SimpleNamespace(
        id=id,
        message_id=message_id,
        text=text,
        caption=caption,
        username=username,
        user_id=user_id,
        raw_payload=raw_payload or {},
        forward_from_user_id=forward_from_user_id,
        reply_to_message=reply_to_message,
    )
