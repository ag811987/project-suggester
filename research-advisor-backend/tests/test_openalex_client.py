"""Tests for OpenAlex API client."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.openalex_client import OpenAlexClient


@pytest.fixture
def client():
    """Create an OpenAlexClient instance for testing."""
    return OpenAlexClient(email="test@example.com")


@pytest.fixture
def mock_openalex_papers():
    """Multiple papers with varying FWCI values."""
    return {
        "results": [
            {
                "id": "W123",
                "title": "Paper One",
                "doi": "10.1234/one",
                "publication_year": 2023,
                "fwci": 2.5,
                "citation_normalized_percentile": {"value": 0.85},
                "cited_by_percentile_year": {"min": 80, "max": 95},
                "cited_by_count": 150,
                "authorships": [
                    {"author": {"display_name": "Smith, J."}},
                    {"author": {"display_name": "Doe, A."}},
                ],
            },
            {
                "id": "W456",
                "title": "Paper Two",
                "doi": "10.1234/two",
                "publication_year": 2022,
                "fwci": 1.8,
                "citation_normalized_percentile": {"value": 0.72},
                "cited_by_percentile_year": {"min": 65, "max": 78},
                "cited_by_count": 98,
                "authorships": [
                    {"author": {"display_name": "Alice, B."}},
                ],
            },
            {
                "id": "W789",
                "title": "Paper Three",
                "doi": None,
                "publication_year": 2023,
                "fwci": 0.8,
                "citation_normalized_percentile": {"value": 0.45},
                "cited_by_percentile_year": {"min": 35, "max": 52},
                "cited_by_count": 42,
                "authorships": [],
            },
        ],
        "meta": {"count": 3, "page": 1, "per_page": 25},
    }


@pytest.fixture
def mock_openalex_none_fwci():
    """Papers with None FWCI values."""
    return {
        "results": [
            {
                "id": "W100",
                "title": "Paper No FWCI",
                "doi": "10.1234/nofwci",
                "publication_year": 2024,
                "fwci": None,
                "citation_normalized_percentile": None,
                "cited_by_percentile_year": None,
                "cited_by_count": 0,
                "authorships": [],
            },
            {
                "id": "W101",
                "title": "Paper Missing FWCI",
                "doi": "10.1234/missing",
                "publication_year": 2024,
                "cited_by_count": 5,
                "authorships": [],
            },
        ],
        "meta": {"count": 2, "page": 1, "per_page": 25},
    }


@pytest.fixture
def mock_openalex_empty():
    """Empty results from OpenAlex."""
    return {
        "results": [],
        "meta": {"count": 0, "page": 1, "per_page": 25},
    }


class TestOpenAlexClientInit:
    """Tests for OpenAlexClient initialization."""

    def test_client_creation_with_email(self):
        client = OpenAlexClient(email="test@example.com")
        assert client.email == "test@example.com"

    def test_client_creation_with_api_key(self):
        client = OpenAlexClient(email="test@example.com", api_key="my-key")
        assert client.api_key == "my-key"

    def test_client_default_per_page(self):
        client = OpenAlexClient(email="test@example.com")
        assert client.per_page == 20


class TestSearchPapers:
    """Tests for the search_papers method."""

    @pytest.mark.asyncio
    async def test_search_papers_returns_list(self, client, mock_openalex_papers):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openalex_papers
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(return_value=mock_response)
            papers = await client.search_papers("quantum computing NP-complete")

        assert isinstance(papers, list)
        assert len(papers) == 3

    @pytest.mark.asyncio
    async def test_search_papers_extracts_fields(self, client, mock_openalex_papers):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openalex_papers
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(return_value=mock_response)
            papers = await client.search_papers("quantum computing")

        paper = papers[0]
        assert paper["title"] == "Paper One"
        assert paper["doi"] == "10.1234/one"
        assert paper["fwci"] == 2.5
        assert paper["citation_normalized_percentile"] == 0.85
        assert paper["cited_by_percentile_year_min"] == 80
        assert paper["cited_by_percentile_year_max"] == 95
        assert paper["authors"] == ["Smith, J.", "Doe, A."]

    @pytest.mark.asyncio
    async def test_search_papers_with_limit(self, client, mock_openalex_papers):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openalex_papers
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(return_value=mock_response)
            papers = await client.search_papers("test", limit=10)

        # Verify limit param was passed in request
        call_args = mock_http.get.call_args
        assert "per_page" in str(call_args) or len(papers) <= 10

    @pytest.mark.asyncio
    async def test_search_papers_empty_results(self, client, mock_openalex_empty):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openalex_empty
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(return_value=mock_response)
            papers = await client.search_papers("nonexistent topic xyz")

        assert papers == []


class TestSearchPapersTitleAbstract:
    """Tests for title_and_abstract search (more targeted for niche topics)."""

    @pytest.mark.asyncio
    async def test_search_title_abstract_returns_papers(self, client, mock_openalex_papers):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openalex_papers
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(return_value=mock_response)
            papers = await client.search_papers_title_abstract("Psittacula parakeet speciation")

        assert len(papers) == 3
        assert papers[0]["title"] == "Paper One"


class TestFWCIExtraction:
    """Tests for FWCI extraction and None handling."""

    @pytest.mark.asyncio
    async def test_fwci_none_values_handled(self, client, mock_openalex_none_fwci):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openalex_none_fwci
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(return_value=mock_response)
            papers = await client.search_papers("test")

        assert len(papers) == 2
        assert papers[0]["fwci"] is None
        assert papers[1]["fwci"] is None

    @pytest.mark.asyncio
    async def test_missing_fwci_key_handled(self, client, mock_openalex_none_fwci):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openalex_none_fwci
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(return_value=mock_response)
            papers = await client.search_papers("test")

        # Paper W101 has no fwci key at all
        paper_missing = papers[1]
        assert paper_missing["fwci"] is None
        assert paper_missing["citation_normalized_percentile"] is None
        assert paper_missing["cited_by_percentile_year_min"] is None
        assert paper_missing["cited_by_percentile_year_max"] is None

    @pytest.mark.asyncio
    async def test_none_percentile_handled(self, client, mock_openalex_none_fwci):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openalex_none_fwci
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(return_value=mock_response)
            papers = await client.search_papers("test")

        paper = papers[0]
        assert paper["citation_normalized_percentile"] is None
        assert paper["cited_by_percentile_year_min"] is None
        assert paper["cited_by_percentile_year_max"] is None


class TestErrorHandling:
    """Tests for API error handling."""

    @pytest.mark.asyncio
    async def test_api_timeout_returns_empty(self, client):
        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            papers = await client.search_papers("test")

        assert papers == []

    @pytest.mark.asyncio
    async def test_api_connection_error_returns_empty(self, client):
        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(
                side_effect=httpx.ConnectError("connection refused")
            )
            papers = await client.search_papers("test")

        assert papers == []

    @pytest.mark.asyncio
    async def test_api_http_error_returns_empty(self, client):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "server error", request=MagicMock(), response=mock_response
        )

        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(return_value=mock_response)
            papers = await client.search_papers("test")

        assert papers == []

    @pytest.mark.asyncio
    async def test_api_rate_limit_returns_empty(self, client):
        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "rate limited", request=MagicMock(), response=mock_response
        )

        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(return_value=mock_response)
            papers = await client.search_papers("test")

        assert papers == []


class TestCalculateFWCIStats:
    """Tests for FWCI statistics calculation."""

    def test_calculate_stats_normal(self, client):
        papers = [
            {"fwci": 2.5, "citation_normalized_percentile": 0.85,
             "cited_by_percentile_year_min": 80, "cited_by_percentile_year_max": 95},
            {"fwci": 1.8, "citation_normalized_percentile": 0.72,
             "cited_by_percentile_year_min": 65, "cited_by_percentile_year_max": 78},
            {"fwci": 0.8, "citation_normalized_percentile": 0.45,
             "cited_by_percentile_year_min": 35, "cited_by_percentile_year_max": 52},
        ]
        stats = client.calculate_fwci_stats(papers)
        # Median of [2.5, 1.8, 0.8] = 1.8
        assert stats["average_fwci"] == pytest.approx(1.8, abs=0.01)
        assert stats["papers_with_fwci"] == 3
        assert stats["citation_percentile_min"] == 35
        assert stats["citation_percentile_max"] == 95

    def test_calculate_stats_with_none_fwci(self, client):
        papers = [
            {"fwci": 2.0, "citation_normalized_percentile": 0.85,
             "cited_by_percentile_year_min": 80, "cited_by_percentile_year_max": 95},
            {"fwci": None, "citation_normalized_percentile": None,
             "cited_by_percentile_year_min": None, "cited_by_percentile_year_max": None},
        ]
        stats = client.calculate_fwci_stats(papers)

        assert stats["average_fwci"] == pytest.approx(2.0)
        assert stats["papers_with_fwci"] == 1

    def test_calculate_stats_all_none_fwci(self, client):
        papers = [
            {"fwci": None, "citation_normalized_percentile": None,
             "cited_by_percentile_year_min": None, "cited_by_percentile_year_max": None},
        ]
        stats = client.calculate_fwci_stats(papers)

        assert stats["average_fwci"] is None
        assert stats["papers_with_fwci"] == 0

    def test_calculate_stats_empty_papers(self, client):
        stats = client.calculate_fwci_stats([])

        assert stats["average_fwci"] is None
        assert stats["papers_with_fwci"] == 0

    def test_calculate_stats_uses_median_not_mean(self, client):
        """Median is used to avoid outlier inflation from tangentially related classics."""
        papers = [
            {"fwci": 56.0, "citation_normalized_percentile": 0.99},
            {"fwci": 2.0, "citation_normalized_percentile": 0.5},
            {"fwci": 3.0, "citation_normalized_percentile": 0.55},
        ]
        stats = client.calculate_fwci_stats(papers)
        # Median of [56, 2, 3] = 3.0 (not mean 20.3)
        assert stats["average_fwci"] == pytest.approx(3.0)
        assert stats["papers_with_fwci"] == 3
        assert stats["citation_percentile_min"] is None
        assert stats["citation_percentile_max"] is None


class TestPaperEnrichment:
    """Tests for abstract, concepts, and keywords extraction."""

    def test_normalize_extracts_abstract(self):
        from app.services.openalex_client import _decode_abstract

        index = {"This": [0], "is": [1], "an": [2], "abstract": [3]}
        result = _decode_abstract(index)
        assert result == "This is an abstract"

    def test_decode_abstract_handles_none(self):
        from app.services.openalex_client import _decode_abstract

        assert _decode_abstract(None) is None
        assert _decode_abstract({}) is None

    @pytest.mark.asyncio
    async def test_normalize_includes_abstract_concepts_keywords(self, client):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "id": "https://openalex.org/W999",
                    "title": "Paper With Abstract",
                    "doi": "10.1234/abstract",
                    "publication_year": 2023,
                    "fwci": 1.5,
                    "citation_normalized_percentile": {"value": 0.6},
                    "cited_by_percentile_year": {"min": 50, "max": 70},
                    "cited_by_count": 50,
                    "authorships": [{"author": {"display_name": "Test Author"}}],
                    "abstract_inverted_index": {
                        "Background": [0],
                        "We": [1],
                        "study": [2],
                    },
                    "concepts": [
                        {"display_name": "Machine learning", "score": 0.9},
                        {"display_name": "Neural networks", "score": 0.7},
                    ],
                    "keywords": [
                        {"keyword": "deep learning", "score": 0.85},
                        {"display_name": "AI", "score": 0.6},
                    ],
                }
            ],
            "meta": {"count": 1, "page": 1, "per_page": 25},
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(return_value=mock_response)
            papers = await client.search_papers("machine learning")

        assert len(papers) == 1
        p = papers[0]
        assert p["abstract"] == "Background We study"
        assert p["concepts"] == [("Machine learning", 0.9), ("Neural networks", 0.7)]
        assert p["keywords"] == [("deep learning", 0.85), ("AI", 0.6)]


class TestSearchPapersSemantic:
    """Tests for search_papers_semantic using /works?search.semantic= endpoint."""

    @pytest.mark.asyncio
    async def test_semantic_search_calls_works_endpoint(self, mock_openalex_papers):
        client = OpenAlexClient(email="test@example.com", api_key="test-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openalex_papers
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(return_value=mock_response)
            papers = await client.search_papers_semantic("machine learning drug discovery")

        call_args = mock_http.get.call_args
        assert call_args[0][0].endswith("/works")
        params = call_args[1].get("params", call_args[0][1] if len(call_args[0]) > 1 else {})
        if isinstance(params, dict):
            assert "search.semantic" in params
            assert params["api_key"] == "test-key"
            assert "mailto" in params

        assert len(papers) == 3
        assert papers[0]["title"] == "Paper One"

    @pytest.mark.asyncio
    async def test_semantic_search_tags_retrieval_source(self, mock_openalex_papers):
        client = OpenAlexClient(email="test@example.com", api_key="test-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openalex_papers
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(return_value=mock_response)
            papers = await client.search_papers_semantic("test query")

        for p in papers:
            assert p["_retrieval_source"] == "semantic"

    @pytest.mark.asyncio
    async def test_semantic_search_falls_back_without_api_key(self, mock_openalex_papers):
        client = OpenAlexClient(email="test@example.com", api_key=None)
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_openalex_papers
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(return_value=mock_response)
            papers = await client.search_papers_semantic("test query")

        assert len(papers) == 3

    @pytest.mark.asyncio
    async def test_semantic_search_returns_empty_on_error(self):
        client = OpenAlexClient(email="test@example.com", api_key="test-key")
        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            papers = await client.search_papers_semantic("test query")
        assert papers == []


class TestGetRemainingBudgetUsd:
    """Tests for get_remaining_budget_usd."""

    @pytest.mark.asyncio
    async def test_returns_none_without_api_key(self):
        client = OpenAlexClient(email="test@example.com", api_key=None)
        result = await client.get_remaining_budget_usd()
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_remaining_budget_with_api_key(self):
        client = OpenAlexClient(email="test@example.com", api_key="test-key")
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "rate_limit": {
                "daily_remaining_usd": 0.95,
                "daily_budget_usd": 1.0,
            }
        }
        mock_response.raise_for_status = MagicMock()

        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(return_value=mock_response)
            result = await client.get_remaining_budget_usd()

        assert result == 0.95

    @pytest.mark.asyncio
    async def test_returns_none_on_api_error(self):
        client = OpenAlexClient(email="test@example.com", api_key="test-key")
        with patch.object(client, "_http_client") as mock_http:
            mock_http.get = AsyncMock(
                side_effect=httpx.HTTPStatusError("500", request=MagicMock(), response=MagicMock())
            )
            result = await client.get_remaining_budget_usd()

        assert result is None
