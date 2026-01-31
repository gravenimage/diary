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

# Project information

This is a repository containing my grandfather's WW2 diary.

## About the Diary

**Author**: Edgar Hopkins, 90th (City of London) Battery, 113th Regiment, 76th Brigade - an anti-aircraft unit.

**Period**: June 1944 (D-Day) through February 1946 (demobilization from Berlin)

**Journey**: Southampton > Normandy (Crépon) > France (Caen, Falaise, Amiens, Boulogne) > Belgium (Bruges, Knokke) > Netherlands (Zuid Beveland) > Germany (Berlin)

The diary chronicles Edgar's experiences as an AA gunner defending the D-Day beachhead and following the Allied advance across Western Europe. It includes vivid descriptions of combat, daily life on gun sites, friendships with fellow soldiers (especially Frank Davis and Alec Moffat), and his longing for his wife Winnie.

## Project Structure

- **complete-diary.md** - The full diary text in markdown format (~30k tokens)
- **places.json** - Location data with coordinates, date ranges, and summaries for 35 places mentioned in the diary
- **generate_app.py** - Python script that generates the interactive web viewer
- **index.html** - Generated single-page web application with interactive map

## How It Works

The `generate_app.py` script:
1. Loads the diary markdown and converts it to HTML
2. Loads place data from `places.json`
3. Wraps location mentions in the text with clickable `<span>` tags (using keyword matching)
4. Generates a self-contained HTML file with:
   - Split-pane layout: diary text (left) and Leaflet map (right)
   - Color-coded markers by country (England=red, France=blue, Belgium=orange, Netherlands=orange, Germany=grey)
   - Clickable locations that pan the map and highlight text
   - A dashed line showing the journey route
   - Responsive design for mobile

## Running the Generator

```bash
uv run generate_app.py
```

This regenerates `index.html` from the current diary and places data.

## Dev Notes

Whenever manipulating or running Python commands or scripts, strongly prefer to use the `uv` command to manage environments, run scripts, install packages etc.
