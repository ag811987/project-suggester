"""Abstract base class for gap map scrapers."""

import json
import logging
from abc import ABC, abstractmethod

import httpx

from app.models.schemas import GapMapEntry

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 30.0
OXYLABS_TIMEOUT = 60.0
DEFAULT_USER_AGENT = "ResearchPivotAdvisor/0.1 (academic-research-tool)"


class BaseScraper(ABC):
    """Base class for all gap map scrapers.

    Subclasses must implement the scrape() method and set source_name.
    Provides shared HTTP fetching with optional Oxylabs proxy support.
    """

    source_name: str

    def __init__(
        self,
        use_oxylabs: bool = False,
        oxylabs_username: str | None = None,
        oxylabs_password: str | None = None,
        http_client: httpx.AsyncClient | None = None,
    ):
        self.use_oxylabs = use_oxylabs
        self.oxylabs_username = oxylabs_username
        self.oxylabs_password = oxylabs_password
        self._http_client = http_client
        self._owns_client = http_client is None

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or lazily create the HTTP client."""
        if self._http_client is None:
            self._http_client = httpx.AsyncClient(
                timeout=DEFAULT_TIMEOUT,
                headers={"User-Agent": DEFAULT_USER_AGENT},
                follow_redirects=True,
            )
        return self._http_client

    async def fetch(
        self, url: str, force_oxylabs: bool = False, render: bool = False
    ) -> str:
        """Fetch a URL and return the HTML/text content.

        Uses Oxylabs proxy if configured or force_oxylabs is True.
        """
        if self.use_oxylabs or force_oxylabs:
            return await self._fetch_via_oxylabs(url, render=render)
        client = await self._get_client()
        response = await client.get(url)
        response.raise_for_status()
        return response.text

    async def fetch_json(
        self, url: str, force_oxylabs: bool = False
    ) -> dict | list:
        """Fetch a URL and parse the JSON response."""
        if self.use_oxylabs or force_oxylabs:
            text = await self._fetch_via_oxylabs(url)
            return json.loads(text)
        client = await self._get_client()
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

    async def _fetch_via_oxylabs(
        self, url: str, render: bool = False
    ) -> str:
        """Fetch a URL through the Oxylabs Web Scraper API."""
        if not self.oxylabs_username or not self.oxylabs_password:
            logger.warning(
                "%s: Oxylabs credentials not configured, falling back to direct fetch",
                self.source_name,
            )
            client = await self._get_client()
            response = await client.get(url)
            response.raise_for_status()
            return response.text

        payload: dict = {"source": "universal", "url": url}
        if render:
            payload["render"] = "html"

        client = await self._get_client()
        response = await client.post(
            "https://realtime.oxylabs.io/v1/queries",
            json=payload,
            auth=(self.oxylabs_username, self.oxylabs_password),
            timeout=OXYLABS_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        return data["results"][0]["content"]

    async def close(self):
        """Close the HTTP client if we created it."""
        if self._owns_client and self._http_client is not None:
            await self._http_client.aclose()
            self._http_client = None

    @abstractmethod
    async def scrape(self) -> list[GapMapEntry]:
        """Scrape gap map entries from the source."""
