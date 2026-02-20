"""Scraper for 3ie evidence gap maps."""

import logging

from bs4 import BeautifulSoup

from app.models.schemas import GapMapEntry
from app.services.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

THREEIE_URL = "https://www.3ieimpact.org/evidence-hub/evidence-gap-maps"


class ThreeIEScraper(BaseScraper):
    """Scraper for 3ie Impact evidence gap maps.

    Scrapes https://www.3ieimpact.org/evidence-hub/evidence-gap-maps
    ~42 evidence gap map entries.
    """

    source_name = "3ie"

    async def scrape(self) -> list[GapMapEntry]:
        html = await self.fetch(THREEIE_URL, force_oxylabs=True)
        soup = BeautifulSoup(html, "lxml")
        entries = []

        # 3ie uses Drupal with div.teaser-medium cards inside div.views-row
        cards = soup.select("div.teaser-medium")

        for card in cards:
            try:
                # Title from h2.heading-2 > a
                title_el = card.select_one("h2.heading-2 a")
                if not title_el:
                    continue
                title = title_el.get_text(strip=True)
                url = title_el.get("href", "")
                if not title or not url:
                    continue

                # Make URL absolute if relative
                if url.startswith("/"):
                    url = f"https://www.3ieimpact.org{url}"

                # Description from div.description > p
                desc_el = card.select_one("div.description p")
                description = desc_el.get_text(strip=True) if desc_el else ""

                # Tags from span.tag
                tag_els = card.select("span.tag span.tag__link")
                tags = [
                    t.get_text(strip=True).lower().replace(" ", "-")
                    for t in tag_els
                    if t.get_text(strip=True)
                ]
                if not tags:
                    tags = ["evidence-gap-map"]

                entries.append(
                    GapMapEntry(
                        title=title,
                        description=description
                        or f"Evidence gap map: {title}",
                        source="3ie",
                        source_url=url,
                        category="Development",
                        tags=tags,
                    )
                )
            except Exception:
                logger.warning("Failed to parse 3ie card")
                continue

        logger.info("3ie: parsed %d entries", len(entries))
        return entries
