#!/usr/bin/env python3
"""
Generate an interactive HTML map application from Edgar Hopkins' WW2 diary.

Reads the diary markdown and places.json, then generates a single self-contained
HTML file with an interactive Leaflet map alongside the diary text, with a
timeline slider for filtering by date.
"""

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import markdown


def get_version_info() -> dict:
    """Get git commit hash and timestamp for version tracking."""
    try:
        # Get short commit hash
        git_hash = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, check=True
        ).stdout.strip()

        # Get commit timestamp
        git_timestamp = subprocess.run(
            ["git", "log", "-1", "--format=%cI"],
            capture_output=True, text=True, check=True
        ).stdout.strip()

        return {
            "hash": git_hash,
            "timestamp": git_timestamp,
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }
    except (subprocess.CalledProcessError, FileNotFoundError):
        return {
            "hash": "unknown",
            "timestamp": "",
            "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        }


def load_diary(path: Path) -> str:
    """Load and convert diary markdown to HTML."""
    md_content = path.read_text(encoding="utf-8")
    md = markdown.Markdown(extensions=["extra"])
    return md.convert(md_content)


def load_places(path: Path) -> list[dict]:
    """Load places data from JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["places"]


def load_timeline(path: Path) -> dict:
    """Load timeline data from JSON file."""
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"events": [], "metadata": {"date_range": {"start": "1943-12-01", "end": "1946-02-18"}}}


def create_keyword_pattern(places: list[dict]) -> re.Pattern:
    """Create a regex pattern matching all place keywords."""
    all_keywords = []
    for place in places:
        all_keywords.extend(place["keywords"])
    # Sort by length (longest first) to match longer phrases first
    all_keywords.sort(key=len, reverse=True)
    # Escape special regex characters and join with |
    escaped = [re.escape(kw) for kw in all_keywords]
    pattern = r"\b(" + "|".join(escaped) + r")\b"
    return re.compile(pattern)


def build_keyword_to_place_map(places: list[dict]) -> dict[str, dict]:
    """Build a mapping from keyword to place data."""
    mapping = {}
    for place in places:
        for keyword in place["keywords"]:
            mapping[keyword.lower()] = place
    return mapping


def wrap_locations_in_html(html: str, places: list[dict]) -> str:
    """Wrap location mentions in clickable span tags."""
    pattern = create_keyword_pattern(places)
    keyword_map = build_keyword_to_place_map(places)

    def replace_match(match):
        keyword = match.group(1)
        place = keyword_map.get(keyword.lower())
        if place:
            return f'<span class="location" data-place-id="{place["id"]}">{keyword}</span>'
        return keyword

    # Don't replace inside HTML tags
    parts = []
    last_end = 0
    in_tag = False
    tag_start = 0

    for i, char in enumerate(html):
        if char == "<":
            # Process text before this tag
            if not in_tag and i > last_end:
                text_part = html[last_end:i]
                text_part = pattern.sub(replace_match, text_part)
                parts.append(text_part)
            in_tag = True
            tag_start = i
        elif char == ">" and in_tag:
            # Append the tag unchanged
            parts.append(html[tag_start : i + 1])
            in_tag = False
            last_end = i + 1

    # Process any remaining text
    if last_end < len(html):
        text_part = html[last_end:]
        text_part = pattern.sub(replace_match, text_part)
        parts.append(text_part)

    return "".join(parts)


def generate_html(diary_html: str, places: list[dict], timeline: dict, version: dict) -> str:
    """Generate the complete HTML application."""
    places_json = json.dumps(places, indent=2)
    timeline_json = json.dumps(timeline, indent=2)
    version_str = f"{version['hash']} ({version['generated'][:10]})"

    # Inject version indicator into the first h1 tag
    version_span = f'<span class="version-indicator" title="Git: {version["hash"]} | Built: {version["generated"]}">{version_str}</span>'
    diary_html = diary_html.replace("</h1>", f"{version_span}</h1>", 1)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Edgar Hopkins' WW2 Diary - Interactive Map</title>
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
          integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=" crossorigin="">
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
            integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=" crossorigin=""></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/nouislider@15.7.1/dist/nouislider.min.css">
    <script src="https://cdn.jsdelivr.net/npm/nouislider@15.7.1/dist/nouislider.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: Georgia, 'Times New Roman', serif;
            height: 100vh;
            overflow: hidden;
        }}

        .container {{
            display: flex;
            height: 100vh;
        }}

        .diary-panel {{
            width: 50%;
            height: 100%;
            overflow-y: auto;
            padding: 2rem;
            background: #faf8f5;
            border-right: 1px solid #ddd;
        }}

        .map-panel {{
            width: 50%;
            height: 100%;
            display: flex;
            flex-direction: column;
        }}

        #map {{
            width: 100%;
            flex: 1;
        }}

        .timeline-container {{
            padding: 1rem 1.5rem 1.5rem;
            background: #f5f5f5;
            border-top: 1px solid #ddd;
        }}

        .timeline-controls {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 0.75rem;
            flex-wrap: wrap;
            align-items: center;
        }}

        .timeline-btn {{
            padding: 0.4rem 0.8rem;
            font-size: 0.8rem;
            font-family: Georgia, serif;
            border: 1px solid #8b4513;
            background: white;
            color: #8b4513;
            cursor: pointer;
            border-radius: 3px;
            transition: all 0.2s ease;
        }}

        .timeline-btn:hover {{
            background: #8b4513;
            color: white;
        }}

        .timeline-btn.active {{
            background: #8b4513;
            color: white;
        }}

        .play-btn {{
            width: 36px;
            height: 36px;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1rem;
        }}

        .timeline-date-display {{
            flex: 1;
            text-align: right;
            font-size: 0.9rem;
            color: #666;
            font-style: italic;
        }}

        #timeline-slider {{
            margin: 0.5rem 0;
        }}

        .noUi-connect {{
            background: #8b4513;
        }}

        .noUi-handle {{
            border-color: #8b4513;
        }}

        .noUi-horizontal {{
            height: 12px;
        }}

        .noUi-horizontal .noUi-handle {{
            width: 20px;
            height: 20px;
            top: -5px;
            border-radius: 50%;
        }}

        .noUi-target {{
            background: #e0e0e0;
            border: none;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.1);
        }}

        .timeline-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 0.75rem;
            color: #888;
            margin-top: 0.5rem;
        }}

        .event-markers {{
            position: relative;
            height: 20px;
            margin-bottom: 0.25rem;
        }}

        .event-dot {{
            position: absolute;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            transform: translateX(-50%);
            cursor: pointer;
            transition: transform 0.2s ease;
        }}

        .event-dot:hover {{
            transform: translateX(-50%) scale(1.5);
        }}

        .event-dot.historical {{
            background: #2980b9;
            top: 0;
        }}

        .event-dot.diary {{
            background: #c0392b;
            top: 10px;
        }}

        .event-tooltip {{
            position: absolute;
            bottom: 100%;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(0,0,0,0.85);
            color: white;
            padding: 0.5rem 0.75rem;
            border-radius: 4px;
            font-size: 0.75rem;
            white-space: nowrap;
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.2s ease;
            z-index: 1000;
        }}

        .event-dot:hover .event-tooltip {{
            opacity: 1;
        }}

        .diary-content {{
            max-width: 700px;
            margin: 0 auto;
            line-height: 1.8;
            color: #333;
        }}

        .diary-content h1 {{
            font-size: 1.8rem;
            margin-bottom: 1rem;
            color: #2c3e50;
            border-bottom: 2px solid #8b4513;
            padding-bottom: 0.5rem;
            position: relative;
        }}

        .version-indicator {{
            position: absolute;
            right: 0;
            bottom: 0.5rem;
            font-size: 0.65rem;
            font-weight: normal;
            color: #999;
            font-family: monospace;
        }}

        .version-indicator:hover {{
            color: #666;
        }}

        .diary-content h2 {{
            font-size: 1.4rem;
            margin: 1.5rem 0 0.75rem 0;
            color: #34495e;
        }}

        .diary-content h3 {{
            font-size: 1.2rem;
            margin: 1.25rem 0 0.5rem 0;
            color: #446;
        }}

        .diary-content p {{
            margin-bottom: 1rem;
            text-align: justify;
        }}

        .diary-content em {{
            color: #666;
        }}

        .diary-content hr {{
            border: none;
            border-top: 1px solid #ccc;
            margin: 2rem 0;
        }}

        .location {{
            background: linear-gradient(to bottom, transparent 60%, #ffe4b5 60%);
            cursor: pointer;
            padding: 0 2px;
            border-radius: 2px;
            transition: background 0.2s ease;
        }}

        .location:hover {{
            background: #ffd700;
        }}

        .location.active {{
            background: #ffa500;
            font-weight: bold;
        }}

        .location.dimmed {{
            opacity: 0.3;
            background: linear-gradient(to bottom, transparent 60%, #ddd 60%);
        }}

        .leaflet-popup-content {{
            font-family: Georgia, serif;
            line-height: 1.5;
        }}

        .popup-title {{
            font-weight: bold;
            font-size: 1.1rem;
            color: #2c3e50;
            margin-bottom: 0.5rem;
            border-bottom: 1px solid #ddd;
            padding-bottom: 0.3rem;
        }}

        .popup-date {{
            font-size: 0.85rem;
            color: #666;
            font-style: italic;
            margin-bottom: 0.5rem;
        }}

        .popup-summary {{
            font-size: 0.95rem;
            color: #444;
        }}

        .legend {{
            background: white;
            padding: 10px;
            border-radius: 5px;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            font-family: Georgia, serif;
            font-size: 0.85rem;
        }}

        .legend h4 {{
            margin: 0 0 8px 0;
            font-size: 0.95rem;
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            margin: 4px 0;
        }}

        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-right: 8px;
            border: 2px solid white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }}

        .marker-dimmed {{
            opacity: 0.2;
        }}

        .journey-segment {{
            transition: opacity 0.3s ease;
        }}

        /* Event Detail Panel Styles */
        .event-panel {{
            position: fixed;
            top: 0;
            right: 0;
            width: 380px;
            height: 100vh;
            background: #faf8f5;
            box-shadow: -4px 0 20px rgba(0,0,0,0.15);
            transform: translateX(100%);
            transition: transform 0.3s ease;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        .event-panel.open {{
            transform: translateX(0);
        }}

        .event-panel-header {{
            padding: 1rem 1.5rem;
            background: #8b4513;
            color: white;
            display: flex;
            align-items: flex-start;
            justify-content: space-between;
            flex-shrink: 0;
        }}

        .event-panel-close {{
            background: none;
            border: none;
            color: white;
            font-size: 1.5rem;
            cursor: pointer;
            padding: 0;
            line-height: 1;
            opacity: 0.8;
            transition: opacity 0.2s ease;
        }}

        .event-panel-close:hover {{
            opacity: 1;
        }}

        .event-panel-title {{
            font-family: Georgia, serif;
            font-size: 1.2rem;
            font-weight: bold;
            margin: 0;
            padding-right: 1rem;
            line-height: 1.3;
        }}

        .event-panel-content {{
            flex: 1;
            overflow-y: auto;
            padding: 1.5rem;
        }}

        .event-panel-date {{
            font-size: 0.95rem;
            color: #666;
            font-style: italic;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 1px solid #ddd;
        }}

        .event-panel-map {{
            margin-bottom: 1.5rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            overflow: hidden;
            background: #b8d4e8;
            height: 200px;
        }}

        .event-panel-map .leaflet-container {{
            height: 100%;
            width: 100%;
        }}

        .event-panel-summary {{
            font-family: Georgia, serif;
            font-size: 0.95rem;
            line-height: 1.7;
            color: #333;
            margin-bottom: 1.5rem;
            text-align: justify;
        }}

        .event-panel-facts {{
            margin: 0 0 1.5rem 0;
            padding: 0;
            list-style: none;
        }}

        .event-panel-facts li {{
            font-size: 0.9rem;
            color: #444;
            padding: 0.5rem 0 0.5rem 1.5rem;
            position: relative;
            border-bottom: 1px solid #eee;
        }}

        .event-panel-facts li:last-child {{
            border-bottom: none;
        }}

        .event-panel-facts li::before {{
            content: "\\2022";
            color: #8b4513;
            font-weight: bold;
            position: absolute;
            left: 0;
        }}

        .event-panel-source {{
            display: inline-block;
            font-size: 0.9rem;
            color: #2980b9;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border: 1px solid #2980b9;
            border-radius: 4px;
            transition: all 0.2s ease;
        }}

        .event-panel-source:hover {{
            background: #2980b9;
            color: white;
        }}

        .event-panel-overlay {{
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.3);
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s ease, visibility 0.3s ease;
            z-index: 999;
        }}

        .event-panel-overlay.open {{
            opacity: 1;
            visibility: visible;
        }}

        @media (max-width: 900px) {{
            .container {{
                flex-direction: column;
            }}

            .diary-panel, .map-panel {{
                width: 100%;
                height: 50%;
            }}

            .diary-panel {{
                border-right: none;
                border-bottom: 1px solid #ddd;
            }}

            .timeline-controls {{
                flex-wrap: wrap;
            }}

            .timeline-date-display {{
                width: 100%;
                text-align: center;
                margin-top: 0.5rem;
            }}

            .event-panel {{
                width: 100%;
            }}
        }}
    </style>
</head>
<body>
    <div class="event-panel-overlay" id="event-panel-overlay"></div>
    <div class="event-panel" id="event-panel">
        <div class="event-panel-header">
            <h2 class="event-panel-title" id="event-panel-title"></h2>
            <button class="event-panel-close" id="event-panel-close">&times;</button>
        </div>
        <div class="event-panel-content">
            <div class="event-panel-date" id="event-panel-date"></div>
            <div class="event-panel-map" id="event-panel-map"></div>
            <div class="event-panel-summary" id="event-panel-summary"></div>
            <ul class="event-panel-facts" id="event-panel-facts"></ul>
            <a class="event-panel-source" id="event-panel-source" target="_blank">Read more on Wikipedia</a>
        </div>
    </div>

    <div class="container">
        <div class="diary-panel">
            <div class="diary-content">
                {diary_html}
            </div>
        </div>
        <div class="map-panel">
            <div id="map"></div>
            <div class="timeline-container">
                <div class="timeline-controls">
                    <button class="timeline-btn play-btn" id="play-btn" title="Play animation">&#9658;</button>
                    <button class="timeline-btn" id="btn-dday">D-Day</button>
                    <button class="timeline-btn" id="btn-veday">VE Day</button>
                    <button class="timeline-btn" id="btn-full">Full Journey</button>
                    <div class="timeline-date-display" id="date-display">December 1943 - February 1946</div>
                </div>
                <div class="event-markers" id="event-markers"></div>
                <div id="timeline-slider"></div>
                <div class="timeline-labels">
                    <span>Dec 1943</span>
                    <span>Jun 1944</span>
                    <span>Dec 1944</span>
                    <span>Jun 1945</span>
                    <span>Feb 1946</span>
                </div>
            </div>
        </div>
    </div>

    <script>
        const places = {places_json};
        const timeline = {timeline_json};

        // Date utilities
        const minDate = new Date('1943-12-01');
        const maxDate = new Date('1946-02-18');
        const dateRange = maxDate - minDate;

        function dateToTimestamp(dateStr) {{
            return new Date(dateStr).getTime();
        }}

        function timestampToDate(ts) {{
            return new Date(ts);
        }}

        function formatDate(date) {{
            const months = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December'];
            return months[date.getMonth()] + ' ' + date.getFullYear();
        }}

        function dateToPercent(dateStr) {{
            const d = new Date(dateStr);
            return ((d - minDate) / dateRange) * 100;
        }}

        // Country colors for markers
        const countryColors = {{
            'England': '#c0392b',
            'France': '#2980b9',
            'Belgium': '#f39c12',
            'Netherlands': '#e67e22',
            'Germany': '#7f8c8d'
        }};

        // Initialize map centered on Western Europe
        const map = L.map('map').setView([50.5, 3.5], 6);

        // Add OpenStreetMap tiles
        L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
            maxZoom: 19,
            attribution: '&copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }}).addTo(map);

        // Store markers by place ID
        const markers = {{}};
        const markerElements = {{}};

        // Create custom icon function
        function createIcon(color) {{
            return L.divIcon({{
                className: 'custom-marker',
                html: `<svg width="24" height="36" viewBox="0 0 24 36" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 0C5.4 0 0 5.4 0 12c0 9 12 24 12 24s12-15 12-24c0-6.6-5.4-12-12-12z"
                          fill="${{color}}" stroke="white" stroke-width="2"/>
                    <circle cx="12" cy="12" r="5" fill="white"/>
                </svg>`,
                iconSize: [24, 36],
                iconAnchor: [12, 36],
                popupAnchor: [0, -36]
            }});
        }}

        // Add markers for each place
        places.forEach(place => {{
            const color = countryColors[place.country] || '#333';
            const icon = createIcon(color);

            const popupContent = `
                <div class="popup-title">${{place.display_name}}</div>
                <div class="popup-date">${{place.date_range}}</div>
                <div class="popup-summary">${{place.summary}}</div>
            `;

            const marker = L.marker([place.lat, place.lng], {{ icon: icon }})
                .addTo(map)
                .bindPopup(popupContent, {{ maxWidth: 300 }});

            markers[place.id] = marker;

            // Click handler to scroll to first mention in text
            marker.on('click', () => {{
                const firstMention = document.querySelector(`.location[data-place-id="${{place.id}}"]`);
                if (firstMention) {{
                    // Remove active class from all locations
                    document.querySelectorAll('.location.active').forEach(el => el.classList.remove('active'));
                    // Add active class to this location
                    document.querySelectorAll(`.location[data-place-id="${{place.id}}"]`).forEach(el => el.classList.add('active'));
                    // Scroll into view
                    firstMention.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                }}
            }});
        }});

        // Add legend
        const legend = L.control({{ position: 'bottomright' }});
        legend.onAdd = function(map) {{
            const div = L.DomUtil.create('div', 'legend');
            div.innerHTML = '<h4>Countries</h4>';

            for (const [country, color] of Object.entries(countryColors)) {{
                div.innerHTML += `
                    <div class="legend-item">
                        <div class="legend-color" style="background: ${{color}}"></div>
                        <span>${{country}}</span>
                    </div>
                `;
            }}
            return div;
        }};
        legend.addTo(map);

        // Add click handlers to location spans
        document.querySelectorAll('.location').forEach(span => {{
            span.addEventListener('click', () => {{
                const placeId = span.dataset.placeId;
                const place = places.find(p => p.id === placeId);

                if (place && markers[placeId]) {{
                    // Remove active class from all locations
                    document.querySelectorAll('.location.active').forEach(el => el.classList.remove('active'));
                    // Add active class to all mentions of this place
                    document.querySelectorAll(`.location[data-place-id="${{placeId}}"]`).forEach(el => el.classList.add('active'));

                    // Pan map to location and open popup
                    map.setView([place.lat, place.lng], 10, {{ animate: true }});
                    markers[placeId].openPopup();
                }}
            }});
        }});

        // Journey route order (chronological)
        const routeOrder = [
            'southampton', 'crepon', 'le_hamel', 'arromanches', 'bayeux', 'creully', 'caen',
            'falaise', 'argentan', 'laigle', 'amiens', 'boulogne', 'desvres', 'calais',
            'bruges', 'knokke', 'goes', 'zuid_beveland', 'middelburg',
            'brussels', 'nieuport', 'antwerp', 'kapelle', 'namur', 'louvain',
            'wesel', 'munster', 'bielefeld', 'brunswick', 'hanover', 'berlin', 'dover'
        ];

        // Create journey segments with date info
        const journeySegments = [];
        const routePlaces = routeOrder
            .map(id => places.find(p => p.id === id))
            .filter(p => p && p.start_date);

        for (let i = 0; i < routePlaces.length - 1; i++) {{
            const from = routePlaces[i];
            const to = routePlaces[i + 1];
            const segmentDate = to.start_date; // Use arrival date for segment

            const polyline = L.polyline([
                [from.lat, from.lng],
                [to.lat, to.lng]
            ], {{
                color: '#8b4513',
                weight: 2,
                opacity: 0.5,
                dashArray: '5, 10',
                className: 'journey-segment'
            }}).addTo(map);

            journeySegments.push({{
                polyline: polyline,
                date: segmentDate,
                from: from.id,
                to: to.id
            }});
        }}

        // Initialize timeline slider
        const slider = document.getElementById('timeline-slider');
        noUiSlider.create(slider, {{
            start: [minDate.getTime(), maxDate.getTime()],
            connect: true,
            range: {{
                'min': minDate.getTime(),
                'max': maxDate.getTime()
            }},
            step: 24 * 60 * 60 * 1000 // 1 day
        }});

        // Event panel functions
        const eventPanel = document.getElementById('event-panel');
        const eventPanelOverlay = document.getElementById('event-panel-overlay');
        const eventPanelClose = document.getElementById('event-panel-close');
        let miniMap = null;
        let miniMapMarkers = [];

        function showEventPanel(event) {{
            // Populate panel content
            document.getElementById('event-panel-title').textContent = event.name;

            // Format date
            const dateStr = event.end_date
                ? `${{event.date}} - ${{event.end_date}}`
                : event.date;
            document.getElementById('event-panel-date').textContent = dateStr;

            // Show panel first so the map container has dimensions
            eventPanel.classList.add('open');
            eventPanelOverlay.classList.add('open');

            // Initialize or update mini map
            const mapContainer = document.getElementById('event-panel-map');

            // Clean up existing mini map
            if (miniMap) {{
                miniMap.remove();
                miniMap = null;
            }}
            miniMapMarkers = [];

            // Create mini map
            miniMap = L.map('event-panel-map', {{
                zoomControl: true,
                attributionControl: false,
                dragging: true,
                scrollWheelZoom: false
            }});

            // Add tile layer (same as main map)
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19
            }}).addTo(miniMap);

            // Determine bounds for the map
            let bounds = null;

            if (event.map_bounds) {{
                // Use predefined bounds
                bounds = L.latLngBounds(
                    [event.map_bounds.south, event.map_bounds.west],
                    [event.map_bounds.north, event.map_bounds.east]
                );
            }}

            // Add markers for related places
            if (event.related_places && event.related_places.length > 0) {{
                const relatedCoords = [];
                event.related_places.forEach(placeId => {{
                    const place = places.find(p => p.id === placeId);
                    if (place) {{
                        relatedCoords.push([place.lat, place.lng]);
                        const color = countryColors[place.country] || '#8b4513';
                        const miniMarker = L.circleMarker([place.lat, place.lng], {{
                            radius: 8,
                            fillColor: color,
                            color: '#fff',
                            weight: 2,
                            opacity: 1,
                            fillOpacity: 0.9
                        }}).addTo(miniMap);
                        miniMarker.bindTooltip(place.display_name, {{
                            permanent: false,
                            direction: 'top',
                            offset: [0, -8]
                        }});
                        miniMapMarkers.push(miniMarker);
                    }}
                }});

                // If no predefined bounds, fit to markers
                if (!bounds && relatedCoords.length > 0) {{
                    bounds = L.latLngBounds(relatedCoords);
                    bounds = bounds.pad(0.3); // Add some padding
                }}
            }}

            // Set the view
            if (bounds) {{
                // Small delay to ensure container is rendered
                setTimeout(() => {{
                    miniMap.fitBounds(bounds, {{ padding: [20, 20] }});
                    miniMap.invalidateSize();
                }}, 50);
            }} else {{
                // Default view of Western Europe
                miniMap.setView([49.5, 2.5], 6);
            }}

            // Show summary
            const summaryEl = document.getElementById('event-panel-summary');
            summaryEl.textContent = event.summary || event.description || '';

            // Show key facts if available
            const factsEl = document.getElementById('event-panel-facts');
            factsEl.innerHTML = '';
            if (event.key_facts && event.key_facts.length > 0) {{
                event.key_facts.forEach(fact => {{
                    const li = document.createElement('li');
                    li.textContent = fact;
                    factsEl.appendChild(li);
                }});
                factsEl.style.display = 'block';
            }} else {{
                factsEl.style.display = 'none';
            }}

            // Show source link
            const sourceEl = document.getElementById('event-panel-source');
            if (event.source && event.source.startsWith('http')) {{
                sourceEl.href = event.source;
                sourceEl.style.display = 'inline-block';
            }} else {{
                sourceEl.style.display = 'none';
            }}
        }}

        function hideEventPanel() {{
            eventPanel.classList.remove('open');
            eventPanelOverlay.classList.remove('open');

            // Clean up mini map after animation
            setTimeout(() => {{
                if (miniMap) {{
                    miniMap.remove();
                    miniMap = null;
                }}
                miniMapMarkers = [];
            }}, 300);
        }}

        // Panel close handlers
        eventPanelClose.addEventListener('click', hideEventPanel);
        eventPanelOverlay.addEventListener('click', hideEventPanel);

        // Close panel on Escape key
        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') {{
                hideEventPanel();
            }}
        }});

        // Event markers
        const eventMarkersContainer = document.getElementById('event-markers');
        timeline.events.forEach(event => {{
            const percent = dateToPercent(event.date);
            if (percent >= 0 && percent <= 100) {{
                const dot = document.createElement('div');
                dot.className = `event-dot ${{event.type}}`;
                dot.style.left = `${{percent}}%`;
                dot.innerHTML = `<div class="event-tooltip">${{event.name}}<br><small>${{event.date}}</small></div>`;
                dot.addEventListener('click', () => {{
                    const eventDate = new Date(event.date).getTime();
                    const rangeWidth = 30 * 24 * 60 * 60 * 1000; // 30 days window
                    slider.noUiSlider.set([eventDate - rangeWidth/2, eventDate + rangeWidth/2]);

                    // For historical events, show the detail panel
                    if (event.type === 'historical') {{
                        showEventPanel(event);
                    }}

                    // For diary events, scroll to related place in text
                    if (event.type === 'diary' && event.related_places && event.related_places.length > 0) {{
                        const placeId = event.related_places[0];
                        const firstMention = document.querySelector(`.location[data-place-id="${{placeId}}"]`);
                        if (firstMention) {{
                            // Remove active class from all locations
                            document.querySelectorAll('.location.active').forEach(el => el.classList.remove('active'));
                            // Add active class to this location
                            document.querySelectorAll(`.location[data-place-id="${{placeId}}"]`).forEach(el => el.classList.add('active'));
                            // Scroll into view with slight delay to let slider update first
                            setTimeout(() => {{
                                firstMention.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                            }}, 100);
                            // Also open the marker popup
                            if (markers[placeId]) {{
                                const place = places.find(p => p.id === placeId);
                                if (place) {{
                                    map.setView([place.lat, place.lng], 9, {{ animate: true }});
                                    markers[placeId].openPopup();
                                }}
                            }}
                        }}
                    }}
                }});
                eventMarkersContainer.appendChild(dot);
            }}
        }});

        // Update display based on slider
        function updateTimeline(values) {{
            const startTs = parseInt(values[0]);
            const endTs = parseInt(values[1]);
            const startDate = timestampToDate(startTs);
            const endDate = timestampToDate(endTs);

            // Update date display
            document.getElementById('date-display').textContent =
                formatDate(startDate) + ' - ' + formatDate(endDate);

            // Filter markers
            places.forEach(place => {{
                const marker = markers[place.id];
                if (!marker) return;

                const markerEl = marker.getElement();
                if (!markerEl) return;

                // Check if place is within date range
                let visible = false;
                if (place.start_date === null) {{
                    // Home (Middleton) - always visible
                    visible = true;
                }} else {{
                    const placeStart = new Date(place.start_date).getTime();
                    const placeEnd = new Date(place.end_date).getTime();
                    // Show if any overlap with selected range
                    visible = placeStart <= endTs && placeEnd >= startTs;
                }}

                if (visible) {{
                    markerEl.classList.remove('marker-dimmed');
                    markerEl.style.opacity = '1';
                }} else {{
                    markerEl.classList.add('marker-dimmed');
                    markerEl.style.opacity = '0.2';
                }}
            }});

            // Filter journey segments
            journeySegments.forEach(segment => {{
                const segmentDate = new Date(segment.date).getTime();
                if (segmentDate <= endTs && segmentDate >= startTs) {{
                    segment.polyline.setStyle({{ opacity: 0.7 }});
                }} else if (segmentDate <= endTs) {{
                    segment.polyline.setStyle({{ opacity: 0.3 }});
                }} else {{
                    segment.polyline.setStyle({{ opacity: 0.1 }});
                }}
            }});

            // Dim text locations outside date range
            document.querySelectorAll('.location').forEach(span => {{
                const placeId = span.dataset.placeId;
                const place = places.find(p => p.id === placeId);
                if (!place) return;

                let visible = false;
                if (place.start_date === null) {{
                    visible = true;
                }} else {{
                    const placeStart = new Date(place.start_date).getTime();
                    const placeEnd = new Date(place.end_date).getTime();
                    visible = placeStart <= endTs && placeEnd >= startTs;
                }}

                if (visible) {{
                    span.classList.remove('dimmed');
                }} else {{
                    span.classList.add('dimmed');
                }}
            }});
        }}

        slider.noUiSlider.on('update', updateTimeline);

        // Quick jump buttons
        document.getElementById('btn-dday').addEventListener('click', () => {{
            const ddayDate = new Date('1944-06-06').getTime();
            const rangeWidth = 60 * 24 * 60 * 60 * 1000; // 60 days
            slider.noUiSlider.set([ddayDate - 7 * 24 * 60 * 60 * 1000, ddayDate + rangeWidth]);
        }});

        document.getElementById('btn-veday').addEventListener('click', () => {{
            const vedayDate = new Date('1945-05-08').getTime();
            const rangeWidth = 30 * 24 * 60 * 60 * 1000; // 30 days
            slider.noUiSlider.set([vedayDate - rangeWidth/2, vedayDate + rangeWidth/2]);
        }});

        document.getElementById('btn-full').addEventListener('click', () => {{
            slider.noUiSlider.set([minDate.getTime(), maxDate.getTime()]);
        }});

        // Play animation
        let isPlaying = false;
        let animationFrame = null;
        const playBtn = document.getElementById('play-btn');

        function animate() {{
            const values = slider.noUiSlider.get();
            const currentEnd = parseInt(values[1]);
            const step = 7 * 24 * 60 * 60 * 1000; // 1 week per frame

            if (currentEnd < maxDate.getTime()) {{
                const newEnd = Math.min(currentEnd + step, maxDate.getTime());
                slider.noUiSlider.set([minDate.getTime(), newEnd]);
                animationFrame = setTimeout(animate, 100);
            }} else {{
                stopAnimation();
            }}
        }}

        function startAnimation() {{
            isPlaying = true;
            playBtn.innerHTML = '&#10074;&#10074;'; // Pause icon
            playBtn.classList.add('active');
            // Reset to start
            slider.noUiSlider.set([minDate.getTime(), minDate.getTime() + 30 * 24 * 60 * 60 * 1000]);
            animate();
        }}

        function stopAnimation() {{
            isPlaying = false;
            playBtn.innerHTML = '&#9658;'; // Play icon
            playBtn.classList.remove('active');
            if (animationFrame) {{
                clearTimeout(animationFrame);
                animationFrame = null;
            }}
        }}

        playBtn.addEventListener('click', () => {{
            if (isPlaying) {{
                stopAnimation();
            }} else {{
                startAnimation();
            }}
        }});

        // Initial update
        updateTimeline([minDate.getTime(), maxDate.getTime()]);
    </script>
</body>
</html>
'''


def main():
    base_dir = Path(__file__).parent
    diary_path = base_dir / "complete-diary.md"
    places_path = base_dir / "places.json"
    timeline_path = base_dir / "data" / "timeline.json"
    output_path = base_dir / "index.html"

    print("Loading diary...")
    diary_html = load_diary(diary_path)

    print("Loading places...")
    places = load_places(places_path)
    print(f"  Found {len(places)} locations")

    print("Loading timeline...")
    timeline = load_timeline(timeline_path)
    print(f"  Found {len(timeline['events'])} events")

    print("Processing diary text...")
    diary_html = wrap_locations_in_html(diary_html, places)

    print("Getting version info...")
    version = get_version_info()
    print(f"  Version: {version['hash']} ({version['generated']})")

    print("Generating HTML...")
    html = generate_html(diary_html, places, timeline, version)

    print(f"Writing output to {output_path}...")
    output_path.write_text(html, encoding="utf-8")

    print("Done!")


if __name__ == "__main__":
    main()
