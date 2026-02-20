"""Scraper for Wikenigma unknown facts repository."""

import asyncio
import logging
import re

from bs4 import BeautifulSoup

from app.models.schemas import GapMapEntry
from app.services.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

AZ_LISTING_URL = "https://wikenigma.org.uk/a-z_listing"
BASE_URL = "https://wikenigma.org.uk"

CATEGORY_MAP = {
    "chemistry": "Chemistry",
    "computer_science": "Computer Science",
    "earth_sciences": "Earth Sciences",
    "history": "History",
    "language": "Language",
    "life_sciences": "Life Sciences",
    "mathematics": "Mathematics",
    "medicine": "Medicine",
    "philosophy": "Philosophy",
    "physics": "Physics",
    "psychology": "Psychology",
}

# Max concurrent detail page fetches (via Oxylabs proxy)
MAX_CONCURRENCY = 5


class WikienigmaScraper(BaseScraper):
    """Scraper for Wikenigma (wikenigma.org.uk).

    Phase 1: Fetch A-Z listing for all ~1,266 article titles and URLs.
    Phase 2: Fetch individual article pages for descriptions (batched).

    Uses Oxylabs proxy (site blocks bot User-Agents).
    """

    source_name = "wikenigma"

    async def scrape(self) -> list[GapMapEntry]:
        # Phase 1: Get all article links from A-Z listing
        html = await self.fetch(AZ_LISTING_URL, force_oxylabs=True)
        soup = BeautifulSoup(html, "lxml")

        article_links: list[tuple[str, str]] = []
        # DokuWiki A-Z listing: <a class="wikilink1" href="...">Title</a>
        for link in soup.select("div.pagequery a.wikilink1"):
            href = link.get("href", "")
            title = link.get_text(strip=True)
            if not href or not title:
                continue
            # Only include content pages, skip other/ categories
            wiki_id = link.get("data-wiki-id", "")
            if wiki_id and wiki_id.startswith("content:other:"):
                continue
            if not href.startswith("http"):
                href = f"{BASE_URL}{href}"
            article_links.append((title, href))

        logger.info(
            "Wikenigma: found %d article links from A-Z listing", len(article_links)
        )

        if not article_links:
            return []

        # Phase 2: Fetch detail pages for descriptions
        semaphore = asyncio.Semaphore(MAX_CONCURRENCY)
        entries: list[GapMapEntry] = []
        lock = asyncio.Lock()

        async def fetch_detail(title: str, url: str) -> None:
            async with semaphore:
                try:
                    detail_html = await self.fetch(url, force_oxylabs=True)
                    detail_soup = BeautifulSoup(detail_html, "lxml")

                    # Extract description from wiki content
                    content_div = detail_soup.select_one(
                        "div.page.group, #wiki__text"
                    )
                    description = ""
                    if content_div:
                        paragraphs = content_div.find_all("p", limit=3)
                        description = " ".join(
                            p.get_text(strip=True)
                            for p in paragraphs
                            if p.get_text(strip=True)
                        )
                    # Truncate long descriptions
                    if len(description) > 500:
                        description = description[:497] + "..."

                    category = self._extract_category(url)
                    tags = []
                    if category:
                        tags.append(category.lower().replace(" ", "-"))

                    entry = GapMapEntry(
                        title=title,
                        description=description or f"Known unknown: {title}",
                        source="wikenigma",
                        source_url=url,
                        category=category,
                        tags=tags,
                    )
                    async with lock:
                        entries.append(entry)
                except Exception:
                    logger.debug("Failed to fetch Wikenigma detail: %s", url)

        # Run all detail fetches concurrently (bounded by semaphore)
        tasks = [fetch_detail(title, url) for title, url in article_links]
        await asyncio.gather(*tasks)

        logger.info("Wikenigma: parsed %d entries with descriptions", len(entries))
        return entries

    @staticmethod
    def _extract_category(url: str) -> str | None:
        """Extract category from URL like /content/physics/ball-lightning."""
        match = re.search(r"/content/([^/]+)", url)
        if match:
            slug = match.group(1)
            return CATEGORY_MAP.get(slug, slug.replace("_", " ").title())
        return None
