"""Tests for OpenAlex topic taxonomy integration.

Covers:
- Topic extraction from OpenAlex API responses (_normalize_paper, _extract_topic)
- Researcher classification from paper topics
- Paper proximity partitioning by topic distance
- Gap map topic enrichment pipeline (majority voting + LLM fallback)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.schemas import ResearcherClassification
from app.services.openalex_client import OpenAlexClient
from app.services.novelty_analyzer import NoveltyAnalyzer
from app.services.gap_map_topic_enricher import GapMapTopicEnricher


# --- Fixtures ---


@pytest.fixture
def client():
    return OpenAlexClient(email="test@example.com")


@pytest.fixture
def raw_paper_with_topic():
    """A raw OpenAlex work result including primary_topic and topics."""
    return {
        "id": "W123",
        "title": "CRISPR-Cas9 Gene Editing in Human Cells",
        "doi": "10.1234/crispr",
        "publication_year": 2024,
        "fwci": 3.2,
        "citation_normalized_percentile": {"value": 0.92},
        "cited_by_percentile_year": {"min": 88, "max": 96},
        "cited_by_count": 250,
        "authorships": [{"author": {"display_name": "Zhang, F."}}],
        "abstract_inverted_index": None,
        "concepts": [],
        "keywords": [],
        "primary_topic": {
            "id": "https://openalex.org/T12345",
            "display_name": "CRISPR Gene Editing",
            "score": 0.98,
            "subfield": {
                "id": "https://openalex.org/subfields/1312",
                "display_name": "Molecular Biology",
            },
            "field": {
                "id": "https://openalex.org/fields/13",
                "display_name": "Biochemistry, Genetics and Molecular Biology",
            },
            "domain": {
                "id": "https://openalex.org/domains/1",
                "display_name": "Life Sciences",
            },
        },
        "topics": [
            {
                "id": "https://openalex.org/T12345",
                "display_name": "CRISPR Gene Editing",
                "score": 0.98,
                "subfield": {"display_name": "Molecular Biology"},
                "field": {"display_name": "Biochemistry, Genetics and Molecular Biology"},
                "domain": {"display_name": "Life Sciences"},
            },
            {
                "id": "https://openalex.org/T67890",
                "display_name": "Gene Therapy Vectors",
                "score": 0.85,
                "subfield": {"display_name": "Genetics"},
                "field": {"display_name": "Biochemistry, Genetics and Molecular Biology"},
                "domain": {"display_name": "Life Sciences"},
            },
            {
                "id": "https://openalex.org/T11111",
                "display_name": "Bioethics of Genetic Engineering",
                "score": 0.72,
                "subfield": {"display_name": "Philosophy"},
                "field": {"display_name": "Arts and Humanities"},
                "domain": {"display_name": "Social Sciences"},
            },
        ],
    }


@pytest.fixture
def raw_paper_without_topic():
    """A raw OpenAlex work result with no topic data."""
    return {
        "id": "W999",
        "title": "A Paper Without Topics",
        "doi": None,
        "publication_year": 2020,
        "fwci": 1.0,
        "cited_by_count": 10,
        "authorships": [],
        "concepts": [],
        "keywords": [],
    }


@pytest.fixture
def papers_for_classification():
    """A set of normalized papers with primary_topic for classification testing."""
    return [
        {
            "id": "W1",
            "title": "Paper 1",
            "fwci": 2.0,
            "primary_topic": {
                "topic": "CRISPR Gene Editing",
                "subfield": "Molecular Biology",
                "field": "Biochemistry, Genetics and Molecular Biology",
                "domain": "Life Sciences",
                "score": 0.95,
            },
        },
        {
            "id": "W2",
            "title": "Paper 2",
            "fwci": 1.5,
            "primary_topic": {
                "topic": "CRISPR Gene Editing",
                "subfield": "Molecular Biology",
                "field": "Biochemistry, Genetics and Molecular Biology",
                "domain": "Life Sciences",
                "score": 0.90,
            },
        },
        {
            "id": "W3",
            "title": "Paper 3",
            "fwci": 3.0,
            "primary_topic": {
                "topic": "Gene Therapy Vectors",
                "subfield": "Genetics",
                "field": "Biochemistry, Genetics and Molecular Biology",
                "domain": "Life Sciences",
                "score": 0.88,
            },
        },
        {
            "id": "W4",
            "title": "Paper 4",
            "fwci": 1.2,
            "primary_topic": {
                "topic": "Machine Learning for Drug Discovery",
                "subfield": "Artificial Intelligence",
                "field": "Computer Science",
                "domain": "Physical Sciences",
                "score": 0.82,
            },
        },
    ]


# --- Test: Topic Extraction in _normalize_paper ---


class TestTopicExtraction:
    """Tests for extracting topic taxonomy from OpenAlex API responses."""

    def test_normalize_paper_extracts_primary_topic(self, client, raw_paper_with_topic):
        result = client._normalize_paper(raw_paper_with_topic)

        assert result["primary_topic"] is not None
        assert result["primary_topic"]["topic"] == "CRISPR Gene Editing"
        assert result["primary_topic"]["subfield"] == "Molecular Biology"
        assert result["primary_topic"]["field"] == "Biochemistry, Genetics and Molecular Biology"
        assert result["primary_topic"]["domain"] == "Life Sciences"
        assert result["primary_topic"]["score"] == 0.98
        assert result["primary_topic"]["topic_id"] == "https://openalex.org/T12345"

    def test_normalize_paper_extracts_topics_array(self, client, raw_paper_with_topic):
        result = client._normalize_paper(raw_paper_with_topic)

        assert len(result["topics"]) == 3
        assert result["topics"][0]["topic"] == "CRISPR Gene Editing"
        assert result["topics"][1]["topic"] == "Gene Therapy Vectors"
        assert result["topics"][2]["topic"] == "Bioethics of Genetic Engineering"

    def test_normalize_paper_no_topic_data(self, client, raw_paper_without_topic):
        result = client._normalize_paper(raw_paper_without_topic)

        assert result["primary_topic"] is None
        assert result["topics"] == []

    def test_extract_topic_none_input(self):
        assert OpenAlexClient._extract_topic(None) is None

    def test_extract_topic_empty_dict(self):
        assert OpenAlexClient._extract_topic({}) is None

    def test_extract_topic_missing_display_name(self):
        assert OpenAlexClient._extract_topic({"id": "T123"}) is None

    def test_extract_topic_missing_nested_fields(self):
        result = OpenAlexClient._extract_topic({
            "display_name": "Some Topic",
            "score": 0.9,
        })
        assert result is not None
        assert result["topic"] == "Some Topic"
        assert result["subfield"] is None
        assert result["field"] is None
        assert result["domain"] is None

    def test_extract_topic_full_hierarchy(self):
        result = OpenAlexClient._extract_topic({
            "id": "https://openalex.org/T100",
            "display_name": "Dark Matter Detection",
            "score": 0.95,
            "subfield": {"display_name": "Nuclear and High Energy Physics"},
            "field": {"display_name": "Physics and Astronomy"},
            "domain": {"display_name": "Physical Sciences"},
        })
        assert result == {
            "topic": "Dark Matter Detection",
            "topic_id": "https://openalex.org/T100",
            "subfield": "Nuclear and High Energy Physics",
            "field": "Physics and Astronomy",
            "domain": "Physical Sciences",
            "score": 0.95,
        }


# --- Test: Researcher Classification ---


class TestResearcherClassification:
    """Tests for extracting researcher taxonomy from paper topics."""

    def test_classification_from_papers(self, papers_for_classification):
        result = NoveltyAnalyzer._extract_researcher_taxonomy(papers_for_classification)

        assert isinstance(result, ResearcherClassification)
        assert result.primary_domain == "Life Sciences"
        assert result.primary_field == "Biochemistry, Genetics and Molecular Biology"
        assert result.primary_subfield == "Molecular Biology"
        assert result.primary_topic == "CRISPR Gene Editing"

    def test_secondary_topics(self, papers_for_classification):
        result = NoveltyAnalyzer._extract_researcher_taxonomy(papers_for_classification)

        assert "Gene Therapy Vectors" in result.secondary_topics
        assert "Machine Learning for Drug Discovery" in result.secondary_topics
        # Primary topic should NOT be in secondary
        assert "CRISPR Gene Editing" not in result.secondary_topics

    def test_topic_diversity(self, papers_for_classification):
        result = NoveltyAnalyzer._extract_researcher_taxonomy(papers_for_classification)

        # 3 unique subfields (Molecular Biology, Genetics, Artificial Intelligence) / 4 papers = 0.75
        assert result.topic_diversity == 0.75

    def test_classification_no_topics(self):
        papers = [
            {"id": "W1", "title": "Paper 1", "fwci": 1.0},
            {"id": "W2", "title": "Paper 2", "fwci": 1.5, "primary_topic": None},
        ]
        result = NoveltyAnalyzer._extract_researcher_taxonomy(papers)

        assert result.primary_domain is None
        assert result.primary_field is None
        assert result.primary_topic is None
        assert result.topic_diversity is None

    def test_classification_single_topic(self):
        papers = [
            {
                "id": "W1",
                "primary_topic": {
                    "topic": "Protein Folding",
                    "subfield": "Structural Biology",
                    "field": "Biochemistry, Genetics and Molecular Biology",
                    "domain": "Life Sciences",
                    "score": 0.99,
                },
            }
        ]
        result = NoveltyAnalyzer._extract_researcher_taxonomy(papers)

        assert result.primary_topic == "Protein Folding"
        assert result.topic_diversity == 1.0  # 1 unique subfield / 1 paper
        assert result.secondary_topics == []

    def test_classification_weighted_voting(self):
        """Higher-score topics should win in a tie."""
        papers = [
            {
                "id": "W1",
                "primary_topic": {
                    "topic": "Topic A",
                    "subfield": "Sub A",
                    "field": "Field A",
                    "domain": "Domain A",
                    "score": 0.99,  # Higher score
                },
            },
            {
                "id": "W2",
                "primary_topic": {
                    "topic": "Topic B",
                    "subfield": "Sub B",
                    "field": "Field B",
                    "domain": "Domain B",
                    "score": 0.50,  # Lower score
                },
            },
        ]
        result = NoveltyAnalyzer._extract_researcher_taxonomy(papers)

        assert result.primary_topic == "Topic A"
        assert result.primary_domain == "Domain A"


# --- Test: Proximity Partitioning ---


class TestProximityPartitioning:
    """Tests for partitioning papers by topic proximity to researcher."""

    def test_partition_all_tiers(self, papers_for_classification):
        classification = ResearcherClassification(
            primary_domain="Life Sciences",
            primary_field="Biochemistry, Genetics and Molecular Biology",
            primary_subfield="Molecular Biology",
            primary_topic="CRISPR Gene Editing",
        )

        tiers = NoveltyAnalyzer._partition_by_proximity(
            papers_for_classification, classification
        )

        # Papers 1,2 = CRISPR Gene Editing → same_topic
        assert len(tiers["same_topic"]) == 2
        # Paper 3 = Gene Therapy Vectors, subfield=Genetics → same_field (not same_subfield since it's Genetics not Molecular Biology)
        assert len(tiers["same_field"]) == 1
        # Paper 4 = Computer Science → cross_field
        assert len(tiers["cross_field"]) == 1
        # Nothing in same_subfield (Genetics is a different subfield)
        assert len(tiers["same_subfield"]) == 0

    def test_partition_same_subfield(self):
        """Paper in same subfield but different topic."""
        papers = [
            {
                "id": "W1",
                "primary_topic": {
                    "topic": "RNA Splicing",
                    "subfield": "Molecular Biology",
                    "field": "Biochemistry, Genetics and Molecular Biology",
                    "domain": "Life Sciences",
                },
            }
        ]
        classification = ResearcherClassification(
            primary_topic="CRISPR Gene Editing",
            primary_subfield="Molecular Biology",
            primary_field="Biochemistry, Genetics and Molecular Biology",
            primary_domain="Life Sciences",
        )

        tiers = NoveltyAnalyzer._partition_by_proximity(papers, classification)

        assert len(tiers["same_subfield"]) == 1
        assert len(tiers["same_topic"]) == 0

    def test_partition_no_classification(self):
        """All papers go to cross_field if classification has no data."""
        papers = [
            {"id": "W1", "primary_topic": {"topic": "X", "subfield": "Y", "field": "Z", "domain": "D"}},
        ]
        classification = ResearcherClassification()

        tiers = NoveltyAnalyzer._partition_by_proximity(papers, classification)

        assert len(tiers["cross_field"]) == 1

    def test_partition_papers_without_topics(self):
        """Papers without primary_topic go to cross_field."""
        papers = [
            {"id": "W1"},
            {"id": "W2", "primary_topic": None},
        ]
        classification = ResearcherClassification(
            primary_topic="Something", primary_subfield="Sub", primary_field="F", primary_domain="D"
        )

        tiers = NoveltyAnalyzer._partition_by_proximity(papers, classification)

        assert len(tiers["cross_field"]) == 2


# --- Test: Gap Map Topic Enricher ---


class TestTopicEnricherVoting:
    """Tests for majority voting in the enrichment pipeline."""

    def test_vote_single_topic(self):
        topics = [
            {"topic": "X", "subfield": "S", "field": "F", "domain": "D", "score": 0.9}
        ]
        result = GapMapTopicEnricher._vote_on_taxonomy(topics)
        assert result == {"topic": "X", "subfield": "S", "field": "F", "domain": "D"}

    def test_vote_majority_wins(self):
        topics = [
            {"topic": "A", "subfield": "SA", "field": "FA", "domain": "DA", "score": 0.8},
            {"topic": "A", "subfield": "SA", "field": "FA", "domain": "DA", "score": 0.7},
            {"topic": "B", "subfield": "SB", "field": "FB", "domain": "DB", "score": 0.9},
        ]
        result = GapMapTopicEnricher._vote_on_taxonomy(topics)
        assert result["topic"] == "A"
        assert result["domain"] == "DA"

    def test_vote_weighted_by_score(self):
        """When count is tied, higher total score wins."""
        topics = [
            {"topic": "A", "subfield": "S", "field": "F", "domain": "D", "score": 0.3},
            {"topic": "B", "subfield": "S2", "field": "F2", "domain": "D2", "score": 0.99},
        ]
        result = GapMapTopicEnricher._vote_on_taxonomy(topics)
        # B has higher score (0.99 vs 0.3)
        assert result["topic"] == "B"

    def test_vote_missing_fields(self):
        topics = [
            {"topic": "X", "score": 0.9},  # Missing subfield, field, domain
        ]
        result = GapMapTopicEnricher._vote_on_taxonomy(topics)
        assert result["topic"] == "X"
        assert result["subfield"] is None
        assert result["field"] is None
        assert result["domain"] is None


class TestTopicEnricherClassify:
    """Tests for the full classification pipeline in GapMapTopicEnricher."""

    @pytest.fixture
    def enricher(self):
        openalex = MagicMock()
        openai = AsyncMock()
        repo = MagicMock()
        return GapMapTopicEnricher(
            openalex_client=openalex,
            openai_client=openai,
            repository=repo,
        )

    @pytest.mark.asyncio
    async def test_classify_uses_openalex_when_available(self, enricher):
        """When OpenAlex returns papers with topics, use majority voting."""
        enricher._openalex.search_papers_title_abstract = AsyncMock(return_value=[
            {
                "primary_topic": {
                    "topic": "Dark Matter",
                    "subfield": "Nuclear and High Energy Physics",
                    "field": "Physics and Astronomy",
                    "domain": "Physical Sciences",
                    "score": 0.95,
                },
            },
        ])

        entry = MagicMock()
        entry.title = "Dark Matter Detection Methods"
        entry.description = "Methods for detecting dark matter particles"
        entry.category = None
        entry.tags = []

        result = await enricher._classify_entry(entry)

        assert result["topic"] == "Dark Matter"
        assert result["domain"] == "Physical Sciences"

    @pytest.mark.asyncio
    async def test_classify_falls_back_to_llm(self, enricher):
        """When OpenAlex returns no papers, fall back to LLM."""
        enricher._openalex.search_papers_title_abstract = AsyncMock(return_value=[])

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"domain": "Health Sciences", "field": "Medicine", "subfield": "Epidemiology", "topic": "Pandemic Preparedness"}'
        enricher._openai.chat.completions.create = AsyncMock(return_value=mock_response)

        entry = MagicMock()
        entry.title = "Why Do Cats Purr?"
        entry.description = "The biological mechanism behind feline purring"
        entry.category = None
        entry.tags = []

        result = await enricher._classify_entry(entry)

        assert result is not None
        assert result["domain"] == "Health Sciences"
        assert result["topic"] == "Pandemic Preparedness"

    @pytest.mark.asyncio
    async def test_classify_papers_without_topics_triggers_llm(self, enricher):
        """Papers returned but none have primary_topic → LLM fallback."""
        enricher._openalex.search_papers_title_abstract = AsyncMock(return_value=[
            {"id": "W1", "title": "Some paper"},  # No primary_topic
        ])

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"domain": "Life Sciences", "field": "Agricultural and Biological Sciences", "subfield": "Animal Science", "topic": "Feline Vocalization"}'
        enricher._openai.chat.completions.create = AsyncMock(return_value=mock_response)

        entry = MagicMock()
        entry.title = "Why Do Cats Purr?"
        entry.description = ""
        entry.category = None
        entry.tags = []

        result = await enricher._classify_entry(entry)

        assert result["domain"] == "Life Sciences"
        enricher._openai.chat.completions.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_classify_llm_failure_returns_none(self, enricher):
        """LLM failure should return None gracefully."""
        enricher._openalex.search_papers_title_abstract = AsyncMock(return_value=[])
        enricher._openai.chat.completions.create = AsyncMock(side_effect=Exception("API error"))

        entry = MagicMock()
        entry.title = "Unknown Research Gap"
        entry.description = ""
        entry.category = None
        entry.tags = []

        result = await enricher._classify_entry(entry)

        assert result is None
