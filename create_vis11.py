
import json
import csv
import math
from pathlib import Path

# Run this file from your FIT3179_A2 project folder.
data_folder = Path("data")

with open(data_folder / "australian_states.geojson", encoding="utf-8") as f:
    australia = json.load(f)

with open(data_folder / "04_ala_state_year_counts.csv", newline="", encoding="utf-8-sig") as f:
    counts = list(csv.DictReader(f))

# Each year's largest state count determines the reference size.
max_by_year = {}
for row in counts:
    year = int(row["year"])
    value = float(row["population_count"])
    max_by_year[year] = max(max_by_year.get(year, 0), value)


def all_points(coordinates):
    """Recursively find coordinate pairs in a GeoJSON geometry."""
    if not coordinates:
        return
    if isinstance(coordinates[0], (int, float)):
        yield coordinates
    else:
        for part in coordinates:
            yield from all_points(part)


def resize_coordinates(coordinates, cx, cy, factor):
    """Scale a geometry around its own centre."""
    if not coordinates:
        return coordinates

    if isinstance(coordinates[0], (int, float)):
        x, y = coordinates[:2]
        return [
            round(cx + (x - cx) * factor, 6),
            round(cy + (y - cy) * factor, 6)
        ]

    return [
        resize_coordinates(part, cx, cy, factor)
        for part in coordinates
    ]


features = []

for row in counts:
    state = row["state"]
    year = int(row["year"])
    count = float(row["population_count"])

    original = next(
        (
            feature for feature in australia["features"]
            if feature["properties"]["STATE_NAME"] == state
        ),
        None
    )

    if original is None:
        print("State not found:", state)
        continue

    geometry = original["geometry"]
    points = list(all_points(geometry["coordinates"]))

    # Bounding-box centre of the original state.
    cx = (min(p[0] for p in points) + max(p[0] for p in points)) / 2
    cy = (min(p[1] for p in points) + max(p[1] for p in points)) / 2

    # Square root because shape area changes with scale squared.
    # Maximum state is kept at 85% of original linear size.
    factor = 0.85 * math.sqrt(count / max_by_year[year])

    resized = resize_coordinates(
        geometry["coordinates"], cx, cy, factor
    )

    features.append({
        "type": "Feature",
        "properties": {
            "state": state,
            "year": year,
            "population_count": int(count)
        },
        "geometry": {
            "type": geometry["type"],
            "coordinates": resized
        }
    })

output = {
    "type": "FeatureCollection",
    "features": features
}

with open(data_folder / "vis11_cartogram.geojson", "w", encoding="utf-8") as f:
    json.dump(output, f)

print(f"Created cartogram with {len(features)} state-year shapes.")
