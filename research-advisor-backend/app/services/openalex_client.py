"""OpenAlex API client for retrieving paper metadata and FWCI metrics."""

import httpx
from loguru import logger


def _decode_abstract(index: dict | None) -> str | None:
    """Reconstruct abstract from OpenAlex abstract_inverted_index.

    OpenAlex stores abstracts as inverted index: token -> list of positions.
    Reconstruct by placing tokens at positions and joining.
    """
    if not index or not isinstance(index, dict):
        return None
    try:
        positions: list[tuple[int, str]] = []
        for token, pos_list in index.items():
            if isinstance(pos_list, list):
                for p in pos_list:
                    if isinstance(p, (int, float)):
                        positions.append((int(p), token))
            elif isinstance(pos_list, (int, float)):
                positions.append((int(pos_list), token))
        if not positions:
            return None
        max_pos = max(p[0] for p in positions)
        tokens: list[str] = [""] * (max_pos + 1)
        for pos, token in positions:
            tokens[pos] = token
        return " ".join(t for t in tokens if t).strip() or None
    except Exception:
        return None


class OpenAlexClient:
    """Async client for the OpenAlex API.

    Queries OpenAlex for papers related to a research question and extracts
    FWCI, citation percentiles, and other bibliometric data.
    """

    BASE_URL = "https://api.openalex.org"

    def __init__(
        self,
        email: str,
        api_key: str | None = None,
        per_page: int = 20,
    ):
        self.email = email
        self.api_key = api_key
        self.per_page = per_page
        self._http_client = httpx.AsyncClient(timeout=30.0)

    async def search_papers(self, query: str, limit: int | None = None) -> list[dict]:
        """Search OpenAlex for papers matching a query.

        Args:
            query: The search query (research question or topic).
            limit: Max number of results. Defaults to self.per_page.

        Returns:
            List of paper dicts with normalized fields. Empty list on error.
        """
        per_page = limit or self.per_page
        params: dict = {
            "search": query,
            "per_page": per_page,
            "mailto": self.email,
        }
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = await self._http_client.get(
                f"{self.BASE_URL}/works",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            return [self._normalize_paper(r) for r in data.get("results", [])]
        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
            logger.warning(f"OpenAlex API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error querying OpenAlex: {e}")
            return []

    def _normalize_paper(self, raw: dict) -> dict:
        """Extract and normalize fields from a raw OpenAlex work result.

        Handles None values gracefully for all optional fields.
        Includes abstract (decoded from inverted index), concepts, and keywords.
        """
        cnp = raw.get("citation_normalized_percentile")
        cbpy = raw.get("cited_by_percentile_year")

        authors = []
        for authorship in raw.get("authorships", []):
            author = authorship.get("author", {})
            name = author.get("display_name")
            if name:
                authors.append(name)

        # Decode abstract from abstract_inverted_index
        abstract = _decode_abstract(raw.get("abstract_inverted_index"))

        # Top concepts: (display_name, score), cap at 5
        concepts: list[tuple[str, float]] = []
        for c in raw.get("concepts", [])[:5]:
            if isinstance(c, dict):
                disp = c.get("display_name")
                score = c.get("score", 0)
                if disp:
                    concepts.append((disp, float(score) if score is not None else 0))

        # Top keywords: (keyword, score), cap at 5
        keywords: list[tuple[str, float]] = []
        for k in raw.get("keywords", [])[:5]:
            if isinstance(k, dict):
                kw = k.get("keyword") or k.get("display_name")
                score = k.get("score", 0)
                if kw:
                    keywords.append((str(kw), float(score) if score is not None else 0))

        return {
            "id": raw.get("id"),
            "title": raw.get("title", ""),
            "doi": raw.get("doi"),
            "publication_year": raw.get("publication_year"),
            "fwci": raw.get("fwci"),
            "citation_normalized_percentile": cnp["value"] if isinstance(cnp, dict) else None,
            "cited_by_percentile_year_min": cbpy["min"] if isinstance(cbpy, dict) else None,
            "cited_by_percentile_year_max": cbpy["max"] if isinstance(cbpy, dict) else None,
            "cited_by_count": raw.get("cited_by_count", 0),
            "authors": authors,
            "abstract": abstract,
            "concepts": concepts,
            "keywords": keywords,
        }

    def calculate_fwci_stats(self, papers: list[dict]) -> dict:
        """Calculate aggregate FWCI statistics from a list of papers.

        Args:
            papers: List of normalized paper dicts from search_papers().

        Returns:
            Dict with average_fwci, fwci_percentile, papers_with_fwci,
            citation_percentile_min, citation_percentile_max.
        """
        fwci_values = [p["fwci"] for p in papers if p.get("fwci") is not None]
        cnp_values = [
            p["citation_normalized_percentile"]
            for p in papers
            if p.get("citation_normalized_percentile") is not None
        ]
        min_percentiles = [
            p["cited_by_percentile_year_min"]
            for p in papers
            if p.get("cited_by_percentile_year_min") is not None
        ]
        max_percentiles = [
            p["cited_by_percentile_year_max"]
            for p in papers
            if p.get("cited_by_percentile_year_max") is not None
        ]

        avg_fwci = sum(fwci_values) / len(fwci_values) if fwci_values else None
        avg_cnp = sum(cnp_values) / len(cnp_values) if cnp_values else None

        return {
            "average_fwci": avg_fwci,
            "fwci_percentile": avg_cnp,
            "papers_with_fwci": len(fwci_values),
            "citation_percentile_min": min(min_percentiles) if min_percentiles else None,
            "citation_percentile_max": max(max_percentiles) if max_percentiles else None,
        }

    async def search_papers_semantic(
        self, query: str, limit: int | None = None
    ) -> list[dict]:
        """Search OpenAlex using semantic (embedding) search.

        Requires API key. Costs 1,000 credits per query.
        Returns papers ranked by semantic similarity.
        """
        if not self.api_key:
            logger.warning("Semantic search requires OpenAlex API key, falling back to keyword")
            return await self.search_papers(query, limit=limit or self.per_page)

        count = min(limit or self.per_page, 100)

        try:
            response = await self._http_client.get(
                f"{self.BASE_URL}/find/works",
                params={
                    "query": query[:10000],
                    "count": count,
                    "api_key": self.api_key,
                },
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            papers = []
            for r in results:
                work = r.get("work") if isinstance(r, dict) else None
                if work:
                    papers.append(self._normalize_paper(work))
            return papers
        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
            logger.warning(f"OpenAlex semantic search error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in semantic search: {e}")
            return []

    async def close(self):
        """Close the underlying HTTP client."""
        await self._http_client.aclose()
