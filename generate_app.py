#!/usr/bin/env python3
"""
Generate an interactive HTML map application from Edgar Hopkins' WW2 diary.

Reads the diary markdown and places.json, then generates a single self-contained
HTML file with an interactive Leaflet map alongside the diary text.
"""

import json
import re
from pathlib import Path

import markdown


def load_diary(path: Path) -> str:
    """Load and convert diary markdown to HTML."""
    md_content = path.read_text(encoding="utf-8")
    md = markdown.Markdown(extensions=["extra"])
    return md.convert(md_content)


def load_places(path: Path) -> list[dict]:
    """Load places data from JSON file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return data["places"]


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


def generate_html(diary_html: str, places: list[dict]) -> str:
    """Generate the complete HTML application."""
    places_json = json.dumps(places, indent=2)

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
        }}

        #map {{
            width: 100%;
            height: 100%;
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
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="diary-panel">
            <div class="diary-content">
                {diary_html}
            </div>
        </div>
        <div class="map-panel">
            <div id="map"></div>
        </div>
    </div>

    <script>
        const places = {places_json};

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

        // Draw journey path
        const journeyCoords = places
            .filter(p => p.id !== 'middleton' && p.id !== 'southend') // Skip non-journey locations
            .map(p => [p.lat, p.lng]);

        // Create a simplified route (chronological order based on the array order)
        const routeOrder = [
            'southampton', 'crepon', 'le_hamel', 'arromanches', 'bayeux', 'creully', 'caen',
            'falaise', 'argentan', 'laigle', 'amiens', 'boulogne', 'desvres', 'calais',
            'bruges', 'knokke', 'kapelle', 'antwerp', 'nieuport', 'goes', 'zuid_beveland',
            'middelburg', 'louvain', 'brussels', 'namur', 'wesel', 'munster', 'bielefeld',
            'brunswick', 'hanover', 'berlin', 'dover', 'middleton'
        ];

        const routeCoords = routeOrder
            .map(id => places.find(p => p.id === id))
            .filter(p => p)
            .map(p => [p.lat, p.lng]);

        L.polyline(routeCoords, {{
            color: '#8b4513',
            weight: 2,
            opacity: 0.5,
            dashArray: '5, 10'
        }}).addTo(map);
    </script>
</body>
</html>
'''


def main():
    base_dir = Path(__file__).parent
    diary_path = base_dir / "complete-diary.md"
    places_path = base_dir / "places.json"
    output_path = base_dir / "index.html"

    print("Loading diary...")
    diary_html = load_diary(diary_path)

    print("Loading places...")
    places = load_places(places_path)
    print(f"  Found {len(places)} locations")

    print("Processing diary text...")
    diary_html = wrap_locations_in_html(diary_html, places)

    print("Generating HTML...")
    html = generate_html(diary_html, places)

    print(f"Writing output to {output_path}...")
    output_path.write_text(html, encoding="utf-8")

    print("Done!")


if __name__ == "__main__":
    main()
