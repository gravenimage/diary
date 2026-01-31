#!/usr/bin/env python3
"""
Research historical events for the WW2 diary timeline.

This is a one-time helper script to research and generate initial
historical events data. The output can be manually reviewed and
edited before adding to data/timeline.json.

Usage:
    uv run scripts/research_events.py
"""

import json
from pathlib import Path
from datetime import datetime

# Key WW2 events relevant to Edgar's journey (Western Front focus)
# These are pre-researched events - in a production system this could
# fetch from Wikipedia API or other sources

HISTORICAL_EVENTS = [
    {
        "id": "dday",
        "name": "D-Day (Operation Overlord)",
        "date": "1944-06-06",
        "end_date": None,
        "type": "historical",
        "description": "Allied invasion of Normandy begins. The largest seaborne invasion in history.",
        "source": "https://en.wikipedia.org/wiki/Normandy_landings",
        "related_places": ["crepon", "le_hamel", "arromanches"]
    },
    {
        "id": "liberation_cherbourg",
        "name": "Liberation of Cherbourg",
        "date": "1944-06-26",
        "end_date": "1944-06-27",
        "type": "historical",
        "description": "Major port of Cherbourg captured by US forces, providing crucial supply capabilities.",
        "source": "https://en.wikipedia.org/wiki/Battle_of_Cherbourg",
        "related_places": []
    },
    {
        "id": "caen_bombing",
        "name": "Bombing of Caen (Operation Charnwood)",
        "date": "1944-07-08",
        "end_date": None,
        "type": "historical",
        "description": "Over 500 Lancasters and Halifaxes bomb Caen. Edgar witnessed this from his position.",
        "source": "https://en.wikipedia.org/wiki/Operation_Charnwood",
        "related_places": ["caen", "crepon"]
    },
    {
        "id": "falaise_pocket",
        "name": "Falaise Pocket closes",
        "date": "1944-08-21",
        "end_date": None,
        "type": "historical",
        "description": "German forces trapped and destroyed in the Falaise Pocket, ending the Battle of Normandy.",
        "source": "https://en.wikipedia.org/wiki/Falaise_pocket",
        "related_places": ["falaise", "argentan"]
    },
    {
        "id": "liberation_paris",
        "name": "Liberation of Paris",
        "date": "1944-08-25",
        "end_date": None,
        "type": "historical",
        "description": "Paris liberated after four years of German occupation.",
        "source": "https://en.wikipedia.org/wiki/Liberation_of_Paris",
        "related_places": []
    },
    {
        "id": "liberation_brussels",
        "name": "Liberation of Brussels",
        "date": "1944-09-03",
        "end_date": None,
        "type": "historical",
        "description": "Brussels liberated by British forces.",
        "source": "https://en.wikipedia.org/wiki/Liberation_of_Belgium",
        "related_places": ["brussels"]
    },
    {
        "id": "liberation_antwerp",
        "name": "Liberation of Antwerp",
        "date": "1944-09-04",
        "end_date": None,
        "type": "historical",
        "description": "Antwerp liberated, though the port would not be usable until the Scheldt was cleared.",
        "source": "https://en.wikipedia.org/wiki/Antwerp_in_World_War_II",
        "related_places": ["antwerp"]
    },
    {
        "id": "scheldt_battle",
        "name": "Battle of the Scheldt",
        "date": "1944-10-02",
        "end_date": "1944-11-08",
        "type": "historical",
        "description": "Allied campaign to open shipping route to Antwerp. Edgar's unit fired at German positions at Knokke.",
        "source": "https://en.wikipedia.org/wiki/Battle_of_the_Scheldt",
        "related_places": ["knokke", "goes", "zuid_beveland"]
    },
    {
        "id": "bulge_starts",
        "name": "Battle of the Bulge begins",
        "date": "1944-12-16",
        "end_date": None,
        "type": "historical",
        "description": "Last major German offensive on the Western Front.",
        "source": "https://en.wikipedia.org/wiki/Battle_of_the_Bulge",
        "related_places": []
    },
    {
        "id": "bulge_ends",
        "name": "Battle of the Bulge ends",
        "date": "1945-01-25",
        "end_date": None,
        "type": "historical",
        "description": "German offensive repulsed with heavy losses on both sides.",
        "source": "https://en.wikipedia.org/wiki/Battle_of_the_Bulge",
        "related_places": []
    },
    {
        "id": "rhine_crossing",
        "name": "Crossing of the Rhine (Operation Plunder)",
        "date": "1945-03-22",
        "end_date": "1945-03-24",
        "type": "historical",
        "description": "Allied forces cross the Rhine River into the German heartland.",
        "source": "https://en.wikipedia.org/wiki/Operation_Plunder",
        "related_places": ["wesel"]
    },
    {
        "id": "ve_day",
        "name": "VE Day",
        "date": "1945-05-08",
        "end_date": None,
        "type": "historical",
        "description": "Victory in Europe. Edgar witnessed celebrations at Kapelle.",
        "source": "https://en.wikipedia.org/wiki/Victory_in_Europe_Day",
        "related_places": ["kapelle", "antwerp"]
    },
    {
        "id": "berlin_victory_parade",
        "name": "Berlin Victory Parade",
        "date": "1945-07-21",
        "end_date": None,
        "type": "historical",
        "description": "Allied victory parade through Berlin.",
        "source": "https://en.wikipedia.org/wiki/Berlin_Victory_Parade_of_1945",
        "related_places": ["berlin", "brunswick"]
    },
    {
        "id": "japan_surrenders",
        "name": "Japan surrenders (VJ Day)",
        "date": "1945-08-15",
        "end_date": None,
        "type": "historical",
        "description": "World War II officially ends with Japanese surrender.",
        "source": "https://en.wikipedia.org/wiki/Victory_over_Japan_Day",
        "related_places": []
    }
]

