from functools import lru_cache

from config.base import Settings


class BackendSettings(Settings):

    database_url: str
    redis_url: str
    celery_broker_url: str
    celery_result_backend: str

    backend_api_key: str
    bot_token: str

    buffer_drain_interval_seconds: int

    merge_topics_interval_minutes: int
    merge_topics_lookback_hours: int
    merge_similarity_threshold: float

    split_topics_interval_minutes: int
    split_topics_lookback_hours: int
    split_topics_min_messages: int

    match_candidate_threshold: float
    match_high_confidence_threshold: float

    topic_min_importance: int


@lru_cache
def get_backend_settings() -> BackendSettings:
    return BackendSettings()
