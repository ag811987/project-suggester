"""Tests for WebSearchClient service."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.web_search_client import WebSearchClient, WebSearchResult, _cache_key


class TestWebSearchResult:
    """Test WebSearchResult serialization."""

    def test_to_dict_round_trip(self):
        result = WebSearchResult(
            summary="Found 3 papers on this topic.",
            citations=[{"url": "https://example.com", "title": "Paper A"}],
            elapsed_ms=450,
        )
        d = result.to_dict()
        restored = WebSearchResult.from_dict(d)
        assert restored.summary == result.summary
        assert restored.citations == result.citations
        assert restored.elapsed_ms == result.elapsed_ms

    def test_from_dict_missing_fields(self):
        result = WebSearchResult.from_dict({})
        assert result.summary == ""
        assert result.citations == []
        assert result.elapsed_ms == 0


class TestCacheKey:
    """Test cache key normalization."""

    def test_identical_queries_same_key(self):
        assert _cache_key("my query") == _cache_key("my query")

    def test_whitespace_normalised(self):
        assert _cache_key("my  query") == _cache_key("my query")
        assert _cache_key("  my query  ") == _cache_key("my query")

    def test_case_insensitive(self):
        assert _cache_key("My Query") == _cache_key("my query")


class TestWebSearchClient:
    """Test suite for WebSearchClient."""

    @pytest.mark.asyncio
    async def test_search_returns_web_search_result(self):
        """Basic happy path: mock the responses.create call."""
        mock_annotation = MagicMock()
        mock_annotation.type = "url_citation"
        mock_annotation.url = "https://example.com/paper"
        mock_annotation.title = "Relevant Paper"

        mock_text_block = MagicMock()
        mock_text_block.type = "output_text"
        mock_text_block.text = "This topic has been well researched."
        mock_text_block.annotations = [mock_annotation]

        mock_message = MagicMock()
        mock_message.type = "message"
        mock_message.content = [mock_text_block]

        mock_response = MagicMock()
        mock_response.output = [mock_message]

        mock_client = AsyncMock()
        mock_client.responses.create = AsyncMock(return_value=mock_response)

        ws = WebSearchClient(openai_client=mock_client, redis=None)
        result = await ws.search("quantum computing NP problems")

        assert isinstance(result, WebSearchResult)
        assert "well researched" in result.summary
        assert len(result.citations) == 1
        assert result.citations[0]["url"] == "https://example.com/paper"
        assert result.elapsed_ms >= 0

    @pytest.mark.asyncio
    async def test_search_returns_empty_on_api_failure(self):
        """When the OpenAI API raises, return empty result (no crash)."""
        mock_client = AsyncMock()
        mock_client.responses.create = AsyncMock(side_effect=Exception("API down"))

        ws = WebSearchClient(openai_client=mock_client, redis=None)
        result = await ws.search("test query")

        assert result.summary == ""
        assert result.citations == []

    @pytest.mark.asyncio
    async def test_search_uses_redis_cache(self):
        """When a cached result exists, return it without calling the API."""
        cached = json.dumps({
            "summary": "cached summary",
            "citations": [{"url": "https://cached.com", "title": "Cached"}],
            "elapsed_ms": 100,
        })

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=cached)
        mock_redis.set = AsyncMock()

        mock_client = AsyncMock()
        mock_client.responses.create = AsyncMock()

        ws = WebSearchClient(openai_client=mock_client, redis=mock_redis)
        result = await ws.search("test query")

        assert result.summary == "cached summary"
        mock_client.responses.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_search_writes_to_redis_cache(self):
        """After a successful API call, result should be cached in Redis."""
        mock_text_block = MagicMock()
        mock_text_block.type = "output_text"
        mock_text_block.text = "fresh result"
        mock_text_block.annotations = []

        mock_message = MagicMock()
        mock_message.type = "message"
        mock_message.content = [mock_text_block]

        mock_response = MagicMock()
        mock_response.output = [mock_message]

        mock_client = AsyncMock()
        mock_client.responses.create = AsyncMock(return_value=mock_response)

        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.set = AsyncMock()

        ws = WebSearchClient(openai_client=mock_client, redis=mock_redis)
        result = await ws.search("novel query")

        assert result.summary == "fresh result"
        mock_redis.set.assert_called_once()
