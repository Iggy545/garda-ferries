#!/usr/bin/env python3
"""Fetch the lake's shape and the ferry piers, and write garda-geography.json.

This is the only part of the project that needs a network connection, and it is
run rarely — the result is committed, and `build.py` reads the file. Re-run it
only if a stop is added or the outline looks wrong.

    python fetch_geo.py

Sources: the lake outline from Nominatim, the piers from OpenStreetMap's
amenity=ferry_terminal nodes via Overpass. Both are ODbL-licensed OpenStreetMap
data, credited in the app.
"""

import json
import math
import pathlib
import sys
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).parent
OUTPUT = HERE / "garda-geography.json"

AGENT = "garda-ferries-app/1.0 (personal timetable project)"
NOMINATIM = "https://nominatim.openstreetmap.org/search"
OVERPASS = "https://overpass-api.de/api/interpreter"
BBOX = (45.42, 10.48, 45.90, 10.90)  # south, west, north, east

# Our timetable's stop names on the left, the name OpenStreetMap gives the pier on
# the right. Kept explicit rather than fuzzy-matched: several piers are near
# neighbours ("Limone centro" vs "Limone P multipiano") and a wrong guess would put
# a dot in a plausible but incorrect place.
PIERS = {
    "PESCHIERA": "Peschiera del Garda",
    "SIRMIONE": "Sirmione",
    "DESENZANO": "Desenzano",
    "PADENGHE": "Padenghe",
    "MONIGA": "Moniga del Garda",
    "MANERBA (Dusano)": "Manerba del Garda",
    "PORTESE": "Porto Portese",
    "SALO": "Salò",
    "GARDONE": "Gardone",
    "MADERNO": "Maderno",
    "BOGLIACO": "Bogliaco",
    "GARGNANO": "Gargnano",
    "TIGNALE": "Tignale",
    "CAMPIONE (Tremosine)": "Campione",
    "LIMONE centro": "Limone centro",
    "LIMONE multipiano": "Limone P multipiano",
    "RIVA": "Riva del Garda",
    "TORBOLE": "Torbole",
    "MALCESINE centro": "Malcesine",
    "ASSENZA di Brenzone": "Assenza",
    "BRENZONE": "Brenzone",
    "CASTELLETTO": "Castelletto",
    "TORRI": "Torri del Benaco",
    "GARDA": "Garda",
    "BARDOLINO": "Bardolino",
    "CISANO": "Cisano",
    "LAZISE": "Lazise",
}

# The raw outline is over 10,000 points, far more than a phone-sized map can show.
# Tuned by eye: coarse enough to keep the file small, fine enough that the bays
# around Salò and the northern fjord still read correctly.
SIMPLIFY_TOLERANCE = 0.00035  # degrees, roughly 30 m


def get(url, data=None):
    request = urllib.request.Request(url, data=data, headers={"User-Agent": AGENT})
    with urllib.request.urlopen(request, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def perpendicular_distance(point, start, end):
    (x, y), (x1, y1), (x2, y2) = point, start, end
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return math.hypot(x - x1, y - y1)
    return abs(dy * x - dx * y + x2 * y1 - y2 * x1) / math.hypot(dx, dy)


def simplify(points, tolerance):
    """Ramer-Douglas-Peucker, iterative so a 10k-point ring cannot blow the stack."""
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        start, end = stack.pop()
        worst, at = 0.0, None
        for i in range(start + 1, end):
            d = perpendicular_distance(points[i], points[start], points[end])
            if d > worst:
                worst, at = d, i
        if at is not None and worst > tolerance:
            keep[at] = True
            stack.append((start, at))
            stack.append((at, end))
    return [p for p, k in zip(points, keep) if k]


def fetch_outline():
    query = urllib.parse.urlencode({
        "q": "Lago di Garda",
        "format": "json",
        "polygon_geojson": 1,
        "limit": 1,
    })
    results = get(f"{NOMINATIM}?{query}")
    if not results:
        sys.exit("Nominatim returned nothing for 'Lago di Garda'")
    geometry = results[0]["geojson"]
    if geometry["type"] == "Polygon":
        ring = geometry["coordinates"][0]
    else:  # MultiPolygon — take the largest ring, which is the lake itself
        ring = max((p[0] for p in geometry["coordinates"]), key=len)
    return [(round(lon, 6), round(lat, 6)) for lon, lat in ring]


def fetch_piers():
    query = (
        f"[out:json][timeout:60];"
        f'(node["amenity"="ferry_terminal"]{BBOX};'
        f'way["amenity"="ferry_terminal"]{BBOX};);out center;'
    )
    payload = urllib.parse.urlencode({"data": query}).encode()
    elements = get(OVERPASS, payload)["elements"]

    by_name = {}
    for element in elements:
        name = element.get("tags", {}).get("name")
        if not name:
            continue
        lat = element.get("lat") or element["center"]["lat"]
        lon = element.get("lon") or element["center"]["lon"]
        by_name[name] = (round(lon, 6), round(lat, 6))

    found, missing = {}, []
    for stop, osm_name in PIERS.items():
        if osm_name in by_name:
            found[stop] = by_name[osm_name]
        else:
            missing.append(f"{stop} (looked for {osm_name!r})")
    if missing:
        sys.exit("No pier found for:\n  " + "\n  ".join(missing))
    return found


def main():
    print("Fetching the lake outline…")
    ring = fetch_outline()
    simplified = simplify(ring, SIMPLIFY_TOLERANCE)
    print(f"  {len(ring)} points simplified to {len(simplified)}")

    print("Fetching ferry piers…")
    piers = fetch_piers()
    print(f"  {len(piers)} of {len(PIERS)} matched")

    OUTPUT.write_text(json.dumps({
        "source": "OpenStreetMap contributors, ODbL",
        "outline": simplified,
        "piers": piers,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {OUTPUT.name} ({OUTPUT.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
