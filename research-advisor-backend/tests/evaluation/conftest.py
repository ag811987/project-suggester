"""Shared fixtures for evaluation tests."""

import json
from pathlib import Path

import pytest

BENCHMARKS_DIR = Path(__file__).parent / "benchmarks"


@pytest.fixture
def novelty_benchmark():
    """Load novelty benchmark dataset."""
    path = BENCHMARKS_DIR / "novelty_benchmark.json"
    with open(path) as f:
        return json.load(f)


@pytest.fixture
def default_mock_papers():
    """Default papers for mocked OpenAlex (medium FWCI)."""
    return [
        {
            "id": "https://openalex.org/W1001",
            "title": "Related Paper 1",
            "doi": "10.1234/rel1",
            "fwci": 1.2,
            "citation_normalized_percentile": 0.65,
            "cited_by_percentile_year_min": 55,
            "cited_by_percentile_year_max": 70,
            "authors": ["Author A"],
            "publication_year": 2023,
            "cited_by_count": 60,
        },
        {
            "id": "https://openalex.org/W1002",
            "title": "Related Paper 2",
            "doi": "10.1234/rel2",
            "fwci": 1.0,
            "citation_normalized_percentile": 0.55,
            "cited_by_percentile_year_min": 45,
            "cited_by_percentile_year_max": 60,
            "authors": ["Author B"],
            "publication_year": 2022,
            "cited_by_count": 40,
        },
    ]
