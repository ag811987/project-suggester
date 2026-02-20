# Oxylabs Integration Guide

## Overview

This project uses Oxylabs Web Scraper API for scraping gap map sources. The account credentials are configured and ready to use.

## Account Details

- **Username**: `rndcatalyst_GauK4`
- **Password**: `J+mWtfqT8iTfGR`
- **API Endpoint**: `https://realtime.oxylabs.io/v1/queries`

## API Usage

### For General Web Scraping (Gap Maps)

Use the **"universal" source** for scraping gap map websites:

```python
import httpx
import os

async def scrape_url(url: str) -> str:
    """Scrape a URL using Oxylabs universal source."""

    oxylabs_username = os.getenv("OXYLABS_USERNAME")
    oxylabs_password = os.getenv("OXYLABS_PASSWORD")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://realtime.oxylabs.io/v1/queries",
            auth=(oxylabs_username, oxylabs_password),
            headers={"Content-Type": "application/json"},
            json={
                "source": "universal",
                "url": url
            },
            timeout=30.0
        )
        response.raise_for_status()

        data = response.json()
        # The scraped HTML is in data["results"][0]["content"]
        return data["results"][0]["content"]
```

### Response Format

Oxylabs returns JSON with this structure:

```json
{
    "results": [
        {
            "content": "<html>...</html>",
            "created_at": "2024-01-01 12:00:00",
            "updated_at": "2024-01-01 12:00:01",
            "page": 1,
            "url": "https://example.com",
            "job_id": "123456789",
            "status_code": 200
        }
    ]
}
```

## Integration with Gap Map Scrapers

### Base Scraper Pattern

```python
# app/services/scrapers/base_scraper.py

import httpx
import os
from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from app.models.schemas import GapMapEntry

class BaseScraper(ABC):
    """Base class for all gap map scrapers."""

    def __init__(self):
        self.oxylabs_username = os.getenv("OXYLABS_USERNAME")
        self.oxylabs_password = os.getenv("OXYLABS_PASSWORD")
        self.oxylabs_endpoint = "https://realtime.oxylabs.io/v1/queries"

    async def fetch_html(self, url: str) -> str:
        """Fetch HTML content using Oxylabs."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.oxylabs_endpoint,
                auth=(self.oxylabs_username, self.oxylabs_password),
                headers={"Content-Type": "application/json"},
                json={
                    "source": "universal",
                    "url": url
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            return data["results"][0]["content"]

    def parse_html(self, html: str) -> BeautifulSoup:
        """Parse HTML with BeautifulSoup."""
        return BeautifulSoup(html, "lxml")

    @abstractmethod
    async def scrape(self) -> list[GapMapEntry]:
        """Scrape gap map entries. Must be implemented by subclass."""
        pass
```

### Example: Convergent Research Scraper

```python
# app/services/scrapers/convergent_scraper.py

from app.services.scrapers.base_scraper import BaseScraper
from app.models.schemas import GapMapEntry

class ConvergentScraper(BaseScraper):
    """Scraper for Convergent Research Gap Map."""

    SOURCE_URL = "https://www.gap-map.org/"
    SOURCE_NAME = "convergent"

    async def scrape(self) -> list[GapMapEntry]:
        """Scrape gap map entries from Convergent Research."""

        # Fetch HTML using Oxylabs
        html = await self.fetch_html(self.SOURCE_URL)
        soup = self.parse_html(html)

        entries = []

        # Example parsing logic (adjust based on actual HTML structure)
        for item in soup.select(".gap-map-item"):  # Adjust selector
            entry = GapMapEntry(
                title=item.select_one(".title").text.strip(),
                description=item.select_one(".description").text.strip(),
                source=self.SOURCE_NAME,
                source_url=self.SOURCE_URL,
                category=item.get("data-category"),  # Adjust based on HTML
                tags=[tag.text.strip() for tag in item.select(".tag")]
            )
            entries.append(entry)

        return entries
```

## Rate Limiting & Best Practices

### Rate Limits
- Oxylabs has account-based rate limits
- Monitor usage to avoid overages
- Use caching to minimize API calls

### Best Practices

1. **Use Background Jobs**: Don't scrape on-demand during user requests
   ```python
   # app/jobs/gap_map_scraper_job.py
   from apscheduler.schedulers.asyncio import AsyncIOScheduler

   scheduler = AsyncIOScheduler()

   @scheduler.scheduled_job('cron', hour=2, minute=0)
   async def scrape_gap_maps():
       """Run daily at 2 AM"""
       orchestrator = GapMapScraperOrchestrator()
       await orchestrator.scrape_all_sources()
   ```

