"""
Tests for SplitTopicsPipeline._resolve_groups — maps 1-based LLM indices
to actual Messages objects and validates that at least 2 clusters are produced.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

from backend.core.pipelines.split_topics_pipeline import SplitTopicsPipeline


def _msg(id: int) -> SimpleNamespace:
    return SimpleNamespace(id=id, text="Some text")


def _pipeline() -> SplitTopicsPipeline:
    return SplitTopicsPipeline(
        topic_storage=MagicMock(),
        topic_message_storage=MagicMock(),
        embedding_service=MagicMock(),
        summarization_service=MagicMock(),
        topic_extraction_service=MagicMock(),
        topic_split_service=MagicMock(),
    )


class TestResolveGroups:

    def test_valid_two_groups_returns_both(self):
        messages = [_msg(i) for i in range(1, 6)]
        groups = [[1, 2, 3], [4, 5]]
        result = _pipeline()._resolve_groups(groups, messages)
        assert result is not None
        assert len(result) == 2
        assert len(result[0]) == 3
        assert len(result[1]) == 2

    def test_indices_are_1_based(self):
        messages = [_msg(10), _msg(20), _msg(30)]
        groups = [[1, 2], [3]]
        result = _pipeline()._resolve_groups(groups, messages)
        assert result is not None
        assert result[0][0].id == 10
        assert result[0][1].id == 20
        assert result[1][0].id == 30

    def test_invalid_indices_are_silently_skipped(self):
        messages = [_msg(i) for i in range(1, 4)]
        # second group has out-of-range indices → becomes empty → only 1 valid group
        groups = [[1, 2], [99, 100]]
        result = _pipeline()._resolve_groups(groups, messages)
        assert result is None

    def test_single_group_returns_none(self):
        messages = [_msg(i) for i in range(1, 4)]
        groups = [[1, 2, 3]]
        result = _pipeline()._resolve_groups(groups, messages)
        assert result is None

    def test_empty_groups_returns_none(self):
        messages = [_msg(i) for i in range(1, 4)]
        result = _pipeline()._resolve_groups([], messages)
        assert result is None

    def test_three_groups_all_returned(self):
        messages = [_msg(i) for i in range(1, 7)]
        groups = [[1, 2], [3, 4], [5, 6]]
        result = _pipeline()._resolve_groups(groups, messages)
        assert result is not None
        assert len(result) == 3

    def test_partial_invalid_indices_group_still_included(self):
        messages = [_msg(i) for i in range(1, 4)]
        groups = [[1, 99], [2, 3]]
        result = _pipeline()._resolve_groups(groups, messages)
        assert result is not None
        assert len(result) == 2
        assert len(result[0]) == 1
        assert len(result[1]) == 2
