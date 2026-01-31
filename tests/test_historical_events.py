"""Tests for historical event data quality.

These tests ensure historical events have complete, high-quality content
including summaries, key facts, and map data.
"""

import pytest

# Minimum content lengths for quality checks
MIN_SUMMARY_LENGTH = 100
MIN_DESCRIPTION_LENGTH = 20
MIN_KEY_FACTS = 2
MAX_KEY_FACTS = 6


class TestHistoricalEventContent:
    """Tests for historical event content quality."""

    def test_historical_events_have_summaries(self, historical_events: list[dict]):
        """Historical events should have Wikipedia summaries."""
        events_without_summary = [
            e["name"] for e in historical_events
            if not e.get("summary")
        ]
        assert len(events_without_summary) == 0, (
            f"Historical events without summary: {events_without_summary}"
        )

    def test_summaries_minimum_length(self, historical_events: list[dict]):
        """Summaries should be at least {MIN_SUMMARY_LENGTH} characters."""
        short_summaries = []
        for event in historical_events:
            summary = event.get("summary", "")
            if len(summary) < MIN_SUMMARY_LENGTH:
                short_summaries.append(f"{event['name']} ({len(summary)} chars)")

        assert len(short_summaries) == 0, (
            f"Summaries too short (min {MIN_SUMMARY_LENGTH}): {short_summaries}"
        )

    def test_descriptions_not_empty(self, historical_events: list[dict]):
        """Events should have descriptions."""
        for event in historical_events:
            desc = event.get("description", "")
            assert len(desc) >= MIN_DESCRIPTION_LENGTH, (
                f"Description too short for: {event['name']}"
            )


class TestHistoricalEventKeyFacts:
    """Tests for key_facts quality."""

    def test_historical_events_have_key_facts(self, historical_events: list[dict]):
        """Historical events should have key_facts list."""
        events_without_facts = [
            e["name"] for e in historical_events
            if not e.get("key_facts")
        ]
        assert len(events_without_facts) == 0, (
            f"Historical events without key_facts: {events_without_facts}"
        )

    def test_key_facts_minimum_count(self, historical_events: list[dict]):
        """Should have at least {MIN_KEY_FACTS} key facts."""
        too_few_facts = []
        for event in historical_events:
            facts = event.get("key_facts", [])
            if len(facts) < MIN_KEY_FACTS:
                too_few_facts.append(f"{event['name']} ({len(facts)} facts)")

        assert len(too_few_facts) == 0, (
            f"Too few key_facts (min {MIN_KEY_FACTS}): {too_few_facts}"
        )

    def test_key_facts_maximum_count(self, historical_events: list[dict]):
        """Should have at most {MAX_KEY_FACTS} key facts (for UI)."""
        too_many_facts = []
        for event in historical_events:
            facts = event.get("key_facts", [])
            if len(facts) > MAX_KEY_FACTS:
                too_many_facts.append(f"{event['name']} ({len(facts)} facts)")

        assert len(too_many_facts) == 0, (
            f"Too many key_facts (max {MAX_KEY_FACTS}): {too_many_facts}"
        )

    def test_key_facts_not_empty_strings(self, historical_events: list[dict]):
        """Key facts should not be empty strings."""
        for event in historical_events:
            for i, fact in enumerate(event.get("key_facts", [])):
                assert fact.strip(), (
                    f"Empty key_fact[{i}] for: {event['name']}"
                )

    def test_key_facts_reasonable_length(self, historical_events: list[dict]):
        """Key facts should be concise (10-150 chars)."""
        issues = []
        for event in historical_events:
            for i, fact in enumerate(event.get("key_facts", [])):
                if len(fact) < 10:
                    issues.append(f"{event['name']} fact[{i}] too short: '{fact}'")
                elif len(fact) > 150:
                    issues.append(f"{event['name']} fact[{i}] too long: {len(fact)} chars")

        assert len(issues) == 0, "\n".join(issues)


class TestHistoricalEventMaps:
    """Tests for map data in historical events."""

    def test_historical_events_have_map_bounds(self, historical_events: list[dict]):
        """Historical events should have map_bounds for the mini map."""
        events_without_bounds = [
            e["name"] for e in historical_events
            if not e.get("map_bounds")
        ]
        assert len(events_without_bounds) == 0, (
            f"Historical events without map_bounds: {events_without_bounds}"
        )

    def test_map_bounds_reasonable_size(self, historical_events: list[dict]):
        """Map bounds should cover a reasonable area (not too big or small)."""
        issues = []
        for event in historical_events:
            bounds = event.get("map_bounds")
            if not bounds:
                continue

            lat_span = bounds["north"] - bounds["south"]
            lng_span = bounds["east"] - bounds["west"]

            # Check for very small areas (< 0.1 degrees ~ 10km)
            if lat_span < 0.1 or lng_span < 0.1:
                issues.append(f"{event['name']}: bounds too small ({lat_span:.2f} x {lng_span:.2f})")

            # Check for very large areas (> 10 degrees ~ 1000km)
            if lat_span > 10 or lng_span > 10:
                issues.append(f"{event['name']}: bounds too large ({lat_span:.2f} x {lng_span:.2f})")

        assert len(issues) == 0, "\n".join(issues)


class TestDiaryEventContent:
    """Tests for diary event content quality."""

    def test_diary_events_have_descriptions(self, diary_events: list[dict]):
        """Diary events should have descriptions."""
        for event in diary_events:
            assert event.get("description"), f"Missing description for: {event['name']}"

    def test_diary_events_source_is_diary(self, diary_events: list[dict]):
        """Diary events should have source='diary'."""
        for event in diary_events:
            assert event.get("source") == "diary", (
                f"Diary event has wrong source '{event.get('source')}': {event['name']}"
            )
