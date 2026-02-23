"""OpenAlex API client for retrieving paper metadata and FWCI metrics."""

import hashlib
import json
import re
import statistics
import time

import httpx
from loguru import logger

_DEBUG_LOG_PATH = "/Users/amit/Coding-Projects/Project-Suggester/.cursor/debug.log"


def _q_fingerprint(q: str) -> dict:
    """Privacy-safe query fingerprint (no raw query logged)."""
    qn = (q or "").strip()
    return {
        "query_len": len(qn),
        "query_sha256_12": hashlib.sha256(qn.encode("utf-8")).hexdigest()[:12]
        if qn
        else None,
    }


def _debug_log(*, location: str, message: str, data: dict, run_id: str, hypothesis_id: str) -> None:
    # region agent log
    payload = {
        "id": f"log_{time.time_ns()}",
        "timestamp": int(time.time() * 1000),
        "location": location,
        "message": message,
        "data": data,
        "runId": run_id,
        "hypothesisId": hypothesis_id,
    }
    try:
        with open(_DEBUG_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
    # endregion


def _safe_httpx_err(e: Exception) -> dict:
    """Privacy-safe HTTP error summary (no URL/query leaked)."""
    out: dict = {"error_type": type(e).__name__}
    if isinstance(e, httpx.HTTPStatusError):
        out["status_code"] = e.response.status_code
    return out


def _sanitize_title_abstract_filter_query(query: str, *, max_len: int = 80) -> str:
    """Sanitize a query string for OpenAlex filter 'title_and_abstract.search'.

    OpenAlex filter syntax is sensitive to certain punctuation and very long strings,
    which can cause 400s. This keeps the query readable while removing known troublemakers.
    """
    q = (query or "").strip()
    if not q:
        return ""
    q = q.replace(":", " ")  # avoid breaking filter key:value parsing
    q = q.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    q = re.sub(r"\s+", " ", q).strip()
    if len(q) > max_len:
        q = q[:max_len].rsplit(" ", 1)[0].strip() or q[:max_len]
    return q


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
        """Search OpenAlex for papers matching a query (title, abstract, fulltext).

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
        # Note: /works does not require an API key; sending api_key can route requests
        # through key-specific quotas. We only send api_key to endpoints that require it
        # (e.g., /find/works and /rate-limit).

        try:
            t0 = time.perf_counter()
            response = await self._http_client.get(
                f"{self.BASE_URL}/works",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results", []) or []
            _debug_log(
                location="app/services/openalex_client.py:search_papers",
                message="OpenAlex /works search completed",
                data={
                    "endpoint": "/works",
                    "mode": "search",
                    "per_page": per_page,
                    "api_key_present": bool(self.api_key),
                    "api_key_sent": False,
                    "mailto_present": bool(self.email),
                    "results_count": len(results),
                    "elapsed_ms": int((time.perf_counter() - t0) * 1000),
                    **_q_fingerprint(query),
                },
                run_id="post-fix",
                hypothesis_id="H_OA_EMPTY",
            )
            return [self._normalize_paper(r) for r in results]
        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
            _debug_log(
                location="app/services/openalex_client.py:search_papers",
                message="OpenAlex /works search failed",
                data={
                    "endpoint": "/works",
                    "mode": "search",
                    "per_page": per_page,
                    "api_key_present": bool(self.api_key),
                    "api_key_sent": False,
                    "mailto_present": bool(self.email),
                    **_safe_httpx_err(e),
                    **_q_fingerprint(query),
                },
                run_id="post-fix",
                hypothesis_id="H_OA_HTTP",
            )
            logger.warning("OpenAlex API error in search_papers (%s)", type(e).__name__)
            return []
        except Exception as e:
            _debug_log(
                location="app/services/openalex_client.py:search_papers",
                message="OpenAlex /works search unexpected failure",
                data={
                    "endpoint": "/works",
                    "mode": "search",
                    "per_page": per_page,
                    "api_key_present": bool(self.api_key),
                    "api_key_sent": False,
                    "mailto_present": bool(self.email),
                    "error_type": type(e).__name__,
                    **_q_fingerprint(query),
                },
                run_id="post-fix",
                hypothesis_id="H_OA_HTTP",
            )
            logger.error(
                "Unexpected error querying OpenAlex in search_papers (%s)", type(e).__name__
            )
            return []

    async def search_papers_title_abstract(
        self, query: str, limit: int | None = None
    ) -> list[dict]:
        """Search OpenAlex using title and abstract only (no fulltext).

        More targeted for niche topics—avoids pulling broad, highly-cited classics
        that mention terms in fulltext but aren't actually about the topic.
        """
        per_page = limit or self.per_page
        q = _sanitize_title_abstract_filter_query(query)
        if not q:
            return []
        params: dict = {
            "filter": f"title_and_abstract.search:{q}",
            "per_page": per_page,
            "mailto": self.email,
        }
        # Note: /works does not require an API key; avoid sending api_key here.

        try:
            t0 = time.perf_counter()
            response = await self._http_client.get(
                f"{self.BASE_URL}/works",
                params=params,
            )
            response.raise_for_status()
            data = response.json()
            results = data.get("results", []) or []
            _debug_log(
                location="app/services/openalex_client.py:search_papers_title_abstract",
                message="OpenAlex /works title_and_abstract.search completed",
                data={
                    "endpoint": "/works",
                    "mode": "title_and_abstract.search",
                    "per_page": per_page,
                    "api_key_present": bool(self.api_key),
                    "api_key_sent": False,
                    "mailto_present": bool(self.email),
                    "results_count": len(results),
                    "elapsed_ms": int((time.perf_counter() - t0) * 1000),
                    **_q_fingerprint(query),
                },
                run_id="post-fix",
                hypothesis_id="H_OA_EMPTY",
            )
            return [self._normalize_paper(r) for r in results]
        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
            _debug_log(
                location="app/services/openalex_client.py:search_papers_title_abstract",
                message="OpenAlex /works title_and_abstract.search failed",
                data={
                    "endpoint": "/works",
                    "mode": "title_and_abstract.search",
                    "per_page": per_page,
                    "api_key_present": bool(self.api_key),
                    "api_key_sent": False,
                    "mailto_present": bool(self.email),
                    **_safe_httpx_err(e),
                    **_q_fingerprint(query),
                },
                run_id="post-fix",
                hypothesis_id="H_OA_HTTP",
            )
            logger.warning(
                "OpenAlex API error in search_papers_title_abstract (%s)", type(e).__name__
            )
            return []
        except Exception as e:
            _debug_log(
                location="app/services/openalex_client.py:search_papers_title_abstract",
                message="OpenAlex /works title_and_abstract.search unexpected failure",
                data={
                    "endpoint": "/works",
                    "mode": "title_and_abstract.search",
                    "per_page": per_page,
                    "api_key_present": bool(self.api_key),
                    "api_key_sent": False,
                    "mailto_present": bool(self.email),
                    "error_type": type(e).__name__,
                    **_q_fingerprint(query),
                },
                run_id="post-fix",
                hypothesis_id="H_OA_HTTP",
            )
            logger.error(
                "Unexpected error querying OpenAlex in search_papers_title_abstract (%s)",
                type(e).__name__,
            )
            return []

    def _normalize_paper(self, raw: dict) -> dict:
        """Extract and normalize fields from a raw OpenAlex work result.

        Handles None values gracefully for all optional fields.
        Includes abstract (decoded from inverted index), concepts, keywords,
        and topic taxonomy (primary_topic + top 3 topics).
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

        # Primary topic taxonomy (Topic → Subfield → Field → Domain)
        primary_topic = self._extract_topic(raw.get("primary_topic"))

        # Top 3 topics for richer classification signals
        topics: list[dict] = []
        for t in raw.get("topics", [])[:3]:
            extracted = self._extract_topic(t)
            if extracted:
                topics.append(extracted)

        return {
            "id": raw.get("id"),
            "title": raw.get("title", ""),
            "doi": raw.get("doi"),
            "publication_year": raw.get("publication_year"),
            "fwci": raw.get("fwci"),
            "relevance_score": raw.get("relevance_score"),
            "citation_normalized_percentile": cnp["value"] if isinstance(cnp, dict) else None,
            "cited_by_percentile_year_min": cbpy["min"] if isinstance(cbpy, dict) else None,
            "cited_by_percentile_year_max": cbpy["max"] if isinstance(cbpy, dict) else None,
            "cited_by_count": raw.get("cited_by_count", 0),
            "authors": authors,
            "abstract": abstract,
            "concepts": concepts,
            "keywords": keywords,
            "primary_topic": primary_topic,
            "topics": topics,
        }

    @staticmethod
    def _extract_topic(topic_data: dict | None) -> dict | None:
        """Extract normalized topic taxonomy from an OpenAlex topic object.

        Returns None if the data is missing or malformed.
        """
        if not topic_data or not isinstance(topic_data, dict):
            return None
        display_name = topic_data.get("display_name")
        if not display_name:
            return None
        subfield = topic_data.get("subfield", {}) or {}
        field = topic_data.get("field", {}) or {}
        domain = topic_data.get("domain", {}) or {}
        return {
            "topic": display_name,
            "topic_id": topic_data.get("id"),
            "subfield": subfield.get("display_name"),
            "field": field.get("display_name"),
            "domain": domain.get("display_name"),
            "score": topic_data.get("score"),
        }

    def calculate_fwci_stats(self, papers: list[dict]) -> dict:
        """Calculate aggregate FWCI statistics from a list of papers.

        Uses median (not mean) to avoid outlier inflation from tangentially
        related highly-cited papers.

        Returns:
            Dict with average_fwci (actually median), fwci_percentile,
            papers_with_fwci, citation_percentile_min, citation_percentile_max.
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

        median_fwci = statistics.median(fwci_values) if fwci_values else None
        avg_cnp = sum(cnp_values) / len(cnp_values) if cnp_values else None

        return {
            "average_fwci": median_fwci,  # median used to avoid outlier inflation
            "fwci_percentile": avg_cnp,
            "papers_with_fwci": len(fwci_values),
            "citation_percentile_min": min(min_percentiles) if min_percentiles else None,
            "citation_percentile_max": max(max_percentiles) if max_percentiles else None,
        }

    async def get_remaining_budget_usd(self) -> float | None:
        """Return remaining daily API budget in USD, or None if unavailable.

        Requires API key. Uses the /rate-limit endpoint.
        """
        if not self.api_key:
            return None
        try:
            t0 = time.perf_counter()
            response = await self._http_client.get(
                f"{self.BASE_URL}/rate-limit",
                params={"api_key": self.api_key},
            )
            response.raise_for_status()
            data = response.json()
            rate_limit = data.get("rate_limit", {})
            remaining = rate_limit.get("daily_remaining_usd")
            _debug_log(
                location="app/services/openalex_client.py:get_remaining_budget_usd",
                message="OpenAlex /rate-limit completed",
                data={
                    "endpoint": "/rate-limit",
                    "api_key_present": True,
                    "daily_remaining_usd": float(remaining) if remaining is not None else None,
                    "elapsed_ms": int((time.perf_counter() - t0) * 1000),
                },
                run_id="post-fix",
                hypothesis_id="H_OA_HTTP",
            )
            return float(remaining) if remaining is not None else None
        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
            _debug_log(
                location="app/services/openalex_client.py:get_remaining_budget_usd",
                message="OpenAlex /rate-limit failed",
                data={"endpoint": "/rate-limit", "api_key_present": True, **_safe_httpx_err(e)},
                run_id="post-fix",
                hypothesis_id="H_OA_HTTP",
            )
            logger.warning("OpenAlex rate-limit check failed (%s)", type(e).__name__)
            return None
        except Exception as e:
            _debug_log(
                location="app/services/openalex_client.py:get_remaining_budget_usd",
                message="OpenAlex /rate-limit unexpected failure",
                data={
                    "endpoint": "/rate-limit",
                    "api_key_present": True,
                    "error_type": type(e).__name__,
                },
                run_id="post-fix",
                hypothesis_id="H_OA_HTTP",
            )
            logger.warning("OpenAlex rate-limit parse error (%s)", type(e).__name__)
            return None

    async def search_papers_semantic(
        self, query: str, limit: int | None = None
    ) -> list[dict]:
        """Search OpenAlex using semantic (embedding) search.

        Requires API key. Costs $0.01 per query.
        Returns papers ranked by semantic similarity.
        """
        if not self.api_key:
            logger.warning("Semantic search requires OpenAlex API key, falling back to keyword")
            return await self.search_papers(query, limit=limit or self.per_page)

        count = min(limit or self.per_page, 100)

        try:
            t0 = time.perf_counter()
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
            _debug_log(
                location="app/services/openalex_client.py:search_papers_semantic",
                message="OpenAlex /find/works semantic completed",
                data={
                    "endpoint": "/find/works",
                    "mode": "semantic",
                    "count": count,
                    "api_key_present": True,
                    "results_count": len(papers),
                    "elapsed_ms": int((time.perf_counter() - t0) * 1000),
                    **_q_fingerprint(query),
                },
                run_id="post-fix",
                hypothesis_id="H_OA_EMPTY",
            )
            return papers
        except (httpx.HTTPStatusError, httpx.TimeoutException, httpx.ConnectError) as e:
            _debug_log(
                location="app/services/openalex_client.py:search_papers_semantic",
                message="OpenAlex /find/works semantic failed",
                data={
                    "endpoint": "/find/works",
                    "mode": "semantic",
                    "count": count,
                    "api_key_present": True,
                    **_safe_httpx_err(e),
                    **_q_fingerprint(query),
                },
                run_id="post-fix",
                hypothesis_id="H_OA_HTTP",
            )
            logger.warning("OpenAlex semantic search error (%s)", type(e).__name__)
            return []
        except Exception as e:
            _debug_log(
                location="app/services/openalex_client.py:search_papers_semantic",
                message="OpenAlex /find/works semantic unexpected failure",
                data={
                    "endpoint": "/find/works",
                    "mode": "semantic",
                    "count": count,
                    "api_key_present": True,
                    "error_type": type(e).__name__,
                    **_q_fingerprint(query),
                },
                run_id="post-fix",
                hypothesis_id="H_OA_HTTP",
            )
            logger.error("Unexpected error in semantic search (%s)", type(e).__name__)
            return []

    async def close(self):
        """Close the underlying HTTP client."""
        await self._http_client.aclose()
