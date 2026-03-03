"""
Tests for SummarizationService pure methods:
  - _extract_forward_author  (static, no LLM call)
  - _render_messages_for_llm (instance, no LLM call)
"""
from unittest.mock import MagicMock

from backend.core.services.llm.summarization_service import SummarizationService
from tests.conftest import make_message


def _svc() -> SummarizationService:
    return SummarizationService(runner=MagicMock())


class TestExtractForwardAuthor:

    def test_plain_message_returns_none(self):
        m = make_message(text="hello")
        assert SummarizationService._extract_forward_author(m) is None

    def test_forward_from_username(self):
        m = make_message(raw_payload={"forward_from": {"username": "john_doe"}})
        assert SummarizationService._extract_forward_author(m) == "@john_doe"

    def test_forward_from_full_name(self):
        m = make_message(raw_payload={"forward_from": {"first_name": "John", "last_name": "Doe"}})
        assert SummarizationService._extract_forward_author(m) == "John Doe"

    def test_forward_from_first_name_only(self):
        m = make_message(raw_payload={"forward_from": {"first_name": "John"}})
        assert SummarizationService._extract_forward_author(m) == "John"

    def test_forward_from_id_fallback(self):
        m = make_message(raw_payload={"forward_from": {"id": 99999}})
        assert SummarizationService._extract_forward_author(m) == "99999"

    def test_forward_from_chat_username(self):
        m = make_message(raw_payload={"forward_from_chat": {"username": "mychannel"}})
        assert SummarizationService._extract_forward_author(m) == "@mychannel"

    def test_forward_from_chat_title(self):
        m = make_message(raw_payload={"forward_from_chat": {"title": "My Channel"}})
        assert SummarizationService._extract_forward_author(m) == "My Channel"

    def test_forward_from_chat_no_title_falls_back(self):
        m = make_message(raw_payload={"forward_from_chat": {"type": "channel", "id": 123}})
        assert SummarizationService._extract_forward_author(m) == "канал"

    def test_forward_sender_name(self):
        m = make_message(raw_payload={"forward_sender_name": "Hidden User"})
        assert SummarizationService._extract_forward_author(m) == "Hidden User"

    def test_forward_from_user_id(self):
        m = make_message(forward_from_user_id=42)
        assert SummarizationService._extract_forward_author(m) == "42"

    def test_forward_from_takes_priority_over_sender_name(self):
        m = make_message(raw_payload={
            "forward_from": {"username": "real_author"},
            "forward_sender_name": "Hidden",
        })
        assert SummarizationService._extract_forward_author(m) == "@real_author"


class TestRenderMessagesForLLM:

    def test_empty_list_returns_header_only(self):
        result = _svc()._render_messages_for_llm([])
        assert result == "СООБЩЕНИЯ ДЛЯ АНАЛИЗА:"

    def test_message_with_text_and_username(self):
        m = make_message(text="Hello world", username="alice")
        result = _svc()._render_messages_for_llm([m])
        assert "@alice: Hello world" in result

    def test_message_without_username_uses_fallback(self):
        m = make_message(text="Hello world")
        result = _svc()._render_messages_for_llm([m])
        assert "неизвестный: Hello world" in result

    def test_uses_caption_when_text_is_absent(self):
        m = make_message(caption="Photo caption", username="bob")
        result = _svc()._render_messages_for_llm([m])
        assert "@bob: Photo caption" in result

    def test_message_with_no_content_is_skipped(self):
        m = make_message(username="alice")
        result = _svc()._render_messages_for_llm([m])
        assert "@alice" not in result

    def test_forwarded_message_shows_original_author(self):
        m = make_message(
            text="Forwarded text",
            username="alice",
            raw_payload={"forward_from": {"username": "original_author"}},
        )
        result = _svc()._render_messages_for_llm([m])
        assert "@original_author" in result
        assert "переслал сообщение" in result

    def test_multiple_messages_all_appear(self):
        messages = [
            make_message(id=1, message_id=1, text="First", username="alice"),
            make_message(id=2, message_id=2, text="Second", username="bob"),
        ]
        result = _svc()._render_messages_for_llm(messages)
        assert "@alice: First" in result
        assert "@bob: Second" in result
