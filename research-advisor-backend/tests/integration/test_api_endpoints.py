"""Integration tests for API endpoints."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.models.schemas import (
    ChatMessage,
    Citation,
    GapMapEntry,
    NoveltyAssessment,
    PivotSuggestion,
    ResearchProfile,
    ResearchRecommendation,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sample_profile() -> ResearchProfile:
    return ResearchProfile(
        research_question="Can quantum computing solve NP-complete problems efficiently?",
        problem_description="Exploring quantum algorithms",
        skills=["Python", "Quantum Computing"],
        expertise_areas=["Computer Science"],
        motivations=["Scientific curiosity"],
        interests=["Quantum algorithms"],
        extracted_from_files=[],
    )


def _sample_novelty() -> NoveltyAssessment:
    return NoveltyAssessment(
        score=0.7,
        verdict="NOVEL",
        evidence=[
            Citation(
                title="Quantum Computing and NP-Complete Problems",
                authors=["Smith, J."],
                year=2023,
                doi="10.1234/quantum.2024",
                url="https://doi.org/10.1234/quantum.2024",
            )
        ],
        reasoning="The research explores a fundamental open problem.",
        related_papers_count=3,
        average_fwci=1.7,
        fwci_percentile=0.67,
        citation_percentile_min=35,
        citation_percentile_max=95,
        impact_assessment="MEDIUM",
        impact_reasoning="Moderate impact area.",
        expected_impact_assessment="MEDIUM",
        expected_impact_reasoning="Moderate expected impact.",
    )


def _sample_recommendation() -> ResearchRecommendation:
    return ResearchRecommendation(
        recommendation="CONTINUE",
        confidence=0.8,
        narrative_report="# Report\n\nContinue your research.",
        novelty_assessment=_sample_novelty(),
        pivot_suggestions=[],
        evidence_citations=[],
    )


def _sample_gap_entries() -> list[GapMapEntry]:
    return [
        GapMapEntry(
            title="Scalable Cell Therapies",
            description="Methods for scaling cell therapies",
            source="convergent",
            source_url="https://gap-map.org/1",
            category="Biotech",
            tags=["cell-therapy"],
        )
    ]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

class FakeRedis:
    """In-memory fake Redis for testing."""

    def __init__(self):
        self._store: dict[str, str] = {}
        self._ttls: dict[str, int] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value
        if ex is not None:
            self._ttls[key] = ex

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)
        self._ttls.pop(key, None)

    async def expire(self, key: str, seconds: int) -> None:
        if key in self._store:
            self._ttls[key] = seconds

    async def aclose(self) -> None:
        pass

    def has(self, key: str) -> bool:
        return key in self._store


@pytest.fixture
def fake_redis():
    return FakeRedis()


@pytest.fixture
def mock_settings():
    """Provide test settings that don't require real API keys."""
    with patch("app.api.routes.get_settings") as mock_gs, \
         patch("app.main.get_settings") as mock_gs_main:
        settings = MagicMock()
        settings.app_name = "Test App"
        settings.app_version = "0.1.0"
        settings.debug = False
        settings.cors_origins = ["http://localhost:5173"]
        settings.api_v1_prefix = "/api/v1"
        settings.openai_api_key = "test-key"
        settings.openai_model = "gpt-4-0125-preview"
        settings.openai_temperature = 0.7
        settings.openai_max_tokens = 2000
        settings.openalex_email = "test@example.com"
        settings.redis_url = "redis://localhost:6379/0"
        settings.database_url = "postgresql+asyncpg://postgres:postgres@localhost:5432/test"
        settings.session_ttl_seconds = 3600
        settings.allowed_file_types = ["pdf", "docx", "txt"]
        settings.max_file_size_mb = 10
        mock_gs.return_value = settings
        mock_gs_main.return_value = settings
        yield settings


@pytest.fixture
def app(fake_redis, mock_settings):
    """Create a test FastAPI app with mocked dependencies."""
    from app.main import create_app

    test_app = create_app()

    # Override lifespan state with fakes
    test_app.state.redis = fake_redis
    test_app.state.db_engine = MagicMock()
    test_app.state.db_session_factory = MagicMock()

    return test_app


