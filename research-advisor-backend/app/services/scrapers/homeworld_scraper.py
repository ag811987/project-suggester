"""Scraper for Homeworld Bio problem repository."""

import logging

from bs4 import BeautifulSoup

from app.models.schemas import GapMapEntry
from app.services.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

HOMEWORLD_URL = "https://www.homeworld.bio/research/problem-statement-repository/"


class HomeworldScraper(BaseScraper):
    """Scraper for Homeworld Bio problem statements.

    Scrapes https://www.homeworld.bio/research/problem-statement-repository/
    ~52 problem statements with category tags and descriptions.
    """

    source_name = "homeworld"

    async def scrape(self) -> list[GapMapEntry]:
        html = await self.fetch(HOMEWORLD_URL, force_oxylabs=True)
        soup = BeautifulSoup(html, "lxml")
        entries = []

        # Each problem is in a div.box.default container
        boxes = soup.select("div.box.default")

        for box in boxes:
            try:
                # Title and URL from a.title
                title_el = box.select_one("a.title")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                url = title_el.get("href", "")
                if not title or not url:
                    continue

                # Description from div.excerpt
                excerpt_el = box.select_one("div.excerpt")
                description = excerpt_el.get_text(strip=True) if excerpt_el else ""

                # Category tags from div.tags > span
                tags_el = box.select("div.tags span")
                tags = [
                    t.get_text(strip=True).lower().replace(" ", "-")
                    for t in tags_el
                    if t.get_text(strip=True)
                ]

                # First tag as category (e.g., "Greenhouse Gas Removal")
                category = None
                if tags_el:
                    category = tags_el[0].get_text(strip=True)

                entries.append(
                    GapMapEntry(
                        title=title,
                        description=description or f"Problem statement: {title}",
                        source="homeworld",
                        source_url=url,
                        category=category,
                        tags=tags,
                    )
                )
            except Exception:
                logger.warning("Failed to parse Homeworld entry")
                continue

        logger.info("Homeworld: parsed %d entries", len(entries))
        return entries