2. **Cache Results**: Store in PostgreSQL, query from cache
   ```python
   # Don't scrape during API requests
   # Instead, query pre-scraped data from database
   entries = await gap_map_repository.get_all()
   ```

3. **Error Handling**: Gracefully handle Oxylabs failures
   ```python
   try:
       html = await self.fetch_html(url)
   except httpx.HTTPStatusError as e:
       logger.error(f"Oxylabs request failed: {e}")
       return []  # Return empty list, don't crash
   except httpx.TimeoutException:
       logger.error(f"Oxylabs timeout for {url}")
       return []
   ```

4. **Respect Timeouts**: Set reasonable timeout values
   ```python
   timeout = httpx.Timeout(30.0, connect=10.0)
   async with httpx.AsyncClient(timeout=timeout) as client:
       # ... scraping logic
   ```

## Testing Without Oxylabs

For development and testing, you can bypass Oxylabs:

```python
# In .env for testing
MOCK_OXYLABS=true

# In base_scraper.py
async def fetch_html(self, url: str) -> str:
    """Fetch HTML content."""

    # For testing/MVP: Use direct HTTP requests
    if os.getenv("MOCK_OXYLABS") == "true":
        async with httpx.AsyncClient() as client:
            response = await client.get(url)
            return response.text

    # Production: Use Oxylabs
    async with httpx.AsyncClient() as client:
        response = await client.post(
            self.oxylabs_endpoint,
            auth=(self.oxylabs_username, self.oxylabs_password),
            headers={"Content-Type": "application/json"},
            json={"source": "universal", "url": url},
            timeout=30.0
        )
        data = response.json()
        return data["results"][0]["content"]
```

## Alternative: Static Sample Data (MVP)

For the 1-hour MVP build, consider using hardcoded sample data:

```python
# app/services/scrapers/convergent_scraper.py

async def scrape(self) -> list[GapMapEntry]:
    """Return sample data for MVP."""

    # MVP: Return hardcoded samples to save time
    return [
        GapMapEntry(
            title="Scalable Production of Cell Therapies",
            description="Methods to produce cell therapies at scale...",
            source="convergent",
            source_url="https://www.gap-map.org/",
            category="Biotech",
            tags=["cell-therapy", "manufacturing", "scale-up"]
        ),
        GapMapEntry(
            title="Protein Design for Novel Functions",
            description="Design proteins with entirely new functions...",
            source="convergent",
            source_url="https://www.gap-map.org/",
            category="Biotech",
            tags=["protein-design", "synthetic-biology"]
        ),
        # ... 3-5 more entries per source
    ]
```

## Gap Map Source URLs

For reference, here are the 5 gap map sources to scrape:

1. **Convergent Research**: https://www.gap-map.org/
2. **Homeworld Bio**: https://www.homeworld.bio/research/problem-statement-repository/
3. **Wikenigma**: https://wikenigma.org.uk/
4. **3ie Impact**: https://www.3ieimpact.org/evidence-hub/evidence-gap-maps
5. **Encyclopedia of World Problems**: https://encyclopedia.uia.org/

## Troubleshooting

### Issue: 401 Unauthorized
- **Cause**: Invalid credentials
- **Fix**: Verify `OXYLABS_USERNAME` and `OXYLABS_PASSWORD` in `.env`

### Issue: 429 Too Many Requests
- **Cause**: Rate limit exceeded
- **Fix**: Implement exponential backoff, reduce scraping frequency

### Issue: Timeout errors
- **Cause**: Slow website or network issues
- **Fix**: Increase timeout, retry with backoff

### Issue: Invalid response format
- **Cause**: Oxylabs changed API response structure
- **Fix**: Check `data["results"][0]["content"]` path

## Cost Estimation

Oxylabs charges per request. For this project:
- **5 gap map sources** × **1 request per source** = 5 requests per scraping run
- **Daily scraping** = 5 requests/day
- **Monthly** = ~150 requests/month

Check your Oxylabs plan for pricing details.

## Security Notes

- ✅ Credentials are in `.env` (not committed to git)
- ✅ Using environment variables (not hardcoded)
- ✅ HTTPS endpoint (secure transmission)
- ⚠️ Monitor usage to avoid overages
- ⚠️ Consider IP whitelisting for production

## References

- Oxylabs Documentation: https://developers.oxylabs.io/scraper-apis/web-scraper-api
- Oxylabs Universal Source: https://developers.oxylabs.io/scraper-apis/web-scraper-api/universal
- Account Dashboard: https://dashboard.oxylabs.io/
