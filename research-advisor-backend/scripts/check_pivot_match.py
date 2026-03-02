#!/usr/bin/env python3
"""Call the analyze API, wait for completion, and print gap retrieval / pivot matching outcome."""
import json
import os
import sys
import time

for path in [os.path.join(os.path.dirname(__file__), "..", ".env"), os.path.join(os.path.dirname(__file__), "..", "..", ".env"), ".env"]:
    if os.path.isfile(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    k, v = k.strip(), v.strip().strip('"').strip("'")
                    if k and k not in os.environ:
                        os.environ[k] = v
        break

import httpx

BASE = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000/api/v1").rstrip("/")
QUESTION = "Incorporating modes of phenotypic evolution into species delimitation of Psittacara parakeets."
ECOLOGY_GAP = "Resilient Ecosystems"

def main():
    print("Calling POST /analyze ...")
    r = httpx.post(f"{BASE}/analyze", data={"messages": json.dumps([{"role": "user", "content": QUESTION}])}, timeout=60)
    if r.status_code != 200:
        print("POST failed:", r.status_code, r.text)
        return 1
    session_id = r.json().get("session_id")
    if not session_id:
        print("No session_id")
        return 1
    print("Session:", session_id)

    for _ in range(120):
        r2 = httpx.get(f"{BASE}/analysis/{session_id}", timeout=30)
        if r2.status_code != 200:
            print("GET failed:", r2.status_code)
            return 1
        data = r2.json()
        status = data.get("status")
        stage = data.get("stage", "")
        if status == "completed":
            break
        if status == "error":
            print("Pipeline error:", data.get("error_message"))
            return 1
        print("  ", stage)
        time.sleep(2)
    else:
        print("Timeout")
        return 1

    result = data.get("result")
    if not result:
        print("No result")
        return 1
    rec = result if isinstance(result, dict) else (result.model_dump() if hasattr(result, "model_dump") else result)
    pivots = rec.get("pivot_suggestions") or []
    novelty = rec.get("novelty_assessment") or {}
    verdict = novelty.get("verdict", "")

    print("\n--- Pivot matching ---")
    print("Verdict:", verdict)
    print("Number of pivot suggestions:", len(pivots))
    if pivots:
        for i, p in enumerate(pivots, 1):
            print(f"  {i}. {p.get('title', '')[:65]}")
            print(f"     URL: {p.get('source_url', '')}")
        has_ecology = any(ECOLOGY_GAP in (p.get("title") or "") for p in pivots)
        print("\nEcology gap (Resilient Ecosystems) in suggestions:", has_ecology)
    else:
        print("(No pivot suggestions returned.)")
    return 0

if __name__ == "__main__":
    sys.exit(main())
