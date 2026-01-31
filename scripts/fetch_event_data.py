#!/usr/bin/env python3
"""
Fetch Wikipedia summaries and generate SVG maps for historical events.

This script enriches the timeline.json historical events with:
- Wikipedia article summaries (1-2 paragraphs)
- Key facts extracted from the articles
- Pre-generated SVG region maps

Usage:
    uv run python scripts/fetch_event_data.py
"""

import json
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path


# Wikipedia API endpoint
WIKIPEDIA_API = "https://en.wikipedia.org/api/rest_v1/page/summary/"

# Map data for each historical event
# Each entry contains: bounds (north, south, east, west), markers, and coastline/border paths
EVENT_MAP_DATA = {
    "dday": {
        "title": "D-Day Landings",
        "bounds": {"north": 49.5, "south": 49.2, "east": -0.3, "west": -1.2},
        "water_path": "",
        "land_path": "M0,120 Q30,100 60,110 Q90,95 120,105 Q150,90 180,100 Q210,85 240,95 Q270,80 300,90 L300,200 L0,200 Z",
        "markers": [
            {"x": 40, "y": 105, "label": "Utah"},
            {"x": 85, "y": 100, "label": "Omaha"},
            {"x": 140, "y": 95, "label": "Gold"},
            {"x": 195, "y": 90, "label": "Juno"},
            {"x": 250, "y": 85, "label": "Sword"},
        ],
        "annotations": [
            {"type": "arrow", "x1": 150, "y1": 40, "x2": 150, "y2": 80, "label": "Allied Forces"},
        ]
    },
    "liberation_cherbourg": {
        "title": "Cherbourg Peninsula",
        "bounds": {"north": 49.8, "south": 49.3, "east": -1.2, "west": -2.0},
        "water_path": "M0,0 L300,0 L300,80 Q200,90 150,70 Q100,50 50,60 Q25,70 0,65 Z",
        "land_path": "M0,65 Q25,70 50,60 Q100,50 150,70 Q200,90 300,80 L300,200 L0,200 Z",
        "markers": [
            {"x": 150, "y": 100, "label": "Cherbourg"},
            {"x": 200, "y": 150, "label": "Utah Beach"},
        ],
        "annotations": []
    },
    "caen_bombing": {
        "title": "Operation Charnwood",
        "bounds": {"north": 49.4, "south": 49.1, "east": -0.2, "west": -0.6},
        "water_path": "",
        "land_path": "M0,0 L300,0 L300,200 L0,200 Z",
        "markers": [
            {"x": 150, "y": 100, "label": "Caen"},
            {"x": 80, "y": 60, "label": "Crepon"},
        ],
        "annotations": [
            {"type": "zone", "cx": 150, "cy": 100, "r": 40, "label": "Bombing Zone"},
        ]
    },
    "falaise_pocket": {
        "title": "Falaise Pocket",
        "bounds": {"north": 49.1, "south": 48.6, "east": -0.1, "west": -0.7},
        "water_path": "",
        "land_path": "M0,0 L300,0 L300,200 L0,200 Z",
        "markers": [
            {"x": 120, "y": 80, "label": "Falaise"},
            {"x": 180, "y": 140, "label": "Argentan"},
        ],
        "annotations": [
            {"type": "encirclement", "cx": 150, "cy": 110, "rx": 60, "ry": 40},
        ]
    },
    "liberation_paris": {
        "title": "Liberation of Paris",
        "bounds": {"north": 49.0, "south": 48.7, "east": 2.5, "west": 2.1},
        "water_path": "",
        "land_path": "M0,0 L300,0 L300,200 L0,200 Z",
        "markers": [
            {"x": 150, "y": 100, "label": "Paris"},
        ],
        "annotations": [
            {"type": "river", "path": "M80,180 Q120,140 150,120 Q180,100 220,60"},
        ]
    },
    "liberation_brussels": {
        "title": "Liberation of Brussels",
        "bounds": {"north": 51.0, "south": 50.7, "east": 4.6, "west": 4.2},
        "water_path": "",
        "land_path": "M0,0 L300,0 L300,200 L0,200 Z",
        "markers": [
            {"x": 150, "y": 100, "label": "Brussels"},
        ],
        "annotations": []
    },
    "liberation_antwerp": {
        "title": "Liberation of Antwerp",
        "bounds": {"north": 51.4, "south": 51.1, "east": 4.6, "west": 4.2},
        "water_path": "M0,0 L100,0 Q120,30 130,60 L130,80 Q100,90 80,100 L0,100 Z",
        "land_path": "M100,0 L300,0 L300,200 L0,200 L0,100 L80,100 Q100,90 130,80 L130,60 Q120,30 100,0 Z",
        "markers": [
            {"x": 180, "y": 100, "label": "Antwerp"},
            {"x": 100, "y": 60, "label": "Scheldt"},
        ],
        "annotations": []
    },
    "scheldt_battle": {
        "title": "Battle of the Scheldt",
        "bounds": {"north": 51.6, "south": 51.2, "east": 4.2, "west": 3.4},
        "water_path": "M0,80 Q50,70 100,90 Q150,110 200,100 Q250,90 300,100 L300,0 L0,0 Z",
        "land_path": "M0,80 Q50,70 100,90 Q150,110 200,100 Q250,90 300,100 L300,200 L0,200 Z",
        "markers": [
            {"x": 80, "y": 120, "label": "Knokke"},
            {"x": 200, "y": 130, "label": "Goes"},
            {"x": 250, "y": 110, "label": "Beveland"},
        ],
        "annotations": []
    },
    "bulge_starts": {
        "title": "Battle of the Bulge",
        "bounds": {"north": 50.5, "south": 49.8, "east": 6.5, "west": 5.5},
        "water_path": "",
        "land_path": "M0,0 L300,0 L300,200 L0,200 Z",
        "markers": [
            {"x": 150, "y": 100, "label": "Bastogne"},
            {"x": 80, "y": 60, "label": "St. Vith"},
        ],
        "annotations": [
            {"type": "bulge", "path": "M50,50 Q100,80 150,120 Q200,80 250,50"},
        ]
    },
    "bulge_ends": {
        "title": "Battle of the Bulge - End",
        "bounds": {"north": 50.5, "south": 49.8, "east": 6.5, "west": 5.5},
        "water_path": "",
        "land_path": "M0,0 L300,0 L300,200 L0,200 Z",
        "markers": [
            {"x": 150, "y": 100, "label": "Bastogne"},
            {"x": 80, "y": 60, "label": "St. Vith"},
        ],
        "annotations": []
    },
    "rhine_crossing": {
        "title": "Operation Plunder",
        "bounds": {"north": 51.8, "south": 51.4, "east": 6.8, "west": 6.4},
        "water_path": "",
        "land_path": "M0,0 L300,0 L300,200 L0,200 Z",
        "markers": [
            {"x": 150, "y": 100, "label": "Wesel"},
            {"x": 100, "y": 80, "label": "Rees"},
        ],
        "annotations": [
            {"type": "river", "path": "M140,0 Q145,50 150,100 Q155,150 160,200"},
        ]
    },
    "ve_day": {
        "title": "Victory in Europe",
        "bounds": {"north": 52.0, "south": 48.0, "east": 8.0, "west": 2.0},
        "water_path": "M0,0 L50,0 Q40,30 35,60 L30,100 L0,100 Z",
        "land_path": "M50,0 L300,0 L300,200 L0,200 L0,100 L30,100 L35,60 Q40,30 50,0 Z",
        "markers": [
            {"x": 100, "y": 80, "label": "Brussels"},
            {"x": 150, "y": 60, "label": "Antwerp"},
            {"x": 250, "y": 100, "label": "Berlin"},
        ],
        "annotations": []
    },
    "berlin_victory_parade": {
        "title": "Berlin Victory Parade",
        "bounds": {"north": 52.6, "south": 52.4, "east": 13.5, "west": 13.3},
        "water_path": "",
        "land_path": "M0,0 L300,0 L300,200 L0,200 Z",
        "markers": [
            {"x": 150, "y": 100, "label": "Berlin"},
            {"x": 120, "y": 80, "label": "Brandenburg"},
        ],
        "annotations": [
            {"type": "route", "path": "M80,150 L150,100 L220,150"},
        ]
    },
    "japan_surrenders": {
        "title": "VJ Day",
        "bounds": {"north": 54.0, "south": 48.0, "east": 14.0, "west": 2.0},
        "water_path": "M0,0 L50,0 Q40,30 35,60 L30,100 L0,100 Z M280,0 L300,0 L300,60 Q290,50 280,40 Z",
        "land_path": "M50,0 L280,0 Q290,50 300,60 L300,200 L0,200 L0,100 L30,100 L35,60 Q40,30 50,0 Z",
        "markers": [
            {"x": 150, "y": 100, "label": "Europe"},
        ],
        "annotations": []
    },
}

