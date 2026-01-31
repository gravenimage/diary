"""Tests for data structure validation.

These tests ensure timeline.json and places.json have valid structure,
proper date formats, and reasonable coordinate values.
"""

import re
from datetime import datetime

import pytest

# Valid date pattern: YYYY-MM-DD
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Geographic bounds for Western Europe (where Edgar traveled)
BOUNDS = {
    "lat_min": 47.0,   # Southern France
    "lat_max": 54.0,   # Northern Germany/Netherlands
    "lng_min": -2.0,   # Western France/England
    "lng_max": 14.0,   # Eastern Germany
}


class TestTimelineStructure:
    """Tests for timeline.json structure."""

    def test_timeline_has_events(self, timeline_data: dict):
        """Timeline must have an events list."""
        assert "events" in timeline_data
        assert isinstance(timeline_data["events"], list)
        assert len(timeline_data["events"]) > 0

    def test_timeline_has_metadata(self, timeline_data: dict):
        """Timeline must have metadata."""
        assert "metadata" in timeline_data
        assert "date_range" in timeline_data["metadata"]

    @pytest.mark.parametrize("required_field", ["id", "name", "date", "type"])
    def test_events_have_required_fields(
        self, timeline_events: list[dict], required_field: str
    ):
        """Every event must have required fields."""
        for event in timeline_events:
            assert required_field in event, f"Event missing '{required_field}': {event.get('name', event)}"

    def test_event_ids_unique(self, timeline_events: list[dict]):
        """Event IDs must be unique."""
        ids = [e["id"] for e in timeline_events]
        duplicates = [id for id in ids if ids.count(id) > 1]
        assert len(duplicates) == 0, f"Duplicate event IDs: {set(duplicates)}"

    def test_event_types_valid(self, timeline_events: list[dict]):
        """Event type must be 'historical' or 'diary'."""
        valid_types = {"historical", "diary"}
        for event in timeline_events:
            assert event["type"] in valid_types, f"Invalid type '{event['type']}' for event: {event['name']}"


class TestTimelineDates:
    """Tests for date validity in timeline."""

    def test_dates_valid_format(self, timeline_events: list[dict]):
        """Dates must be in YYYY-MM-DD format."""
        for event in timeline_events:
            assert DATE_PATTERN.match(event["date"]), f"Invalid date format '{event['date']}' for: {event['name']}"
            if event.get("end_date"):
                assert DATE_PATTERN.match(event["end_date"]), f"Invalid end_date format for: {event['name']}"

    def test_dates_parseable(self, timeline_events: list[dict]):
        """Dates must be parseable as real dates."""
        for event in timeline_events:
            try:
                datetime.strptime(event["date"], "%Y-%m-%d")
            except ValueError:
                pytest.fail(f"Cannot parse date '{event['date']}' for: {event['name']}")

            if event.get("end_date"):
                try:
                    datetime.strptime(event["end_date"], "%Y-%m-%d")
                except ValueError:
                    pytest.fail(f"Cannot parse end_date '{event['end_date']}' for: {event['name']}")

    def test_end_date_after_start_date(self, timeline_events: list[dict]):
        """End date must be >= start date when present."""
        for event in timeline_events:
            if event.get("end_date"):
                start = datetime.strptime(event["date"], "%Y-%m-%d")
                end = datetime.strptime(event["end_date"], "%Y-%m-%d")
                assert end >= start, f"end_date before date for: {event['name']}"

    def test_dates_in_ww2_range(self, timeline_events: list[dict]):
        """Dates should be within WW2/post-war period (1939-1947)."""
        min_date = datetime(1939, 1, 1)
        max_date = datetime(1947, 12, 31)

        for event in timeline_events:
            date = datetime.strptime(event["date"], "%Y-%m-%d")
            assert min_date <= date <= max_date, f"Date {event['date']} outside WW2 range for: {event['name']}"


class TestPlacesStructure:
    """Tests for places.json structure."""

    def test_places_has_places(self, places_data: dict):
        """Places file must have a places list."""
        assert "places" in places_data
        assert isinstance(places_data["places"], list)
        assert len(places_data["places"]) > 0

    @pytest.mark.parametrize("required_field", ["id", "display_name", "lat", "lng", "country"])
    def test_places_have_required_fields(
        self, places: list[dict], required_field: str
    ):
        """Every place must have required fields."""
        for place in places:
            assert required_field in place, f"Place missing '{required_field}': {place.get('display_name', place)}"

    def test_place_ids_unique(self, places: list[dict]):
        """Place IDs must be unique."""
        ids = [p["id"] for p in places]
        duplicates = [id for id in ids if ids.count(id) > 1]
        assert len(duplicates) == 0, f"Duplicate place IDs: {set(duplicates)}"

    def test_places_have_keywords(self, places: list[dict]):
        """Every place should have keywords for text matching."""
        for place in places:
            assert "keywords" in place, f"Place missing keywords: {place['display_name']}"
            assert len(place["keywords"]) > 0, f"Place has empty keywords: {place['display_name']}"


class TestPlacesCoordinates:
    """Tests for coordinate validity."""

    def test_coordinates_are_numbers(self, places: list[dict]):
        """Coordinates must be numeric."""
        for place in places:
            assert isinstance(place["lat"], (int, float)), f"Invalid lat for: {place['display_name']}"
            assert isinstance(place["lng"], (int, float)), f"Invalid lng for: {place['display_name']}"

    def test_coordinates_in_bounds(self, places: list[dict]):
        """Coordinates must be within Western Europe bounds."""
        for place in places:
            lat, lng = place["lat"], place["lng"]
            assert BOUNDS["lat_min"] <= lat <= BOUNDS["lat_max"], (
                f"Latitude {lat} out of bounds for: {place['display_name']}"
            )
            assert BOUNDS["lng_min"] <= lng <= BOUNDS["lng_max"], (
                f"Longitude {lng} out of bounds for: {place['display_name']}"
            )

    def test_coordinates_not_zero(self, places: list[dict]):
        """Coordinates should not be exactly 0,0 (common error)."""
        for place in places:
            assert not (place["lat"] == 0 and place["lng"] == 0), (
                f"Coordinates are 0,0 for: {place['display_name']}"
            )
