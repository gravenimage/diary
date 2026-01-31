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
