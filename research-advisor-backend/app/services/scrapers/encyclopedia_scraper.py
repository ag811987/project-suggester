"""Scraper for Encyclopedia of World Problems.

NOTE: This scraper is currently disabled. The Encyclopedia site is a Next.js SPA
that only shows problem titles on its browse page (no descriptions). Most entries
are very broad topics (e.g., "War", "Theft") rather than specific research gaps.
Fetching detail pages for descriptions would require expensive Oxylabs JS-rendered
requests for each of the 56,000+ entries with poor signal-to-noise ratio.

The other 4 sources (Convergent, Homeworld, Wikenigma, 3ie) provide ~1,400+
high-quality research gap entries with proper descriptions and categories.
"""

import logging

from app.models.schemas import GapMapEntry
from app.services.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)


class EncyclopediaScraper(BaseScraper):
    """Scraper for Encyclopedia of World Problems (encyclopedia.uia.org).

    Currently returns empty list - see module docstring for rationale.
    """

    source_name = "encyclopedia"

    async def scrape(self) -> list[GapMapEntry]:
        logger.info("Encyclopedia: scraper disabled (low signal-to-noise ratio)")
        return []