# Key diary milestones extracted from Edgar's diary
DIARY_EVENTS = [
    {
        "id": "edgar_lands",
        "name": "Edgar lands in France",
        "date": "1944-06-07",
        "end_date": None,
        "type": "diary",
        "description": "Edgar arrives at Crepon gun site at 12:45am, D-Day+1. First night on French soil.",
        "source": "diary",
        "related_places": ["crepon", "le_hamel"]
    },
    {
        "id": "edgar_leaves_normandy",
        "name": "Edgar leaves Normandy",
        "date": "1944-08-31",
        "end_date": None,
        "type": "diary",
        "description": "200-mile journey from Crepon through devastated Falaise to Amiens.",
        "source": "diary",
        "related_places": ["crepon", "falaise", "argentan", "laigle", "amiens"]
    },
    {
        "id": "calais_bombing",
        "name": "Edgar watches Calais bombing",
        "date": "1944-09-26",
        "end_date": None,
        "type": "diary",
        "description": "Watched Lancasters and Halifaxes bombing Calais from Boulogne with no opposition.",
        "source": "diary",
        "related_places": ["boulogne", "calais"]
    },
    {
        "id": "edgar_birthday",
        "name": "Edgar's birthday in Belgium",
        "date": "1944-10-17",
        "end_date": None,
        "type": "diary",
        "description": "Edgar arrives in Bruges on his birthday despite terrible weather.",
        "source": "diary",
        "related_places": ["bruges"]
    },
    {
        "id": "edgar_zuid_beveland",
        "name": "Edgar arrives at Zuid Beveland",
        "date": "1944-11-04",
        "end_date": None,
        "type": "diary",
        "description": "Gun position on a bleak dyke in front of the sea. Very cold winter ahead.",
        "source": "diary",
        "related_places": ["zuid_beveland", "goes"]
    },
    {
        "id": "edgar_first_leave",
        "name": "Edgar's first leave",
        "date": "1945-01-15",
        "end_date": "1945-01-27",
        "type": "diary",
        "description": "Long-awaited leave to see Winnie. Hard seats and no heating on the train.",
        "source": "diary",
        "related_places": ["middleton"]
    },
    {
        "id": "edgar_brussels_leave",
        "name": "48-hour leave in Brussels",
        "date": "1945-02-18",
        "end_date": "1945-02-20",
        "type": "diary",
        "description": "Stay at the Albert Hotel with conducted tour of the city. V-1 air raid warnings.",
        "source": "diary",
        "related_places": ["brussels"]
    },
    {
        "id": "cease_firing",
        "name": "Cease Firing order",
        "date": "1945-04-17",
        "end_date": None,
        "type": "diary",
        "description": "Edgar's unit receives Cease Firing order. End of AA operations.",
        "source": "diary",
        "related_places": ["kapelle", "nieuport"]
    },
    {
        "id": "collaborators",
        "name": "Ransacking of collaborators' houses",
        "date": "1945-05-13",
        "end_date": None,
        "type": "diary",
        "description": "Edgar witnessed crowds ransacking the houses of Nazi collaborators at Kapelle.",
        "source": "diary",
        "related_places": ["kapelle"]
    },
    {
        "id": "edgar_leaves_belgium",
        "name": "Edgar leaves for Germany",
        "date": "1945-06-21",
        "end_date": None,
        "type": "diary",
        "description": "Journey to Berlin through devastated German cities. Wesel and Munster were 'heaps of rubble'.",
        "source": "diary",
        "related_places": ["louvain", "wesel", "munster", "bielefeld", "brunswick"]
    },
    {
        "id": "edgar_berlin",
        "name": "Edgar arrives in Berlin",
        "date": "1945-07-01",
        "end_date": None,
        "type": "diary",
        "description": "Final posting. Best bed in his army career, but city in ruins with 'whiff of dead people'.",
        "source": "diary",
        "related_places": ["berlin"]
    },
    {
        "id": "edgar_demob",
        "name": "Edgar leaves Berlin for demob",
        "date": "1946-02-13",
        "end_date": None,
        "type": "diary",
        "description": "Final journey home begins. Left Berlin Transit Camp at 7:40am.",
        "source": "diary",
        "related_places": ["berlin", "hanover"]
    },
    {
        "id": "edgar_home",
        "name": "Edgar arrives home",
        "date": "1946-02-18",
        "end_date": None,
        "type": "diary",
        "description": "Arrived home at 4:30am after long journey via Dover, Reading, Hereford, and Crewe.",
        "source": "diary",
        "related_places": ["dover", "middleton"]
    }
]