# Pre-researched summaries and key facts (fallback if Wikipedia API fails)
FALLBACK_DATA = {
    "dday": {
        "summary": "On 6 June 1944, Allied forces launched the largest amphibious invasion in history on the beaches of Normandy, France. Codenamed Operation Overlord, the assault involved nearly 160,000 troops crossing the English Channel, supported by over 5,000 ships and 11,000 aircraft. The invasion marked the beginning of the liberation of Western Europe from Nazi occupation.",
        "key_facts": [
            "156,000 Allied troops landed on first day",
            "5 beaches: Utah, Omaha, Gold, Juno, Sword",
            "Over 4,400 Allied deaths on D-Day",
            "Largest seaborne invasion in history"
        ]
    },
    "liberation_cherbourg": {
        "summary": "The Battle of Cherbourg was fought from 22-30 June 1944, resulting in the capture of the vital port city by American forces. The port was crucial for Allied logistics, though German demolitions delayed its full operation until September. The capture marked a significant milestone in securing supply lines for the Normandy campaign.",
        "key_facts": [
            "Port captured by US VII Corps",
            "39,000 German prisoners taken",
            "Port operational by late September",
            "Key to Allied supply chain"
        ]
    },
    "caen_bombing": {
        "summary": "Operation Charnwood began on 8 July 1944 with a massive aerial bombardment of Caen by RAF Bomber Command. Over 2,500 tons of bombs were dropped on the northern outskirts of the city, followed by a ground assault. Though controversial due to civilian casualties, the operation finally secured the northern half of Caen for British and Canadian forces.",
        "key_facts": [
            "467 RAF heavy bombers participated",
            "2,500 tons of bombs dropped",
            "Significant civilian casualties",
            "Northern Caen captured by 9 July"
        ]
    },
    "falaise_pocket": {
        "summary": "The Falaise Pocket was the decisive engagement of the Battle of Normandy, occurring between 12-21 August 1944. Allied forces encircled two German armies, destroying much of their combat capability. Though some German units escaped, the pocket's closure effectively ended German resistance in Normandy and opened the path to Paris.",
        "key_facts": [
            "50,000 German soldiers captured",
            "10,000 German soldiers killed",
            "Massive equipment losses for Germany",
            "Ended Battle of Normandy"
        ]
    },
    "liberation_paris": {
        "summary": "Paris was liberated on 25 August 1944 after a popular uprising and the arrival of Free French and American forces. General Dietrich von Choltitz, the German military governor, defied Hitler's orders to destroy the city. Charles de Gaulle led a triumphant parade down the Champs-Elysees the following day, marking the symbolic restoration of French sovereignty.",
        "key_facts": [
            "City spared from destruction",
            "General von Choltitz surrendered",
            "De Gaulle parade on 26 August",
            "4 years of German occupation ended"
        ]
    },
    "liberation_brussels": {
        "summary": "Brussels was liberated on 3 September 1944 by the British Guards Armoured Division, ending four years of German occupation. The rapid advance caught German forces off guard, and the city was taken with minimal fighting. Jubilant crowds filled the streets to welcome their liberators, though some German resistance continued in the outskirts.",
        "key_facts": [
            "Liberated by Guards Armoured Division",
            "Minimal fighting in city center",
            "Part of the rapid Allied advance",
            "4 years of occupation ended"
        ]
    },
    "liberation_antwerp": {
        "summary": "Antwerp was liberated on 4 September 1944 by the British 11th Armoured Division. The port facilities were captured nearly intact, but the city could not be used for shipping until the Scheldt estuary was cleared of German forces. The port would become the most important Allied supply hub after finally opening in late November.",
        "key_facts": [
            "Port captured nearly intact",
            "Could not be used until Scheldt cleared",
            "Became key Allied supply hub",
            "German V-weapon attacks followed"
        ]
    },
    "scheldt_battle": {
        "summary": "The Battle of the Scheldt was fought from 2 October to 8 November 1944 to open the port of Antwerp to Allied shipping. Canadian forces, with British and other Allied support, fought through flooded polders and fortified positions along the Scheldt estuary. The hard-fought campaign cleared the approaches, allowing the first supply ships to reach Antwerp on 28 November.",
        "key_facts": [
            "Canadian forces led the campaign",
            "12,873 Canadian casualties",
            "Opened vital supply route",
            "First convoy reached Antwerp 28 Nov"
        ]
    },
    "bulge_starts": {
        "summary": "The Battle of the Bulge began on 16 December 1944 when German forces launched a surprise offensive through the Ardennes forest. Hitler aimed to split Allied lines and capture Antwerp. The attack created a 'bulge' in American lines and surrounded Bastogne, where the 101st Airborne held out despite German demands for surrender.",
        "key_facts": [
            "250,000 German troops attacked",
            "Largest battle on Western Front",
            "'Nuts!' reply at Bastogne",
            "Coldest winter in decades"
        ]
    },
    "bulge_ends": {
        "summary": "The Battle of the Bulge officially ended on 25 January 1945 when American forces eliminated the last German salient. The failed offensive cost Germany irreplaceable men and equipment, hastening the end of the war. American casualties were also heavy, making it the bloodiest battle for US forces in the European theater.",
        "key_facts": [
            "19,000 American soldiers killed",
            "German losses: 100,000+ casualties",
            "Last major German offensive",
            "Depleted German reserves"
        ]
    },
    "rhine_crossing": {
        "summary": "Operation Plunder on 23-24 March 1945 was the largest opposed river crossing in history, with Allied forces crossing the Rhine into the German heartland. The operation involved British, American, and Canadian forces supported by massive airborne operations. The crossing marked the beginning of the final campaign to defeat Nazi Germany.",
        "key_facts": [
            "Largest river crossing operation ever",
            "Operation Varsity airborne support",
            "25,000 troops crossed on first day",
            "Opened path into Germany"
        ]
    },
    "ve_day": {
        "summary": "Victory in Europe Day was celebrated on 8 May 1945 following Germany's unconditional surrender. The surrender was signed in Reims on 7 May and ratified in Berlin on 8-9 May. Across Europe, jubilant crowds took to the streets in spontaneous celebrations, marking the end of nearly six years of devastating war on the continent.",
        "key_facts": [
            "German surrender signed 7 May",
            "Ratified in Berlin 8-9 May",
            "End of war in Europe",
            "Massive celebrations worldwide"
        ]
    },
    "berlin_victory_parade": {
        "summary": "The Berlin Victory Parade took place on 21 July 1945, celebrating the Allied victory over Nazi Germany. Troops from Britain, the United States, France, and the Soviet Union marched through the ruined city. The parade demonstrated Allied unity and marked the symbolic end of the European war in the heart of the former enemy capital.",
        "key_facts": [
            "Four Allied powers participated",
            "Held in ruined Berlin",
            "Symbolic end of European war",
            "Massive military display"
        ]
    },
    "japan_surrenders": {
        "summary": "Japan's surrender on 15 August 1945 (VJ Day) ended World War II. Following the atomic bombings of Hiroshima and Nagasaki, Emperor Hirohito announced Japan's acceptance of the Potsdam Declaration. The formal surrender ceremony took place on 2 September aboard USS Missouri in Tokyo Bay, concluding the deadliest conflict in human history.",
        "key_facts": [
            "Announced by Emperor Hirohito",
            "Formal surrender 2 September",
            "End of World War II",
            "Followed atomic bombings"
        ]
    },
}


