# Agent Instructions

This project uses **bd** (beads) for issue tracking. Run `bd onboard` to get started.

## Quick Reference

```bash
bd ready              # Find available work
bd show <id>          # View issue details
bd update <id> --status in_progress  # Claim work
bd close <id>         # Complete work
bd sync               # Sync with git
```

## Landing the Plane (Session Completion)

**When ending a work session**, you MUST complete ALL steps below. Work is NOT complete until `git push` succeeds.

**MANDATORY WORKFLOW:**

1. **File issues for remaining work** - Create issues for anything that needs follow-up
2. **Run quality gates** (if code changed) - Tests, linters, builds
3. **Update issue status** - Close finished work, update in-progress items
4. **PUSH TO REMOTE** - This is MANDATORY:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Clean up** - Clear stashes, prune remote branches
6. **Verify** - All changes committed AND pushed
7. **Hand off** - Provide context for next session

**CRITICAL RULES:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing - that leaves work stranded locally
- NEVER say "ready to push when you are" - YOU must push
- If push fails, resolve and retry until it succeeds

---

# Project Information

This is a repository containing my grandfather's WW2 diary, presented as an interactive web application.

**Live site**: https://gravenimage.github.io/diary/

## About the Diary

**Author**: Edgar Hopkins, 90th (City of London) Battery, 113th Regiment, 76th Brigade - an anti-aircraft unit.

**Period**: June 1944 (D-Day) through February 1946 (demobilization from Berlin)

**Journey**: Southampton → Normandy (Crépon) → France (Caen, Falaise, Amiens, Boulogne) → Belgium (Bruges, Knokke) → Netherlands (Zuid Beveland) → Germany (Berlin)

The diary chronicles Edgar's experiences as an AA gunner defending the D-Day beachhead and following the Allied advance across Western Europe.

---

## Project Structure

```
diary/
├── complete-diary.md          # Full diary text (~30k tokens)
├── places.json                 # Location data (35 places)
├── data/
│   ├── timeline.json          # Timeline events (historical + diary)
│   ├── unit_history.json      # Military unit records and events
│   └── event_maps/            # SVG maps (legacy, not currently used)
├── scripts/
│   ├── research_events.py     # Generate base timeline data
│   └── fetch_event_data.py    # Enrich with Wikipedia summaries
├── tests/
│   ├── conftest.py            # Shared pytest fixtures
│   ├── test_data_validation.py
│   ├── test_references.py
│   ├── test_historical_events.py
│   └── test_chronology.py
├── generate_app.py            # Main generator script
├── index.html                 # Generated web application
├── pyproject.toml             # Python dependencies
└── .github/workflows/
    └── deploy.yml             # CI/CD pipeline
```

---

## Data Structures

### places.json

Location data for places mentioned in the diary:

```json
{
  "id": "crepon",
  "display_name": "Crépon",
  "lat": 49.3167,
  "lng": -0.5333,
  "country": "France",
  "keywords": ["Crepon", "Crépon"],
  "summary": "First gun position in France...",
  "date_range": "7 June - 31 August 1944",
  "start_date": "1944-06-07",
  "end_date": "1944-08-31"
}
```

### data/timeline.json

Timeline events with two types: `historical` and `diary`.

**Historical events** (blue dots) include enriched data:

```json
{
  "id": "dday",
  "name": "D-Day (Operation Overlord)",
  "date": "1944-06-06",
  "end_date": null,
  "type": "historical",
  "description": "Allied invasion of Normandy begins...",
  "source": "https://en.wikipedia.org/wiki/Normandy_landings",
  "related_places": ["crepon", "le_hamel", "arromanches"],
  "summary": "Wikipedia summary (1-2 paragraphs)...",
  "key_facts": [
    "156,000 Allied troops landed on first day",
    "5 beaches: Utah, Omaha, Gold, Juno, Sword",
    "Over 4,400 Allied deaths on D-Day"
  ],
  "map_bounds": {
    "north": 49.5,
    "south": 49.2,
    "east": -0.3,
    "west": -1.2
  }
}
```

**Diary events** (red dots) are simpler:

```json
{
  "id": "edgar_lands",
  "name": "Edgar lands in France",
  "date": "1944-06-07",
  "type": "diary",
  "description": "Edgar arrives at Crepon gun site...",
  "source": "diary",
  "related_places": ["crepon", "le_hamel"]
}
```

### data/unit_history.json

Official military unit history for Edgar's regiment and brigade. Contains four main sections:

**Sources** - Reference materials with reliability ratings:
```json
{
  "id": "wiki_113haa",
  "type": "encyclopedia",
  "title": "113th Heavy Anti-Aircraft Regiment, Royal Artillery",
  "url": "https://en.wikipedia.org/wiki/...",
  "accessed": "2026-01-31",
  "reliability": "secondary"
}
```

**Units** - Military unit definitions:
```json
{
  "id": "113_haa_rgt",
  "designation": "113th Heavy Anti-Aircraft Regiment, Royal Artillery (TA)",
  "short_name": "113 HAA Rgt",
  "type": "regiment",
  "branch": "Royal Artillery",
  "role": "heavy_anti-aircraft",
  "formed": "1940-11-25",
  "disbanded": "1945-04-30",
  "parent_unit": "76_aa_bde",
  "subordinate_units": ["362_haa_bty", "366_haa_bty", "391_haa_bty"],
  "equipment": ["3.7-inch AA gun (24 guns total)"]
}
```

