"""Scraper for Convergent Research gap map data via public JSON API."""

import logging

from app.models.schemas import GapMapEntry
from app.services.scrapers.base_scraper import BaseScraper

logger = logging.getLogger(__name__)

GAPS_URL = "https://www.gap-map.org/data/gaps.json"
FIELDS_URL = "https://www.gap-map.org/data/fields.json"
GAP_PAGE_BASE = "https://www.gap-map.org/gaps/"


class ConvergentScraper(BaseScraper):
    """Scraper for Convergent Research (gap-map.org).

    Uses the public JSON API at /data/gaps.json (~170 research gaps).
    """

    source_name = "convergent"

    async def scrape(self) -> list[GapMapEntry]:
        fields_data = await self.fetch_json(FIELDS_URL, force_oxylabs=True)
        field_map = {}
        if isinstance(fields_data, list):
            field_map = {
                f["id"]: f["name"]
                for f in fields_data
                if "id" in f and "name" in f
            }

        gaps_data = await self.fetch_json(GAPS_URL, force_oxylabs=True)
        if not isinstance(gaps_data, list):
            logger.warning("Unexpected gaps.json format, expected list")
            return []

        entries = []
        for gap in gaps_data:
            try:
                name = gap.get("name", "").strip()
                slug = gap.get("slug", "")
                description = gap.get("description", "").strip()
                if not name or not slug:
                    continue

                field = gap.get("field")
                category = None
                if isinstance(field, dict):
                    category = field.get("name")
                elif isinstance(field, str):
                    category = field_map.get(field)

                raw_tags = gap.get("tags", [])
                tags = [t for t in raw_tags if isinstance(t, str)] if raw_tags else []

                entries.append(
                    GapMapEntry(
                        title=name,
                        description=description or f"Research gap: {name}",
                        source="convergent",
                        source_url=f"{GAP_PAGE_BASE}{slug}",
                        category=category,
                        tags=tags,
                    )
                )
            except Exception:
                logger.warning("Failed to parse gap entry: %s", gap.get("name", "?"))
                continue

        logger.info("Convergent: parsed %d entries from JSON API", len(entries))
        return entries