def fetch_wikipedia_summary(wiki_url: str) -> tuple[str, list[str]]:
    """Fetch summary from Wikipedia API.

    Returns tuple of (summary_text, key_facts_list).
    """
    # Extract article title from URL
    match = re.search(r'wikipedia\.org/wiki/(.+)$', wiki_url)
    if not match:
        return "", []

    title = match.group(1)
    api_url = WIKIPEDIA_API + urllib.parse.quote(title)

    try:
        req = urllib.request.Request(
            api_url,
            headers={'User-Agent': 'WW2DiaryProject/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            summary = data.get('extract', '')
            # Clean up the summary - take first 2 paragraphs
            paragraphs = summary.split('\n\n')
            if len(paragraphs) > 2:
                summary = '\n\n'.join(paragraphs[:2])
            return summary, []
    except Exception as e:
        print(f"  Warning: Could not fetch from Wikipedia ({e})")
        return "", []


def generate_svg_map(event_id: str) -> str:
    """Generate an SVG map for the given event."""
    if event_id not in EVENT_MAP_DATA:
        return ""

    data = EVENT_MAP_DATA[event_id]

    svg_parts = [
        '<svg viewBox="0 0 300 200" xmlns="http://www.w3.org/2000/svg">',
        '  <defs>',
        '    <style>',
        '      .water { fill: #b8d4e8; }',
        '      .land { fill: #e8e4d9; }',
        '      .marker { fill: #8b4513; }',
        '      .label { font-family: Georgia, serif; font-size: 10px; fill: #333; }',
        '      .title { font-family: Georgia, serif; font-size: 11px; font-weight: bold; fill: #2c3e50; }',
        '      .annotation { fill: none; stroke: #8b4513; stroke-width: 1.5; opacity: 0.6; }',
        '      .river { fill: none; stroke: #6ba3d6; stroke-width: 2; }',
        '      .zone { fill: #c0392b; opacity: 0.2; }',
        '    </style>',
        '  </defs>',
    ]

    # Background water
    svg_parts.append('  <rect class="water" width="300" height="200"/>')

    # Land mass
    if data.get("land_path"):
        svg_parts.append(f'  <path class="land" d="{data["land_path"]}"/>')

    # Water overlay (for complex coastlines)
    if data.get("water_path"):
        svg_parts.append(f'  <path class="water" d="{data["water_path"]}"/>')

    # Annotations
    for ann in data.get("annotations", []):
        if ann["type"] == "arrow":
            svg_parts.append(f'  <line class="annotation" x1="{ann["x1"]}" y1="{ann["y1"]}" x2="{ann["x2"]}" y2="{ann["y2"]}" marker-end="url(#arrowhead)"/>')
        elif ann["type"] == "zone":
            svg_parts.append(f'  <circle class="zone" cx="{ann["cx"]}" cy="{ann["cy"]}" r="{ann["r"]}"/>')
        elif ann["type"] == "encirclement":
            svg_parts.append(f'  <ellipse class="annotation" cx="{ann["cx"]}" cy="{ann["cy"]}" rx="{ann["rx"]}" ry="{ann["ry"]}" stroke-dasharray="5,3"/>')
        elif ann["type"] == "river":
            svg_parts.append(f'  <path class="river" d="{ann["path"]}"/>')
        elif ann["type"] == "route":
            svg_parts.append(f'  <path class="annotation" d="{ann["path"]}" stroke-dasharray="4,2"/>')
        elif ann["type"] == "bulge":
            svg_parts.append(f'  <path class="annotation" d="{ann["path"]}" stroke-width="2"/>')

    # Markers
    for marker in data.get("markers", []):
        x, y = marker["x"], marker["y"]
        label = marker["label"]
        svg_parts.append(f'  <circle class="marker" cx="{x}" cy="{y}" r="4"/>')
        svg_parts.append(f'  <text class="label" x="{x + 6}" y="{y + 4}">{label}</text>')

    # Title
    svg_parts.append(f'  <text class="title" x="10" y="15">{data["title"]}</text>')

    svg_parts.append('</svg>')

    return '\n'.join(svg_parts)


def enrich_timeline(timeline_path: Path) -> dict:
    """Enrich timeline data with summaries, facts, and maps."""
    with open(timeline_path, 'r', encoding='utf-8') as f:
        timeline = json.load(f)

    historical_events = [e for e in timeline["events"] if e["type"] == "historical"]
    print(f"Found {len(historical_events)} historical events to enrich")

    for event in timeline["events"]:
        if event["type"] != "historical":
            continue

        event_id = event["id"]
        print(f"\nProcessing: {event['name']}")

        # Try to fetch from Wikipedia
        wiki_url = event.get("source", "")
        summary, facts = "", []

        if wiki_url and "wikipedia.org" in wiki_url:
            print(f"  Fetching from Wikipedia...")
            summary, facts = fetch_wikipedia_summary(wiki_url)
            time.sleep(0.5)  # Be nice to Wikipedia API

        # Use fallback data if Wikipedia fetch failed or returned empty
        if not summary and event_id in FALLBACK_DATA:
            print(f"  Using fallback data for summary")
            summary = FALLBACK_DATA[event_id]["summary"]

        # Always use fallback key facts (Wikipedia API doesn't provide structured facts)
        if event_id in FALLBACK_DATA and FALLBACK_DATA[event_id].get("key_facts"):
            facts = FALLBACK_DATA[event_id]["key_facts"]
            print(f"  Using fallback key facts")

        # Generate SVG map
        svg_map = generate_svg_map(event_id)
        if svg_map:
            print(f"  Generated SVG map")

        # Add enriched data to event
        event["summary"] = summary
        event["key_facts"] = facts
        event["map_svg"] = svg_map

        # Add map bounds if available
        if event_id in EVENT_MAP_DATA:
            event["map_bounds"] = EVENT_MAP_DATA[event_id]["bounds"]

    return timeline


def main():
    base_dir = Path(__file__).parent.parent
    timeline_path = base_dir / "data" / "timeline.json"

    if not timeline_path.exists():
        print(f"Error: {timeline_path} not found")
        print("Run 'uv run python scripts/research_events.py' first to create timeline.json")
        return

    print("Enriching timeline data...")
    timeline = enrich_timeline(timeline_path)

    # Count enriched events
    enriched = sum(1 for e in timeline["events"]
                   if e.get("summary") or e.get("map_svg"))
    print(f"\n{enriched} events enriched with summaries and/or maps")

    # Save enriched timeline
    print(f"\nSaving to {timeline_path}...")
    with open(timeline_path, 'w', encoding='utf-8') as f:
        json.dump(timeline, f, indent=2, ensure_ascii=False)

    # Also save individual SVG files for reference
    maps_dir = base_dir / "data" / "event_maps"
    maps_dir.mkdir(exist_ok=True)

    for event in timeline["events"]:
        if event.get("map_svg"):
            svg_path = maps_dir / f"{event['id']}.svg"
            svg_path.write_text(event["map_svg"], encoding='utf-8')

    print(f"SVG maps saved to {maps_dir}/")
    print("\nDone! Run 'uv run python generate_app.py' to regenerate the app.")


if __name__ == "__main__":
    main()