def sort_events(events: list[dict]) -> list[dict]:
    """Sort events by date."""
    return sorted(events, key=lambda e: e["date"])


def generate_timeline() -> dict:
    """Generate the complete timeline data structure."""
    all_events = HISTORICAL_EVENTS + DIARY_EVENTS
    sorted_events = sort_events(all_events)

    return {
        "events": sorted_events,
        "metadata": {
            "date_range": {
                "start": "1943-12-01",
                "end": "1946-02-18"
            },
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "notes": "Timeline events derived from Edgar Hopkins' WW2 diary and historical sources. Dates cross-referenced with diary text where possible."
        }
    }


def main():
    base_dir = Path(__file__).parent.parent
    output_path = base_dir / "data" / "timeline.json"

    # Ensure data directory exists
    output_path.parent.mkdir(exist_ok=True)

    print("Generating timeline data...")
    timeline = generate_timeline()

    print(f"  Found {len(timeline['events'])} total events:")
    historical = [e for e in timeline['events'] if e['type'] == 'historical']
    diary = [e for e in timeline['events'] if e['type'] == 'diary']
    print(f"    - {len(historical)} historical events")
    print(f"    - {len(diary)} diary milestones")

    print(f"\nWriting to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(timeline, f, indent=2, ensure_ascii=False)

    print("Done!")
    print("\nTo add more events, edit the HISTORICAL_EVENTS or DIARY_EVENTS lists")
    print("in this script and re-run, or edit data/timeline.json directly.")


if __name__ == "__main__":
    main()
