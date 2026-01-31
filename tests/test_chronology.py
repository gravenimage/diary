"""Tests for chronological consistency.

These tests ensure the timeline is historically and logically consistent.
"""

from datetime import datetime

import pytest

# Key historical dates for validation
DDAY = datetime(1944, 6, 6)
VE_DAY = datetime(1945, 5, 8)
VJ_DAY = datetime(1945, 8, 15)
EDGAR_HOME = datetime(1946, 2, 18)


class TestTimelineOrder:
    """Tests for timeline ordering."""

    def test_events_sorted_by_date(self, timeline_events: list[dict]):
        """Events should be sorted by date."""
        dates = [datetime.strptime(e["date"], "%Y-%m-%d") for e in timeline_events]
        sorted_dates = sorted(dates)
        assert dates == sorted_dates, "Timeline events are not sorted by date"

    def test_no_duplicate_dates_same_type(self, timeline_events: list[dict]):
        """Same-type events on same date might indicate duplicates."""
        seen = set()
        duplicates = []
        for event in timeline_events:
            key = (event["date"], event["type"])
            if key in seen:
                duplicates.append(f"{event['date']} ({event['type']}): {event['name']}")
            seen.add(key)

        # This is a warning, not necessarily an error
        if duplicates:
            pytest.skip(f"Multiple same-type events on same date: {duplicates}")


class TestHistoricalDates:
    """Tests for historically accurate dates."""

    def test_dday_is_june_6_1944(self, historical_events: list[dict]):
        """D-Day event should be on June 6, 1944."""
        dday_events = [e for e in historical_events if e["id"] == "dday"]
        assert len(dday_events) == 1, "Should have exactly one D-Day event"
        assert dday_events[0]["date"] == "1944-06-06", "D-Day should be 1944-06-06"

    def test_ve_day_is_may_8_1945(self, historical_events: list[dict]):
        """VE Day event should be on May 8, 1945."""
        ve_events = [e for e in historical_events if e["id"] == "ve_day"]
        assert len(ve_events) == 1, "Should have exactly one VE Day event"
        assert ve_events[0]["date"] == "1945-05-08", "VE Day should be 1945-05-08"

    def test_vj_day_is_august_15_1945(self, historical_events: list[dict]):
        """VJ Day event should be on August 15, 1945."""
        vj_events = [e for e in historical_events if "japan" in e["id"]]
        assert len(vj_events) == 1, "Should have exactly one VJ Day event"
        assert vj_events[0]["date"] == "1945-08-15", "VJ Day should be 1945-08-15"


class TestDiaryChronology:
    """Tests for diary event chronological consistency."""

    def test_edgar_lands_after_dday(self, diary_events: list[dict]):
        """Edgar should land in France after D-Day."""
        landing = [e for e in diary_events if e["id"] == "edgar_lands"]
        if landing:
            landing_date = datetime.strptime(landing[0]["date"], "%Y-%m-%d")
            assert landing_date >= DDAY, "Edgar can't land before D-Day"

    def test_no_diary_events_before_dday(self, diary_events: list[dict]):
        """Diary events about France/Belgium/Germany should be after D-Day."""
        # Events before D-Day might be in England which is fine
        for event in diary_events:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d")
            # Skip if this could be an England-based event
            related = event.get("related_places", [])
            if any(p in ["middleton", "southampton", "dover"] for p in related):
                continue
            if event_date < DDAY:
                pytest.fail(f"Diary event '{event['name']}' on {event['date']} is before D-Day")

    def test_edgar_home_is_last_diary_event(self, diary_events: list[dict]):
        """Edgar arriving home should be the last diary event."""
        if not diary_events:
            pytest.skip("No diary events")

        sorted_events = sorted(
            diary_events,
            key=lambda e: datetime.strptime(e["date"], "%Y-%m-%d")
        )
        last_event = sorted_events[-1]

        # Either it's the "edgar_home" event or the date matches
        assert (
            last_event["id"] == "edgar_home" or
            last_event["date"] == "1946-02-18"
        ), f"Last diary event should be Edgar arriving home, got: {last_event['name']}"

    def test_diary_events_within_service_period(self, diary_events: list[dict]):
        """Diary events should be within Edgar's service period."""
        earliest_possible = datetime(1943, 1, 1)  # Some buffer before D-Day
        latest_possible = EDGAR_HOME

        for event in diary_events:
            event_date = datetime.strptime(event["date"], "%Y-%m-%d")
            assert earliest_possible <= event_date <= latest_possible, (
                f"Diary event '{event['name']}' on {event['date']} outside service period"
            )


class TestEventSequence:
    """Tests for logical event sequences."""

    def test_liberation_sequence(self, historical_events: list[dict]):
        """Liberation events should be in correct chronological order."""
        liberation_order = [
            "liberation_cherbourg",
            "liberation_paris",
            "liberation_brussels",
            "liberation_antwerp",
        ]

        liberation_events = {
            e["id"]: datetime.strptime(e["date"], "%Y-%m-%d")
            for e in historical_events
            if e["id"] in liberation_order
        }

        for i in range(len(liberation_order) - 1):
            id1, id2 = liberation_order[i], liberation_order[i + 1]
            if id1 in liberation_events and id2 in liberation_events:
                assert liberation_events[id1] < liberation_events[id2], (
                    f"{id1} should be before {id2}"
                )

    def test_bulge_sequence(self, historical_events: list[dict]):
        """Battle of the Bulge start should be before end."""
        bulge_events = {
            e["id"]: datetime.strptime(e["date"], "%Y-%m-%d")
            for e in historical_events
            if "bulge" in e["id"]
        }

        if "bulge_starts" in bulge_events and "bulge_ends" in bulge_events:
            assert bulge_events["bulge_starts"] < bulge_events["bulge_ends"], (
                "Battle of the Bulge should start before it ends"
            )

    def test_major_events_in_order(self, historical_events: list[dict]):
        """Major WW2 events should be in correct order."""
        major_order = ["dday", "ve_day", "japan_surrenders"]

        major_events = {
            e["id"]: datetime.strptime(e["date"], "%Y-%m-%d")
            for e in historical_events
            if e["id"] in major_order
        }

        for i in range(len(major_order) - 1):
            id1, id2 = major_order[i], major_order[i + 1]
            if id1 in major_events and id2 in major_events:
                assert major_events[id1] < major_events[id2], (
                    f"{id1} should be before {id2}"
                )
