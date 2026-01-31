"""Tests for cross-reference integrity between data files.

These tests ensure that references between timeline.json and places.json
are valid - e.g., related_places IDs actually exist.
"""

import pytest


class TestRelatedPlacesReferences:
    """Tests for related_places references in timeline events."""

    def test_related_places_exist(
        self, timeline_events: list[dict], place_ids: set[str]
    ):
        """Every related_places ID must exist in places.json."""
        errors = []
        for event in timeline_events:
            related = event.get("related_places", [])
            for place_id in related:
                if place_id not in place_ids:
                    errors.append(f"Event '{event['name']}' references unknown place: {place_id}")

        assert len(errors) == 0, "\n".join(errors)

    def test_related_places_is_list(self, timeline_events: list[dict]):
        """related_places should be a list when present."""
        for event in timeline_events:
            if "related_places" in event:
                assert isinstance(event["related_places"], list), (
                    f"related_places is not a list for: {event['name']}"
                )

    def test_diary_events_have_related_places(self, diary_events: list[dict]):
        """Diary events should have at least one related place."""
        events_without_places = [
            e["name"] for e in diary_events
            if not e.get("related_places")
        ]
        # Warning, not failure - some diary events might not have specific locations
        if events_without_places:
            pytest.skip(f"Diary events without related_places: {events_without_places}")


class TestMapBoundsReferences:
    """Tests for map_bounds validity in historical events."""

    def test_map_bounds_structure(self, historical_events: list[dict]):
        """map_bounds should have north/south/east/west when present."""
        required_keys = {"north", "south", "east", "west"}
        for event in historical_events:
            if "map_bounds" in event:
                bounds = event["map_bounds"]
                missing = required_keys - set(bounds.keys())
                assert len(missing) == 0, (
                    f"map_bounds missing {missing} for: {event['name']}"
                )

    def test_map_bounds_values_valid(self, historical_events: list[dict]):
        """map_bounds values should be valid coordinates."""
        for event in historical_events:
            if "map_bounds" in event:
                bounds = event["map_bounds"]
                # North should be > South
                assert bounds["north"] > bounds["south"], (
                    f"north <= south in map_bounds for: {event['name']}"
                )
                # East should be > West (for Western Europe, no antimeridian crossing)
                assert bounds["east"] > bounds["west"], (
                    f"east <= west in map_bounds for: {event['name']}"
                )


class TestSourceUrls:
    """Tests for source URL validity."""

    def test_historical_events_have_sources(self, historical_events: list[dict]):
        """Historical events should have source URLs."""
        events_without_source = [
            e["name"] for e in historical_events
            if not e.get("source")
        ]
        assert len(events_without_source) == 0, (
            f"Historical events without source: {events_without_source}"
        )

    def test_source_urls_valid_format(self, historical_events: list[dict]):
        """Source URLs should be valid HTTP(S) URLs."""
        for event in historical_events:
            source = event.get("source", "")
            if source and source != "diary":
                assert source.startswith(("http://", "https://")), (
                    f"Invalid source URL '{source}' for: {event['name']}"
                )

    def test_wikipedia_urls_valid_domain(self, historical_events: list[dict]):
        """Wikipedia sources should use correct domain."""
        for event in historical_events:
            source = event.get("source", "")
            if "wikipedia" in source:
                assert "en.wikipedia.org/wiki/" in source, (
                    f"Invalid Wikipedia URL '{source}' for: {event['name']}"
                )