@pytest.fixture
async def client(app):
    """Create an async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ---------------------------------------------------------------------------
# POST /api/v1/analyze
# ---------------------------------------------------------------------------

class TestAnalyzeEndpoint:
    """Tests for POST /api/v1/analyze."""

    @pytest.mark.asyncio
    async def test_analyze_success(self, client, app, fake_redis):
        """Test successful analysis with mocked services."""
        profile = _sample_profile()
        novelty = _sample_novelty()
        recommendation = _sample_recommendation()
        gap_entries = _sample_gap_entries()

        with patch("app.api.routes.InfoCollectionService") as MockInfoService, \
             patch("app.api.routes.NoveltyAnalyzer") as MockNovelty, \
             patch("app.api.routes.PivotMatcher") as MockMatcher, \
             patch("app.api.routes.ReportGenerator") as MockReport, \
             patch("app.api.routes.GapMapRepository") as MockRepo:

            # Mock InfoCollectionService
            mock_info = AsyncMock()
            mock_info.extract_from_chat = AsyncMock(return_value=profile)
            mock_info.merge_profiles = MagicMock(return_value=profile)
            MockInfoService.return_value = mock_info

            # Mock NoveltyAnalyzer
            mock_novelty = AsyncMock()
            mock_novelty.analyze = AsyncMock(return_value=novelty)
            MockNovelty.return_value = mock_novelty

            # Mock GapMapRepository - setup db_session_factory
            mock_db_entry = MagicMock()
            mock_db_entry.to_pydantic.return_value = gap_entries[0]
            mock_repo = AsyncMock()
            mock_repo.get_all = AsyncMock(return_value=[mock_db_entry])
            MockRepo.return_value = mock_repo

            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            app.state.db_session_factory.return_value = mock_session

            # Mock PivotMatcher
            mock_matcher = AsyncMock()
            mock_matcher.match_pivots = AsyncMock(return_value=[])
            MockMatcher.return_value = mock_matcher

            # Mock ReportGenerator
            mock_report = AsyncMock()
            mock_report.generate_report = AsyncMock(return_value=recommendation)
            MockReport.return_value = mock_report

            messages = [{"role": "user", "content": "I study quantum computing and NP problems"}]

            response = await client.post(
                "/api/v1/analyze",
                data={"messages": json.dumps(messages)},
            )

            assert response.status_code == 200
            data = response.json()
            assert "session_id" in data
            assert data["status"] == "completed"

            # Verify session stored in Redis
            assert fake_redis.has(f"session:{data['session_id']}")

    @pytest.mark.asyncio
    async def test_analyze_invalid_messages_format(self, client):
        """Test that invalid JSON in messages returns 422."""
        response = await client.post(
            "/api/v1/analyze",
            data={"messages": "not-valid-json"},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_empty_messages(self, client):
        """Test that empty messages list returns 422."""
        response = await client.post(
            "/api/v1/analyze",
            data={"messages": json.dumps([])},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_analyze_invalid_file_type(self, client):
        """Test that an unsupported file type returns 400."""
        messages = [{"role": "user", "content": "Test message"}]

        response = await client.post(
            "/api/v1/analyze",
            data={"messages": json.dumps(messages)},
            files=[("files", ("malware.exe", b"binary content", "application/octet-stream"))],
        )
        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]


# ---------------------------------------------------------------------------
# GET /api/v1/analysis/{session_id}
# ---------------------------------------------------------------------------

class TestGetAnalysisEndpoint:
    """Tests for GET /api/v1/analysis/{session_id}."""

    @pytest.mark.asyncio
    async def test_get_analysis_success(self, client, fake_redis):
        """Test retrieving an existing session."""
        recommendation = _sample_recommendation()
        session_id = "test-session-123"

        session_data = {
            "status": "completed",
            "recommendation": recommendation.model_dump_json(),
            "profile": _sample_profile().model_dump_json(),
        }
        await fake_redis.set(f"session:{session_id}", json.dumps(session_data))

        response = await client.get(f"/api/v1/analysis/{session_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["recommendation"] == "CONTINUE"
        assert data["confidence"] == 0.8
        assert "narrative_report" in data

    @pytest.mark.asyncio
    async def test_get_analysis_not_found(self, client):
        """Test 404 for non-existent session."""
        response = await client.get("/api/v1/analysis/nonexistent-id")
        assert response.status_code == 404
        assert "Session not found" in response.json()["detail"]


# ---------------------------------------------------------------------------
# POST /api/v1/chat
# ---------------------------------------------------------------------------

class TestChatEndpoint:
    """Tests for POST /api/v1/chat."""

    @pytest.mark.asyncio
    async def test_chat_success(self, client, fake_redis):
        """Test successful chat follow-up."""
        session_id = "chat-session-456"
        recommendation = _sample_recommendation()

        session_data = {
            "status": "completed",
            "recommendation": recommendation.model_dump_json(),
            "profile": _sample_profile().model_dump_json(),
        }
        await fake_redis.set(f"session:{session_id}", json.dumps(session_data))

        profile = _sample_profile()

        with patch("app.api.routes.InfoCollectionService") as MockInfoService:
            mock_info = AsyncMock()
            mock_info.extract_from_chat = AsyncMock(return_value=profile)
            MockInfoService.return_value = mock_info

            response = await client.post(
                "/api/v1/chat",
                json={"session_id": session_id, "message": "Tell me more about quantum algorithms"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "response" in data
            assert data["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_chat_session_not_found(self, client):
        """Test 404 when chatting with non-existent session."""
        response = await client.post(
            "/api/v1/chat",
            json={"session_id": "nonexistent", "message": "Hello"},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_chat_missing_fields(self, client):
        """Test 422 when required fields are missing."""
        response = await client.post(
            "/api/v1/chat",
            json={"session_id": "some-id"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /api/v1/session/{session_id}
# ---------------------------------------------------------------------------

class TestDeleteSessionEndpoint:
    """Tests for DELETE /api/v1/session/{session_id}."""

    @pytest.mark.asyncio
    async def test_delete_session_success(self, client, fake_redis):
        """Test successful session deletion."""
        session_id = "delete-session-789"
        await fake_redis.set(f"session:{session_id}", '{"status": "completed"}')

        response = await client.delete(f"/api/v1/session/{session_id}")

        assert response.status_code == 204
        assert not fake_redis.has(f"session:{session_id}")

    @pytest.mark.asyncio
    async def test_delete_nonexistent_session(self, client):
        """Test deleting a session that doesn't exist (still returns 204)."""
        response = await client.delete("/api/v1/session/nonexistent")
        assert response.status_code == 204


# ---------------------------------------------------------------------------
# Error cases
# ---------------------------------------------------------------------------

class TestErrorCases:
    """Test various error conditions."""

    @pytest.mark.asyncio
    async def test_invalid_session_id_returns_404(self, client):
        """Test that an invalid session ID returns 404 for GET."""
        response = await client.get("/api/v1/analysis/invalid-uuid-here")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_missing_messages_field_returns_422(self, client):
        """Test that missing the 'messages' form field returns 422."""
        response = await client.post("/api/v1/analyze", data={})
        assert response.status_code == 422
