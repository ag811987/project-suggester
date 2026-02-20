"""Tests for GapMapRepository database operations."""

import pytest
from datetime import datetime

from app.services.gap_map_repository import GapMapRepository
from app.models.schemas import GapMapEntry as GapMapEntrySchema


class TestGapMapRepository:
    """Tests for GapMapRepository CRUD operations."""

    async def test_upsert_inserts_new_entries(self, test_db_session, sample_gap_map_entries):
        """Test that upsert inserts new entries into an empty table."""
        repo = GapMapRepository(test_db_session)
        count = await repo.upsert(sample_gap_map_entries)
        assert count == 3

    async def test_upsert_updates_existing_entry(self, test_db_session, sample_gap_map_entries):
        """Test that upsert updates an entry with matching source_url."""
        repo = GapMapRepository(test_db_session)
        # Insert first time
        await repo.upsert(sample_gap_map_entries)

        # Modify entry and upsert again (same source_url)
        updated = [
            GapMapEntrySchema(
                title="Updated Title",
                description="Updated description",
                source="convergent",
                source_url="https://www.gap-map.org/entry/1",
                category="Updated Category",
                tags=["updated"],
            )
        ]
        count = await repo.upsert(updated)
        assert count == 1

        # Verify the update took effect
        entries = await repo.get_by_source("convergent")
        found = [e for e in entries if e.source_url == "https://www.gap-map.org/entry/1"]
        assert len(found) == 1
        assert found[0].title == "Updated Title"
        assert found[0].description == "Updated description"
        assert found[0].category == "Updated Category"

    async def test_upsert_does_not_duplicate(self, test_db_session, sample_gap_map_entries):
        """Test that upserting same entries twice doesn't create duplicates."""
        repo = GapMapRepository(test_db_session)
        await repo.upsert(sample_gap_map_entries)
        await repo.upsert(sample_gap_map_entries)
        entries = await repo.get_all()
        assert len(entries) == 3

    async def test_get_all(self, test_db_session, sample_gap_map_entries):
        """Test get_all returns all entries."""
        repo = GapMapRepository(test_db_session)
        await repo.upsert(sample_gap_map_entries)
        entries = await repo.get_all()
        assert len(entries) == 3

    async def test_get_all_empty(self, test_db_session):
        """Test get_all on empty database returns empty list."""
        repo = GapMapRepository(test_db_session)
        entries = await repo.get_all()
        assert entries == []

    async def test_get_by_category(self, test_db_session, sample_gap_map_entries):
        """Test filtering entries by category."""
        repo = GapMapRepository(test_db_session)
        await repo.upsert(sample_gap_map_entries)
        biotech_entries = await repo.get_by_category("Biotech")
        assert len(biotech_entries) == 2
        assert all(e.category == "Biotech" for e in biotech_entries)

    async def test_get_by_category_no_match(self, test_db_session, sample_gap_map_entries):
        """Test filtering by non-existent category returns empty list."""
        repo = GapMapRepository(test_db_session)
        await repo.upsert(sample_gap_map_entries)
        entries = await repo.get_by_category("NonExistent")
        assert entries == []

    async def test_get_by_source(self, test_db_session, sample_gap_map_entries):
        """Test filtering entries by source."""
        repo = GapMapRepository(test_db_session)
        await repo.upsert(sample_gap_map_entries)
        convergent_entries = await repo.get_by_source("convergent")
        assert len(convergent_entries) == 2
        assert all(e.source == "convergent" for e in convergent_entries)

    async def test_get_by_source_single(self, test_db_session, sample_gap_map_entries):
        """Test filtering by source with single match."""
        repo = GapMapRepository(test_db_session)
        await repo.upsert(sample_gap_map_entries)
        homeworld_entries = await repo.get_by_source("homeworld")
        assert len(homeworld_entries) == 1
        assert homeworld_entries[0].source == "homeworld"

    async def test_get_by_source_empty(self, test_db_session):
        """Test filtering by source on empty database."""
        repo = GapMapRepository(test_db_session)
        entries = await repo.get_by_source("convergent")
        assert entries == []

    async def test_upsert_sets_scraped_at(self, test_db_session, sample_gap_map_entries):
        """Test that upsert sets scraped_at timestamp."""
        repo = GapMapRepository(test_db_session)
        await repo.upsert(sample_gap_map_entries)
        entries = await repo.get_all()
        for entry in entries:
            assert entry.scraped_at is not None
            assert isinstance(entry.scraped_at, datetime)
