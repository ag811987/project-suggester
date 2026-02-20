"""Tests for gap map scrapers and orchestrator."""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.models.schemas import GapMapEntry
from app.services.scrapers.base_scraper import BaseScraper
from app.services.scrapers.convergent_scraper import ConvergentScraper
from app.services.scrapers.homeworld_scraper import HomeworldScraper
from app.services.scrapers.wikenigma_scraper import WikienigmaScraper
from app.services.scrapers.threeie_scraper import ThreeIEScraper
from app.services.scrapers.encyclopedia_scraper import EncyclopediaScraper
from app.services.gap_map_scraper import GapMapScraperOrchestrator


VALID_SOURCES = {"convergent", "homeworld", "wikenigma", "3ie", "encyclopedia"}


# ---- Sample response fixtures ----

SAMPLE_CONVERGENT_FIELDS = [
    {"id": "f1", "name": "Neuroscience"},
    {"id": "f2", "name": "Energy"},
    {"id": "f3", "name": "Biotech"},
]

SAMPLE_CONVERGENT_GAPS = [
    {
        "id": "g1",
        "name": "Brain Circuitry Mapping",
        "slug": "brain-circuitry-mapping",
        "description": "Understanding the complete wiring of the brain at single-cell resolution.",
        "field": {"id": "f1", "name": "Neuroscience"},
        "foundationalCapabilities": [],
        "tags": ["neuroscience", "connectomics"],
    },
    {
        "id": "g2",
        "name": "Low-Cost Geothermal Energy",
        "slug": "low-cost-geothermal",
        "description": "Technologies to reduce geothermal energy extraction costs by 10x.",
        "field": {"id": "f2", "name": "Energy"},
        "foundationalCapabilities": [],
        "tags": [],
    },
    {
        "id": "g3",
        "name": "Protein Design for Novel Functions",
        "slug": "protein-design",
        "description": "Computational methods for designing proteins with new functions.",
        "field": {"id": "f3", "name": "Biotech"},
        "foundationalCapabilities": [],
        "tags": [],
    },
]

SAMPLE_HOMEWORLD_HTML = """
<html><body>
<div class="box default">
  <div class="tags"><span>Greenhouse Gas Removal</span><span>Methane</span></div>
  <div class="date">10/08/2025</div>
  <div class="min">
    <a class="title" href="https://homeworld.pubpub.org/pub/bioreactors" target="_blank">Methane Removal Bioreactors</a>
    <div class="excerpt">Scalable methane removal bioreactor designs are needed.</div>
  </div>
  <div class="author">by Alice, Bob</div>
</div>
<div class="box default">
  <div class="tags"><span>Protein Engineering</span></div>
  <div class="date">09/15/2025</div>
  <div class="min">
    <a class="title" href="https://homeworld.pubpub.org/pub/carbonic-anhydrase" target="_blank">Carbonic Anhydrase Engineering</a>
    <div class="excerpt">Engineer carbonic anhydrase for enhanced weathering applications.</div>
  </div>
  <div class="author">by Charlie</div>
</div>
<div class="box default">
  <div class="tags"><span>Agriculture</span></div>
  <div class="date">08/20/2025</div>
  <div class="min">
    <a class="title" href="https://homeworld.pubpub.org/pub/soil-microbiome" target="_blank">Soil Microbiome Characterization</a>
    <div class="excerpt">Map the soil microbiome to improve agricultural practices.</div>
  </div>
  <div class="author">by Diana</div>
</div>
</body></html>
"""

SAMPLE_WIKENIGMA_AZ_HTML = """
<html><body>
<div class="pagequery">
<ul>
<li><a href="https://wikenigma.org.uk/content/medicine/anaesthesia" class="wikilink1"
    data-wiki-id="content:medicine:anaesthesia">Mechanism of General Anaesthesia</a></li>
<li><a href="https://wikenigma.org.uk/content/life_sciences/handedness" class="wikilink1"
    data-wiki-id="content:life_sciences:handedness">Origin of Handedness</a></li>
<li><a href="https://wikenigma.org.uk/content/physics/ball_lightning" class="wikilink1"
    data-wiki-id="content:physics:ball_lightning">Ball Lightning</a></li>
<li><a href="https://wikenigma.org.uk/content/other/resolved/test" class="wikilink1"
    data-wiki-id="content:other:resolved:test">Resolved Item (should be skipped)</a></li>
</ul>
</div>
</body></html>
"""

