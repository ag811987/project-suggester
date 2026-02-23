# FWCI Calibration for Research Pivot Advisor

## Problem

OpenAlex Field-Weighted Citation Impact (FWCI) tends to produce **inflated scores** compared to other bibliometric databases (e.g., SciVal, Web of Science, Scopus). In our system, this led to most research areas receiving HIGH impact scores, reducing the discriminative power of the metric.

## Why OpenAlex FWCI Differs

From [OpenAlex documentation](https://help.openalex.org/hc/en-us/articles/24735753007895-Field-Weighted-Citation-Impact-FWCI) and empirical research:

1. **Publication date**: OpenAlex uses online publication date rather than periodical date, which can shift the year of publication and thus the expected citation baseline.

2. **Subfield classification**: OpenAlex classifies works by analyzing their **text content** rather than using the journal's primary field. This leads to different expected citation values than journal-level classifiers.

3. **Database comprehensiveness**: OpenAlex includes many uncited works. This drives down the average expected citations, so works that *do* get cited appear to have **higher FWCI values** in OpenAlex.

4. **Empirical comparison**: Research comparing OpenAlex FWCI to SciVal found OpenAlex's mean FWCI was **1.5–1.7× higher** than SciVal, primarily due to broader field definitions.

## Our Calibration Approach

### Configurable Thresholds

We use configurable thresholds (via `FWCI_HIGH_THRESHOLD` and `FWCI_LOW_THRESHOLD`) instead of the raw Snowball Metrics defaults:

| Level  | Raw Snowball (1.0 baseline) | Our Default (calibrated) | Rationale                          |
|--------|-----------------------------|--------------------------|------------------------------------|
| HIGH   | > 1.5                       | > 2.2                    | Stricter; only truly high-impact   |
| MEDIUM | 0.8 – 1.5                   | 1.2 – 2.2                | Narrower band                      |
| LOW    | < 0.8                       | < 1.2                    | Catches more marginal research     |

### Environment Variables

```bash
# Optional: Override defaults (see .env.example)
FWCI_HIGH_THRESHOLD=2.2   # Default: 2.2
FWCI_LOW_THRESHOLD=1.2    # Default: 1.2
```

### Legacy Thresholds (for testing)

Tests use the legacy thresholds (1.5, 0.8) to preserve existing test expectations. Production should use the stricter defaults.

## Search Relevance & FWCI Robustness

For **niche topics** (e.g., "speciation in Psittacula parakeets"), the default OpenAlex search can return broad, highly-cited classics that mention "speciation" or "ecology" in fulltext but aren't actually about the topic. This inflates FWCI.

**Mitigations implemented:**

1. **Title-and-abstract search**: We use `filter=title_and_abstract.search` instead of the default fulltext search, so papers must mention the topic in title or abstract.

2. **Specific key_concepts**: The decomposition prompt instructs the LLM to preserve genus/species names and specific terms (e.g., "Psittacula", "parakeet") in `key_concepts`, and we prefer those for the search query over broad terms like "speciation" alone.

3. **Tight search (3–10 results)**: We fetch fewer papers (default 8) via `OPENALEX_SEARCH_LIMIT`. Long lists tend to include tangentially related highly-cited papers; fewer results keep the set more closely related.

4. **Median instead of mean**: We use the **median** FWCI for impact assessment, not the average. This avoids outlier inflation when a few tangentially related classics slip through.

## Further Research Needed

1. **Empirical validation**: Run our system on a labeled set of research questions with known impact (e.g., from expert assessment) and tune thresholds to maximize discrimination.

2. **Field-specific calibration**: FWCI inflation may vary by field. Consider field-specific multipliers or thresholds.

3. **Percentile-based fallback**: When average FWCI is misleading (e.g., few papers, high variance), consider using `citation_normalized_percentile` or `cited_by_percentile_year` as supplementary signals.

4. **LLM override**: Our prompts instruct the LLM to use FWCI as *evidence*, not the sole rule. The LLM can override when justified (e.g., emerging fields with few citations but high potential).

## References

- [OpenAlex FWCI Help](https://help.openalex.org/hc/en-us/articles/24735753007895-Field-Weighted-Citation-Impact-FWCI)
- [Snowball Metrics Recipe Book](https://arma.ac.uk/wp-content/uploads/2021/08/Snowball-Metrics-Recipe-Book-edition-2.pdf)
- Springer (2025): "How similar are field-normalized citation impact scores obtained from OpenAlex and three popular commercial databases?"
