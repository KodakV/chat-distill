from backend.core.pipelines.merge_topics_pipeline import MergeTopicsPipeline
from backend.core.pipelines.process_chat_block_pipeline import ProcessChatBlockPipeline
from backend.core.pipelines.process_message_pipeline import ProcessMessagePipeline
from backend.core.pipelines.split_topics_pipeline import SplitTopicsPipeline
from backend.core.services.llm.batch_segmentation_service import BatchSegmentationService
from backend.core.services.llm.embedding_service import EmbeddingService
from backend.core.services.llm.summarization_service import SummarizationService
from backend.core.services.llm.topic_extraction_service import TopicExtractService
from backend.core.services.llm.topic_importance_service import TopicImportanceService
from backend.core.services.llm.topic_matching_service import TopicMatchingService
from backend.core.services.llm.topic_merge_service import TopicMergeService
from backend.core.services.llm.topic_split_service import TopicSplitService
from backend.db.storages.chat_buffer_storage import ChatBufferStorage
from backend.db.storages.message_embedding_storage import MessageEmbeddingStorage
from backend.db.storages.message_storage import MessageStorage
from backend.db.storages.topic_message_storage import TopicMessageStorage
from backend.db.storages.topic_storage import TopicStorage
from config.backend_settings import get_backend_settings
from llm.clients.embedding_client import EmbeddingClient
from llm.clients.llm_client import LLMClient
from llm.runner.embedding_runner import EmbeddingRunner
from llm.runner.llm_runner import LLMRunner


def _make_llm_runner() -> LLMRunner:
    return LLMRunner(client=LLMClient())


def _make_embedding_runner() -> EmbeddingRunner:
    return EmbeddingRunner(EmbeddingClient())


def build_process_message_pipeline(db) -> ProcessMessagePipeline:
    return ProcessMessagePipeline(
        message_storage=MessageStorage(db),
        chat_buffer_storage=ChatBufferStorage(db),
    )


def build_process_chat_block_pipeline(db) -> ProcessChatBlockPipeline:
    settings = get_backend_settings()

    llm_runner = _make_llm_runner()
    embedding_service = EmbeddingService(_make_embedding_runner())

    return ProcessChatBlockPipeline(
        chat_buffer_storage=ChatBufferStorage(db),
        message_storage=MessageStorage(db),
        topic_storage=TopicStorage(db),
        topic_message_storage=TopicMessageStorage(db),
        message_embedding_storage=MessageEmbeddingStorage(db),
        embedding_service=embedding_service,
        topic_matching_service=TopicMatchingService(llm_runner),
        summarization_service=SummarizationService(llm_runner),
        topic_extraction_service=TopicExtractService(llm_runner),
        batch_segmentation_service=BatchSegmentationService(llm_runner),
        topic_importance_service=TopicImportanceService(llm_runner),
        min_topic_importance=settings.topic_min_importance,
        match_candidate_threshold=settings.match_candidate_threshold,
        match_high_confidence_threshold=settings.match_high_confidence_threshold,
    )


def build_merge_topics_pipeline(db) -> MergeTopicsPipeline:
    settings = get_backend_settings()

    llm_runner = _make_llm_runner()
    embedding_service = EmbeddingService(_make_embedding_runner())

    return MergeTopicsPipeline(
        topic_storage=TopicStorage(db),
        topic_message_storage=TopicMessageStorage(db),
        embedding_service=embedding_service,
        summarization_service=SummarizationService(llm_runner),
        topic_merge_service=TopicMergeService(llm_runner),
        similarity_threshold=settings.merge_similarity_threshold,
        hours=settings.merge_topics_lookback_hours,
    )


def build_split_topics_pipeline(db) -> SplitTopicsPipeline:
    settings = get_backend_settings()

    llm_runner = _make_llm_runner()
    embedding_service = EmbeddingService(_make_embedding_runner())

    return SplitTopicsPipeline(
        topic_storage=TopicStorage(db),
        topic_message_storage=TopicMessageStorage(db),
        embedding_service=embedding_service,
        summarization_service=SummarizationService(llm_runner),
        topic_extraction_service=TopicExtractService(llm_runner),
        topic_split_service=TopicSplitService(llm_runner),
        min_messages=settings.split_topics_min_messages,
        hours=settings.split_topics_lookback_hours,
    )