SAMPLE_WIKENIGMA_DETAIL_HTML = """
<html><body>
<div class="page group">
  <p>Despite over 170 years of clinical use, the precise mechanism by which
  general anaesthetics produce unconsciousness remains unknown.</p>
  <p>Multiple competing theories exist but none fully explain the phenomenon.</p>
</div>
</body></html>
"""

SAMPLE_3IE_HTML = """
<html><body>
<div class="views-row right">
  <div class="teaser-medium">
    <div class="content">
      <h2 class="heading-2">
        <a href="https://developmentevidence.3ieimpact.org/egm/transport" target="_blank">
          Transport Policy Evidence Gap Map
        </a>
      </h2>
      <span class="tag tag--evidence-gap-map">
        <span class="tag__link">Evidence gap map</span>
      </span>
      <div class="description">
        <p>Global effectiveness evidence on transportation interventions and policies.</p>
      </div>
    </div>
  </div>
</div>
<div class="views-row left">
  <div class="teaser-medium">
    <div class="content">
      <h2 class="heading-2">
        <a href="/evidence-hub/egm/food-security" target="_blank">
          Food Security in Humanitarian Settings
        </a>
      </h2>
      <span class="tag tag--evidence-gap-map">
        <span class="tag__link">Evidence gap map</span>
      </span>
      <div class="description">
        <p>186 impact evaluations and 6 systematic reviews on food security.</p>
      </div>
    </div>
  </div>
</div>
<div class="views-row right">
  <div class="teaser-medium">
    <div class="content">
      <h2 class="heading-2">
        <a href="https://developmentevidence.3ieimpact.org/egm/climate" target="_blank">
          Climate Change and Biodiversity EGM
        </a>
      </h2>
      <span class="tag tag--evidence-gap-map">
        <span class="tag__link">Evidence gap map</span>
      </span>
      <div class="description">
        <p>1,512 impact evaluations on climate change and biodiversity interventions.</p>
      </div>
    </div>
  </div>
</div>
</body></html>
"""



# ---- Helpers ----

def _validate_entries(entries, expected_source, min_count=3):
    """Helper to validate a list of GapMapEntry objects."""
    assert len(entries) >= min_count
    for entry in entries:
        assert isinstance(entry, GapMapEntry)
        assert entry.source == expected_source
        assert entry.title
        assert entry.description
        assert entry.source_url
        assert isinstance(entry.tags, list)


