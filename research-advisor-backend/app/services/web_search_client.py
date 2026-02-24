"""OpenAI web-search tool wrapper for supplemental research intelligence.

Uses the OpenAI Responses API with the built-in web_search tool to retrieve
up-to-date information with cited sources. Results are cached in Redis to
avoid redundant API calls.
"""

import hashlib
import json
import logging
import time

from openai import AsyncOpenAI

from app.config import get_settings

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 3600


class WebSearchResult:
    """Container for a web-search response with extracted citations."""

    __slots__ = ("summary", "citations", "elapsed_ms")

    def __init__(self, summary: str, citations: list[dict], elapsed_ms: int):
        self.summary = summary
        self.citations = citations
        self.elapsed_ms = elapsed_ms

    def to_dict(self) -> dict:
        return {
            "summary": self.summary,
            "citations": self.citations,
            "elapsed_ms": self.elapsed_ms,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WebSearchResult":
        return cls(
            summary=d.get("summary", ""),
            citations=d.get("citations", []),
            elapsed_ms=d.get("elapsed_ms", 0),
        )


def _cache_key(query: str) -> str:
    normalised = " ".join(query.lower().split())
    digest = hashlib.sha256(normalised.encode()).hexdigest()[:16]
    return f"websearch:{digest}"


class WebSearchClient:
    """Thin wrapper around the OpenAI Responses API web_search tool."""

    def __init__(
        self,
        openai_client: AsyncOpenAI | None = None,
        redis=None,
    ):
        self._client = openai_client
        self._redis = redis

    async def search(self, query: str, context: str = "") -> WebSearchResult:
        """Run a web search via OpenAI and return summarised results with citations.

        Args:
            query: The research question or search query.
            context: Optional additional context to include in the prompt.

        Returns:
            WebSearchResult with summary text and a list of citation dicts.
        """
        if self._client is None:
            self._client = AsyncOpenAI(api_key=get_settings().openai_api_key)

        if self._redis:
            cached = await self._redis.get(_cache_key(query))
            if cached:
                try:
                    return WebSearchResult.from_dict(json.loads(cached))
                except Exception:
                    pass

        prompt = (
            "Search the web for the latest information about this research topic "
            "and summarise what you find. Focus on: (1) whether this has already "
            "been solved or published, (2) current state-of-the-art, (3) impact "
            "and real-world significance. Include source URLs.\n\n"
            f"Research topic: {query}"
        )
        if context:
            prompt += f"\n\nAdditional context: {context}"

        t0 = time.monotonic()
        try:
            response = await self._client.responses.create(
                model="gpt-4o",
                input=prompt,
                tools=[{"type": "web_search"}],
            )
        except Exception:
            logger.exception("Web search API call failed")
            return WebSearchResult(summary="", citations=[], elapsed_ms=0)

        elapsed_ms = int((time.monotonic() - t0) * 1000)

        summary = ""
        citations: list[dict] = []
        for item in response.output:
            if getattr(item, "type", None) == "message":
                for block in getattr(item, "content", []):
                    if getattr(block, "type", None) == "output_text":
                        summary = block.text or ""
                        for ann in getattr(block, "annotations", []):
                            if getattr(ann, "type", None) == "url_citation":
                                citations.append({
                                    "url": ann.url,
                                    "title": getattr(ann, "title", ""),
                                })

        result = WebSearchResult(
            summary=summary,
            citations=citations,
            elapsed_ms=elapsed_ms,
        )

        # Privacy: No user data logged
        logger.info(
            "Web search completed in %dms, %d citations",
            elapsed_ms,
            len(citations),
        )

        if self._redis:
            try:
                await self._redis.set(
                    _cache_key(query),
                    json.dumps(result.to_dict()),
                    ex=CACHE_TTL_SECONDS,
                )
            except Exception:
                pass

        return result
