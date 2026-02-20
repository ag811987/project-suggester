"""Test configuration and fixtures for pytest."""

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.models.gap_map_models import Base

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/research_advisor_test"


@pytest_asyncio.fixture
async def test_db_engine():
    """Create test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(test_db_engine):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session


@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response for testing."""
    return {
        "choices": [{
            "message": {
                "content": '''{
                    "research_question": "Can quantum computing solve NP-complete problems efficiently?",
                    "problem_description": "Exploring quantum algorithms for NP-complete problems",
                    "skills": ["Python", "Quantum Computing", "Algorithm Design"],
                    "expertise_areas": ["Computer Science", "Quantum Physics"],
                    "motivations": ["Scientific curiosity", "Breakthrough research"],
                    "interests": ["Quantum algorithms", "Complexity theory"],
                    "extracted_from_files": ["research_proposal.pdf"]
                }'''
            }
        }]
    }


@pytest.fixture
def mock_openalex_response():
    """Mock OpenAlex API response with FWCI metrics."""
    return {
        "results": [
            {
                "id": "W123456789",
                "title": "Quantum Computing and NP-Complete Problems",
                "doi": "10.1234/quantum.2024",
                "publication_year": 2023,
                "fwci": 2.5,
                "citation_normalized_percentile": {
                    "value": 0.85,
                    "is_in_top_10_percent": True
                },
                "cited_by_percentile_year": {
                    "min": 80,
                    "max": 95
                },
                "cited_by_count": 150
            },
            {
                "id": "W987654321",
                "title": "Limitations of Quantum Algorithms",
                "doi": "10.1234/quantum.2023",
                "publication_year": 2022,
                "fwci": 1.8,
                "citation_normalized_percentile": {
                    "value": 0.72,
                    "is_in_top_10_percent": False
                },
                "cited_by_percentile_year": {
                    "min": 65,
                    "max": 78
                },
                "cited_by_count": 98
            },
            {
                "id": "W111222333",
                "title": "Survey of NP-Complete Problem Solutions",
                "doi": "10.1234/survey.2023",
                "publication_year": 2023,
                "fwci": 0.8,
                "citation_normalized_percentile": {
                    "value": 0.45,
                    "is_in_top_10_percent": False
                },
                "cited_by_percentile_year": {
                    "min": 35,
                    "max": 52
                },
                "cited_by_count": 42
            }
        ],
        "meta": {
            "count": 3,
            "page": 1,
            "per_page": 25
        }
    }


@pytest.fixture
def sample_gap_map_entries():
    """Sample gap map entries for testing."""
    from app.models.schemas import GapMapEntry

    return [
        GapMapEntry(
            title="Scalable Production of Cell Therapies",
            description="Methods to produce cell therapies at scale for clinical use",
            source="convergent",
            source_url="https://www.gap-map.org/entry/1",
            category="Biotech",
            tags=["cell-therapy", "manufacturing", "scale-up"]
        ),
        GapMapEntry(
            title="Protein Design for Novel Functions",
            description="Computational methods for designing proteins with new functions",
            source="convergent",
            source_url="https://www.gap-map.org/entry/2",
            category="Biotech",
            tags=["protein-design", "computational-biology", "synthetic-biology"]
        ),
        GapMapEntry(
            title="Climate Change Mitigation Technologies",
            description="Novel approaches to carbon capture and sequestration",
            source="homeworld",
            source_url="https://www.homeworld.bio/problem/climate-1",
            category="Climate",
            tags=["carbon-capture", "climate", "energy"]
        )
    ]


@pytest.fixture
def sample_research_profile():
    """Sample research profile for testing."""
    from app.models.schemas import ResearchProfile

    return ResearchProfile(
        research_question="Can quantum computing solve NP-complete problems efficiently?",
        problem_description="Exploring quantum algorithms for NP-complete problems",
        skills=["Python", "Quantum Computing", "Algorithm Design"],
        expertise_areas=["Computer Science", "Quantum Physics"],
        motivations=["Scientific curiosity", "Breakthrough research"],
        interests=["Quantum algorithms", "Complexity theory"],
        extracted_from_files=["research_proposal.pdf"]
    )


@pytest.fixture
def sample_novelty_assessment():
    """Sample novelty assessment for testing."""
    from app.models.schemas import NoveltyAssessment, Citation

    return NoveltyAssessment(
        score=0.7,
        verdict="NOVEL",
        evidence=[
            Citation(
                title="Quantum Computing and NP-Complete Problems",
                authors=["Smith, J.", "Doe, A."],
                year=2023,
                doi="10.1234/quantum.2024",
                url="https://doi.org/10.1234/quantum.2024"
            )
        ],
        reasoning="The research question explores a fundamental open problem in quantum computing. While there is existing work, no definitive solution exists.",
        related_papers_count=3,
        average_fwci=1.7,
        fwci_percentile=0.67,
        citation_percentile_min=35,
        citation_percentile_max=95,
        impact_assessment="MEDIUM",
        impact_reasoning="Related papers show moderate impact (avg FWCI 1.7), indicating active but not breakthrough-level research area.",
        expected_impact_assessment="MEDIUM",
        expected_impact_reasoning="The research has moderate expected impact given the novelty of the approach and the researcher's skills.",
    )