def _mock_response(text: str = "", json_data=None, status_code: int = 200):
    """Create a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.text = text
    resp.raise_for_status = MagicMock()
    if json_data is not None:
        resp.json.return_value = json_data
    return resp


def _oxylabs_response(content: str) -> MagicMock:
    """Wrap content in an Oxylabs API response (POST to realtime API)."""
    return _mock_response(
        json_data={"results": [{"content": content}]}
    )


def _oxylabs_json_response(data) -> MagicMock:
    """Wrap JSON data in an Oxylabs API response (returned as string)."""
    return _mock_response(
        json_data={"results": [{"content": json.dumps(data)}]}
    )


def _oxylabs_client(post_responses=None, single_post_response=None):
    """Create a mock httpx.AsyncClient that routes through Oxylabs (POST).

    All scrapers use force_oxylabs=True, so all fetches go through client.post.
    """
    client = MagicMock()
    if post_responses:
        client.post = AsyncMock(side_effect=post_responses)
    elif single_post_response:
        client.post = AsyncMock(return_value=single_post_response)
    else:
        client.post = AsyncMock(return_value=_mock_response())
    client.get = AsyncMock()
    client.aclose = AsyncMock()
    return client


_OXYLABS_KWARGS = {
    "use_oxylabs": True,
    "oxylabs_username": "test",
    "oxylabs_password": "test",
}


# ---- Base scraper tests ----

class TestBaseScraper:
    """Test base scraper abstract class."""

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            BaseScraper()

    def test_subclass_must_implement_scrape(self):
        class IncompleteScraper(BaseScraper):
            pass

        with pytest.raises(TypeError):
            IncompleteScraper()

    def test_subclass_with_scrape_can_instantiate(self):
        class CompleteScraper(BaseScraper):
            source_name = "test"

            async def scrape(self):
                return []

        scraper = CompleteScraper()
        assert scraper.source_name == "test"


# ---- Convergent scraper tests ----

class TestConvergentScraper:

    async def test_returns_valid_entries(self):
        client = _oxylabs_client(post_responses=[
            _oxylabs_json_response(SAMPLE_CONVERGENT_FIELDS),
            _oxylabs_json_response(SAMPLE_CONVERGENT_GAPS),
        ])
        scraper = ConvergentScraper(http_client=client, **_OXYLABS_KWARGS)
        entries = await scraper.scrape()
        _validate_entries(entries, "convergent")

    async def test_source_name(self):
        scraper = ConvergentScraper()
        assert scraper.source_name == "convergent"

    async def test_entries_have_categories(self):
        client = _oxylabs_client(post_responses=[
            _oxylabs_json_response(SAMPLE_CONVERGENT_FIELDS),
            _oxylabs_json_response(SAMPLE_CONVERGENT_GAPS),
        ])
        scraper = ConvergentScraper(http_client=client, **_OXYLABS_KWARGS)
        entries = await scraper.scrape()
        assert all(e.category is not None for e in entries)

    async def test_source_urls_use_slug(self):
        client = _oxylabs_client(post_responses=[
            _oxylabs_json_response(SAMPLE_CONVERGENT_FIELDS),
            _oxylabs_json_response(SAMPLE_CONVERGENT_GAPS),
        ])
        scraper = ConvergentScraper(http_client=client, **_OXYLABS_KWARGS)
        entries = await scraper.scrape()
        for entry in entries:
            assert "gap-map.org/gaps/" in entry.source_url


# ---- Homeworld scraper tests ----

class TestHomeworldScraper:

    async def test_returns_valid_entries(self):
        client = _oxylabs_client(
            single_post_response=_oxylabs_response(SAMPLE_HOMEWORLD_HTML)
        )
        scraper = HomeworldScraper(http_client=client, **_OXYLABS_KWARGS)
        entries = await scraper.scrape()
        _validate_entries(entries, "homeworld")

    async def test_source_name(self):
        scraper = HomeworldScraper()
        assert scraper.source_name == "homeworld"

    async def test_extracts_categories(self):
        client = _oxylabs_client(
            single_post_response=_oxylabs_response(SAMPLE_HOMEWORLD_HTML)
        )
        scraper = HomeworldScraper(http_client=client, **_OXYLABS_KWARGS)
        entries = await scraper.scrape()
        categories = {e.category for e in entries}
        assert "Greenhouse Gas Removal" in categories


# ---- Wikenigma scraper tests ----

class TestWikenigmaScraper:

    async def test_returns_valid_entries(self):
        # First POST is A-Z listing, then 3 detail pages (4th skipped: other:resolved)
        client = _oxylabs_client(post_responses=[
            _oxylabs_response(SAMPLE_WIKENIGMA_AZ_HTML),
        ] + [
            _oxylabs_response(SAMPLE_WIKENIGMA_DETAIL_HTML),
        ] * 3)
        scraper = WikienigmaScraper(http_client=client, **_OXYLABS_KWARGS)
        entries = await scraper.scrape()
        _validate_entries(entries, "wikenigma")

    async def test_source_name(self):
        scraper = WikienigmaScraper()
        assert scraper.source_name == "wikenigma"

    async def test_skips_other_categories(self):
        client = _oxylabs_client(post_responses=[
            _oxylabs_response(SAMPLE_WIKENIGMA_AZ_HTML),
        ] + [
            _oxylabs_response(SAMPLE_WIKENIGMA_DETAIL_HTML),
        ] * 3)
        scraper = WikienigmaScraper(http_client=client, **_OXYLABS_KWARGS)
        entries = await scraper.scrape()
        assert all("Resolved" not in e.title for e in entries)

    async def test_category_extracted_from_url(self):
        client = _oxylabs_client(post_responses=[
            _oxylabs_response(SAMPLE_WIKENIGMA_AZ_HTML),
        ] + [
            _oxylabs_response(SAMPLE_WIKENIGMA_DETAIL_HTML),
        ] * 3)
        scraper = WikienigmaScraper(http_client=client, **_OXYLABS_KWARGS)
        entries = await scraper.scrape()
        categories = {e.category for e in entries}
        assert "Medicine" in categories or "Physics" in categories


# ---- 3ie scraper tests ----

class TestThreeIEScraper:

    async def test_returns_valid_entries(self):
        client = _oxylabs_client(
            single_post_response=_oxylabs_response(SAMPLE_3IE_HTML)
        )
        scraper = ThreeIEScraper(http_client=client, **_OXYLABS_KWARGS)
        entries = await scraper.scrape()
        _validate_entries(entries, "3ie")

    async def test_source_name(self):
        scraper = ThreeIEScraper()
        assert scraper.source_name == "3ie"

    async def test_all_entries_are_development(self):
        client = _oxylabs_client(
            single_post_response=_oxylabs_response(SAMPLE_3IE_HTML)
        )
        scraper = ThreeIEScraper(http_client=client, **_OXYLABS_KWARGS)
        entries = await scraper.scrape()
        assert all(e.category == "Development" for e in entries)

    async def test_relative_urls_made_absolute(self):
        client = _oxylabs_client(
            single_post_response=_oxylabs_response(SAMPLE_3IE_HTML)
        )
        scraper = ThreeIEScraper(http_client=client, **_OXYLABS_KWARGS)
        entries = await scraper.scrape()
        for entry in entries:
            assert entry.source_url.startswith("http")


# ---- Encyclopedia scraper tests ----

class TestEncyclopediaScraper:

    async def test_source_name(self):
        scraper = EncyclopediaScraper()
        assert scraper.source_name == "encyclopedia"

    async def test_returns_empty_disabled(self):
        scraper = EncyclopediaScraper()
        entries = await scraper.scrape()
        assert entries == []


# ---- Orchestrator tests ----

class TestGapMapScraperOrchestrator:

    async def test_scrape_all_returns_entries_from_all_sources(self):
        orchestrator = GapMapScraperOrchestrator()
        # Mock each scraper's scrape method
        for scraper in orchestrator.scrapers:
            scraper.scrape = AsyncMock(
                return_value=[
                    GapMapEntry(
                        title=f"Test {scraper.source_name} {i}",
                        description=f"Description for {scraper.source_name} {i}",
                        source=scraper.source_name,
                        source_url=f"https://example.com/{scraper.source_name}/{i}",
                        category="Test",
                        tags=["test"],
                    )
                    for i in range(3)
                ]
            )
            scraper.close = AsyncMock()

        all_entries = await orchestrator.scrape_all()
        assert len(all_entries) >= 15
        sources = {e.source for e in all_entries}
        assert sources == VALID_SOURCES

    async def test_orchestrator_has_all_scrapers(self):
        orchestrator = GapMapScraperOrchestrator()
        assert len(orchestrator.scrapers) == 5

    async def test_one_scraper_failure_doesnt_block_others(self):
        orchestrator = GapMapScraperOrchestrator()
        # First scraper fails, others succeed
        orchestrator.scrapers[0].scrape = AsyncMock(side_effect=Exception("fail"))
        orchestrator.scrapers[0].close = AsyncMock()
        for scraper in orchestrator.scrapers[1:]:
            scraper.scrape = AsyncMock(
                return_value=[
                    GapMapEntry(
                        title=f"Test {scraper.source_name}",
                        description=f"Description {scraper.source_name}",
                        source=scraper.source_name,
                        source_url=f"https://example.com/{scraper.source_name}/1",
                        category="Test",
                        tags=["test"],
                    )
                ]
            )
            scraper.close = AsyncMock()

        all_entries = await orchestrator.scrape_all()
        assert len(all_entries) >= 4  # 4 scrapers succeeded
