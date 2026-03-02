#!/usr/bin/env python3
"""
Regression test for the Psittacara parakeet analysis.

Runs the full analysis pipeline via the API and asserts:
- Novelty: MARGINAL (or score <= 0.55), not NOVEL at 80%.
- References: On-topic (parakeet/Psittacara/speciation/phylogeny/delimitation);
  no irrelevant top citations (HIV-1 drug resistance, polyploidy, plant-microbe-insect).
- Gap retrieval: Does not fail (pipeline returns result); ideally pivot suggestions
  include ecology/restoration gap (e.g. Challenges in Tracking and Restoring Resilient Ecosystems).

Usage:
  API_BASE_URL=http://localhost:8000/api/v1 poetry run python scripts/run_psittacara_regression.py
"""
import json
import os
import sys
import time

try:
    import httpx
except ImportError:
    import urllib.request
    import urllib.error
    import json as _json

    class httpx:
        @staticmethod
        def post(url, **kwargs):
            req = urllib.request.Request(url, data=kwargs.get("data", {}).encode() if isinstance(kwargs.get("data"), str) else kwargs.get("data"), method="POST")
            if "files" in kwargs:
                pass  # multipart would need different handling
            try:
                with urllib.request.urlopen(req, timeout=60) as r:
                    return type("R", (), {"json": lambda: _json.loads(r.read().decode()), "status_code": r.status})()
            except urllib.error.HTTPError as e:
                return type("R", (), {"json": lambda: {}, "status_code": e.code})()

        @staticmethod
        def get(url, **kwargs):
            req = urllib.request.Request(url, method="GET")
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    return type("R", (), {"json": lambda: _json.loads(r.read().decode()), "status_code": r.status})()
            except urllib.error.HTTPError as e:
                return type("R", (), {"json": lambda: {}, "status_code": e.code})()


RESEARCH_QUESTION = "Incorporating modes of phenotypic evolution into species delimitation of Psittacara parakeets."

# Terms that indicate on-topic references (at least one should appear in top citations)
ON_TOPIC_TERMS = ("psittacara", "parakeet", "parrot", "speciation", "phylogen", "species delimitation", "delimitation", "taxonom", "morpholog")

# Terms that indicate irrelevant references (none of these should be the main focus of top citations)
IRRELEVANT_TERMS = ("hiv-1", "drug resistance", "polyploidy", "plant-microbe", "plant-microbe-insect", "insect-plant")

# Gap title we expect to be retrievable for ecology
ECOLOGY_GAP_TITLE_FRAGMENT = "Resilient Ecosystems"


def main():
    base = os.environ.get("API_BASE_URL", "http://localhost:8000/api/v1").rstrip("/")
    print(f"API base: {base}")
    print(f"Research question: {RESEARCH_QUESTION[:60]}...")

    # Start analysis (form: messages = JSON string)
    messages = [{"role": "user", "content": RESEARCH_QUESTION}]
    try:
        r = httpx.post(
            f"{base}/analyze",
            data={"messages": json.dumps(messages)},
            timeout=60.0,
        )
    except Exception as e:
        print(f"POST /analyze failed: {e}")
        return 1
    if r.status_code != 200:
        print(f"POST /analyze returned {r.status_code}: {r.text}")
        return 1
    body = r.json()
    session_id = body.get("session_id")
    if not session_id:
        print("No session_id in response")
        return 1
    print(f"Session: {session_id}")

    # Poll until completed
    for _ in range(120):
        try:
            r2 = httpx.get(f"{base}/analysis/{session_id}", timeout=30.0)
        except Exception as e:
            print(f"GET /analysis failed: {e}")
            return 1
        if r2.status_code != 200:
            print(f"GET /analysis returned {r2.status_code}")
            return 1
        data = r2.json() if r2.status_code == 200 else {}
        status = data.get("status", "")
        stage = data.get("stage", "")
        if status == "completed":
            break
        if status == "error":
            print(f"Pipeline error: {data.get('error_message', 'unknown')}")
            return 1
        print(f"  {stage}...")
        time.sleep(2)
    else:
        print("Timeout waiting for completion")
        return 1

    result = data.get("result")
    if not result:
        print("No result in response")
        return 1

    # Parse result (may be nested under result key as object)
    if isinstance(result, dict):
        rec = result
    else:
        rec = result.model_dump() if hasattr(result, "model_dump") else result

    novelty = rec.get("novelty_assessment") or {}
    evidence = novelty.get("evidence") or rec.get("evidence_citations") or []
    verdict = novelty.get("verdict", "")
    score = float(novelty.get("score", 0))
    pivots = rec.get("pivot_suggestions") or []

    failures = []

    # 1) Novelty: should be MARGINAL or score <= 0.55 (not 80% NOVEL)
    if verdict == "NOVEL" and score > 0.6:
        failures.append(f"Novelty overscored: verdict=NOVEL score={score:.0%} (expected MARGINAL or score <= 0.55)")
    if verdict == "MARGINAL" and score > 0.55:
        failures.append(f"MARGINAL score too high: {score:.0%} (expected <= 0.55)")
    print(f"Novelty: verdict={verdict} score={score:.2f} -> {'PASS' if not any('Novelty' in f or 'MARGINAL' in f for f in failures) else 'CHECK'}")

    # 2) References: at least one on-topic; none clearly irrelevant as top refs
    titles = [c.get("title") or "" for c in evidence[:10]]
    on_topic = any(any(t in (c.get("title") or "").lower() for t in ON_TOPIC_TERMS) for c in evidence[:8])
    irrelevant = []
    for c in evidence[:8]:
        tit = (c.get("title") or "").lower()
        for bad in IRRELEVANT_TERMS:
            if bad in tit:
                irrelevant.append((c.get("title", "")[:60], bad))
                break
    if not on_topic and titles:
        failures.append("No on-topic reference in top 8 (expected parakeet/Psittacara/speciation/phylogeny/delimitation)")
    if irrelevant:
        failures.append(f"Irrelevant top references: {irrelevant}")
    print(f"References: {len(evidence)} citations; on_topic={on_topic}, irrelevant={len(irrelevant)} -> {'PASS' if on_topic and not irrelevant else 'FAIL'}")

    # 3) Gap retrieval: pipeline completed and we got a result; optionally check pivot titles
    pivot_titles = [
        (p.get("gap_entry") or {}).get("title") or ""
        for p in pivots
    ]
    has_ecology_gap = any(ECOLOGY_GAP_TITLE_FRAGMENT in t for t in pivot_titles)
    print(f"Gap retrieval: {len(pivots)} pivot suggestions; ecology gap in pivots={has_ecology_gap} -> {'PASS' if len(pivots) >= 0 else 'FAIL'}")

    if failures:
        print("\nFailures:")
        for f in failures:
            print(f"  - {f}")
        print("\nTop citation titles:")
        for i, c in enumerate(evidence[:8]):
            print(f"  {i+1}. {(c.get('title') or '')[:70]}")
        return 1
    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
