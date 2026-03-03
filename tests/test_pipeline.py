"""
Tests for ProcessChatBlockPipeline pure methods:
  - _build_resummarize_input
  - _format_block_for_llm
  - _raw_text_for_embedding
"""
from unittest.mock import MagicMock

from backend.core.pipelines.process_chat_block_pipeline import ProcessChatBlockPipeline
from backend.core.services.llm.summarization_service import SummarizationService
from tests.conftest import make_message


def _pipeline() -> ProcessChatBlockPipeline:
    """Create a pipeline with all dependencies mocked out."""
    mock_svc = MagicMock(spec=SummarizationService)
    mock_svc._extract_forward_author.side_effect = SummarizationService._extract_forward_author
    return ProcessChatBlockPipeline(
        chat_buffer_storage=MagicMock(),
        message_storage=MagicMock(),
        topic_storage=MagicMock(),
        topic_message_storage=MagicMock(),
        message_embedding_storage=MagicMock(),
        embedding_service=MagicMock(),
        topic_matching_service=MagicMock(),
        summarization_service=mock_svc,
        topic_extraction_service=MagicMock(),
        batch_segmentation_service=MagicMock(),
        topic_importance_service=MagicMock(),
    )


class TestBuildResummarizeInput:

    def test_contains_all_three_sections(self):
        result = _pipeline()._build_resummarize_input(
            previous_text="old messages",
            new_text="new messages",
            summary="existing summary",
        )
        assert "Previous topic summary:" in result
        assert "existing summary" in result
        assert "Previously discussed messages:" in result
        assert "old messages" in result
        assert "New messages:" in result
        assert "new messages" in result

    def test_none_summary_renders_as_none_label(self):
        result = _pipeline()._build_resummarize_input("prev", "new", None)
        assert "None" in result

    def test_empty_previous_text_renders_as_none_label(self):
        result = _pipeline()._build_resummarize_input("", "new text", "summary")
        assert "None" in result

    def test_empty_new_text_renders_as_none_label(self):
        result = _pipeline()._build_resummarize_input("prev text", "", "summary")
        assert "None" in result


class TestFormatBlockForLLM:

    def test_empty_messages_returns_empty_string(self):
        assert _pipeline()._format_block_for_llm([]) == ""

    def test_block_header_is_present(self):
        m = make_message(text="Hello everyone!", username="alice", message_id=1, id=1)
        result = _pipeline()._format_block_for_llm([m])
        assert "Discussion block:" in result

    def test_normal_message_is_included(self):
        m = make_message(text="Hello everyone!", username="alice", message_id=1, id=1)
        result = _pipeline()._format_block_for_llm([m])
        assert "alice" in result
        assert "Hello everyone!" in result

    def test_very_short_text_is_skipped(self):
        # len("ok") == 2, threshold is < 3
        m = make_message(text="ok", username="alice", message_id=1, id=1)
        result = _pipeline()._format_block_for_llm([m])
        assert "alice" not in result

    def test_forwarded_message_shows_origin(self):
        m = make_message(
            text="Forwarded content here",
            username="alice",
            raw_payload={"forward_from": {"username": "original_author"}},
            message_id=1, id=1,
        )
        result = _pipeline()._format_block_for_llm([m])
        assert "forwarded from @original_author" in result

    def test_reply_shows_back_reference(self):
        m1 = make_message(text="Original message text", username="alice", message_id=1, id=1)
        m2 = make_message(
            text="Replying to your message", username="bob",
            message_id=2, id=2, reply_to_message=1,
        )
        result = _pipeline()._format_block_for_llm([m1, m2])
        assert "reply to" in result

    def test_caption_used_when_no_text(self):
        m = make_message(caption="Photo description", username="alice", message_id=1, id=1)
        result = _pipeline()._format_block_for_llm([m])
        assert "Photo description" in result


class TestRawTextForEmbedding:

    def test_joins_texts_with_space(self):
        messages = [
            make_message(text="Hello", id=1, message_id=1),
            make_message(text="World", id=2, message_id=2),
        ]
        assert _pipeline()._raw_text_for_embedding(messages) == "Hello World"

    def test_uses_caption_when_no_text(self):
        messages = [make_message(caption="Photo caption", id=1, message_id=1)]
        assert _pipeline()._raw_text_for_embedding(messages) == "Photo caption"

    def test_skips_messages_with_no_content(self):
        messages = [
            make_message(text="Hello", id=1, message_id=1),
            make_message(id=2, message_id=2),
            make_message(text="World", id=3, message_id=3),
        ]
        assert _pipeline()._raw_text_for_embedding(messages) == "Hello World"

    def test_returns_empty_string_when_all_empty(self):
        messages = [make_message(id=1, message_id=1)]
        assert _pipeline()._raw_text_for_embedding(messages) == ""
