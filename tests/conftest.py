"""Shared fixtures for diary tests."""

import json
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def timeline_data(project_root: Path) -> dict:
    """Load timeline.json data."""
    timeline_path = project_root / "data" / "timeline.json"
    with open(timeline_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def timeline_events(timeline_data: dict) -> list[dict]:
    """Return list of all timeline events."""
    return timeline_data["events"]


@pytest.fixture(scope="session")
def historical_events(timeline_events: list[dict]) -> list[dict]:
    """Return only historical events."""
    return [e for e in timeline_events if e["type"] == "historical"]


@pytest.fixture(scope="session")
def diary_events(timeline_events: list[dict]) -> list[dict]:
    """Return only diary events."""
    return [e for e in timeline_events if e["type"] == "diary"]


@pytest.fixture(scope="session")
def places_data(project_root: Path) -> dict:
    """Load places.json data."""
    places_path = project_root / "places.json"
    with open(places_path, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="session")
def places(places_data: dict) -> list[dict]:
    """Return list of all places."""
    return places_data["places"]


@pytest.fixture(scope="session")
def place_ids(places: list[dict]) -> set[str]:
    """Return set of all valid place IDs."""
    return {p["id"] for p in places}