**Events** - Unit operational history:
```json
{
  "id": "dday_gold_beach",
  "date": "1944-06-06",
  "unit_id": "76_aa_bde",
  "type": "combat",
  "category": "amphibious_assault",
  "name": "D-Day: 76 AA Brigade lands on Gold Beach",
  "description": "76th AA Bde supported XXX Corps landing on Gold Beach...",
  "location": {
    "name": "Gold Beach, Normandy",
    "lat": 49.34,
    "lng": -0.63,
    "country": "France"
  },
  "sources": ["wiki_76aabde", "wiki_113haa"],
  "tags": ["combat", "dday", "overlord", "gold_beach"],
  "edgar_relevance": "high",
  "related_diary_events": ["dday", "edgar_lands"]
}
```

**Classification Schema** - Controlled vocabularies:
- `event_types`: formation, combat, deployment, movement, etc.
- `event_categories`: air_defence, ground_support, amphibious_assault, etc.
- `edgar_relevance_levels`: none, low, medium, high
- `source_reliability`: primary, secondary, tertiary
- `tags`: theatre, operation, action_type, significance

**Units documented:**
- 76th Anti-Aircraft Brigade (parent formation)
- 113th Heavy Anti-Aircraft Regiment (Edgar's regiment)
- 362, 366, 391 HAA Batteries (constituent batteries)

**Events documented (26 total):**
- Formation and training (1940-1943)
- D-Day and Normandy campaign (June-August 1944)
- Advance through France (September 1944)
- Battle of the Scheldt (October-November 1944)
- Antwerp defence and Operation Bodenplatte (1944-1945)
- End of war and disbandment (1945-1946)

---

## Features

### Interactive Map
- Leaflet.js map with OpenStreetMap tiles
- Color-coded markers by country (England=red, France=blue, Belgium=orange, Netherlands=orange, Germany=grey)
- Dashed journey route line
- Click markers to see details and scroll to diary text

### Timeline Slider
- Interactive date range slider (noUiSlider)
- Event dots above slider: blue (historical) / red (diary)
- Quick-jump buttons: D-Day, VE Day, Full Journey
- Play animation button

### Historical Event Panel
- Slide-out panel when clicking blue (historical) event dots
- Mini Leaflet map zoomed to event region
- Circle markers for related places
- Wikipedia summary (1-2 paragraphs)
- Key facts (bullet points)
- Link to Wikipedia source

### Text Highlighting
- Location mentions are highlighted and clickable
- Clicking a location pans map and opens popup
- Locations dim/brighten based on timeline selection

### Version Indicator
- Git commit hash and build date displayed next to diary title
- Hover tooltip shows full version details
- Helps verify which version is deployed to GitHub Pages

---

## Scripts

### generate_app.py

Main generator - creates the single-page web application.

```bash
uv run python generate_app.py
```

### scripts/fetch_event_data.py

Enriches historical events with Wikipedia summaries and key facts:

```bash
uv run python scripts/fetch_event_data.py
```

This script:
1. Fetches summaries from Wikipedia API
2. Uses fallback data for key facts (pre-researched)
3. Adds map_bounds for mini map display
4. Updates data/timeline.json in place

### scripts/research_events.py

Generates base timeline data (historical events + diary milestones):

```bash
uv run python scripts/research_events.py
```

---

## Testing

55 tests covering data validation, references, content quality, and chronology.

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_data_validation.py -v

# Stop on first failure
uv run pytest tests/ -v -x
```

### Test Categories

| File | Tests | Purpose |
|------|-------|---------|
| test_data_validation.py | 23 | Structure, dates, coordinates |
| test_references.py | 9 | Cross-file references |
| test_historical_events.py | 13 | Content quality |
| test_chronology.py | 10 | Date ordering, historical accuracy |

### What Tests Catch

- Missing required fields
- Invalid date formats
- Coordinates outside Western Europe
- Broken related_places references
- Missing Wikipedia summaries
- Unsorted timeline
- Historical date errors (e.g., D-Day not on June 6)

---

## CI/CD Pipeline

GitHub Actions workflow (`.github/workflows/deploy.yml`):

1. **Test job**: Runs pytest on every push
2. **Build job**: Regenerates index.html
3. **Deploy job**: Publishes to GitHub Pages

Deployment is automatic on push to `master`.

**Manual trigger**:
```bash
gh workflow run deploy.yml
```

**View status**:
```bash
gh run list --workflow=deploy.yml
```

---

## Development Workflow

### Adding a New Historical Event

1. Add event to `data/timeline.json`:
   ```json
   {
     "id": "new_event",
     "name": "Event Name",
     "date": "1944-MM-DD",
     "type": "historical",
     "description": "Brief description",
     "source": "https://en.wikipedia.org/wiki/...",
     "related_places": ["place_id"]
   }
   ```

2. Run fetch script to enrich:
   ```bash
   uv run python scripts/fetch_event_data.py
   ```

3. Run tests:
   ```bash
   uv run pytest tests/ -v
   ```

4. Regenerate app:
   ```bash
   uv run python generate_app.py
   ```

5. Commit and push (auto-deploys)

### Adding a New Place

1. Add to `places.json` with required fields:
   - id, display_name, lat, lng, country, keywords, summary, date_range, start_date, end_date

2. Run tests to validate:
   ```bash
   uv run pytest tests/test_data_validation.py -v
   ```

3. Regenerate and push

---

## Dev Notes

- Use `uv` for all Python operations
- Tests run automatically on push
- Site auto-deploys to GitHub Pages
- Timeline events must be sorted by date (tests enforce this)
- Historical events need: summary, key_facts, map_bounds, source URL
