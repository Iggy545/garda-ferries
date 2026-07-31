#!/usr/bin/env python3
"""Generate index.html from the timetable JSON.

The app ships as a single self-contained HTML file so it works offline on a
phone. This script bakes the timetable into app.template.html at the
/*__DATA__*/ marker. Re-run it after editing the JSON, or next season after
transcribing a new PDF.

    python build.py
"""

import datetime
import json
import math
import pathlib
import sys

# Bump this when something user-visible changes, and give the same number a heading
# in CHANGELOG.md. The build date beside it in the app is what actually tells you
# whether the phone has picked up a new copy.
VERSION = "1.2"

HERE = pathlib.Path(__file__).parent
SOURCE = HERE / "garda-ferry-2026-summer.json"
GEO_FILE = HERE / "garda-geography.json"
TEMPLATE = HERE / "app.template.html"
OUTPUT = HERE / "index.html"

# The map is drawn tall, as the lake is: about 50 km north to south and 28 km across
# at its widest. LAKE_HEIGHT sets the drawing size in SVG units and the width follows
# from the real proportions. MARGIN leaves room for the labels beside it.
LAKE_HEIGHT = 520
MARGIN = 72

# Stops in geographic order around the lake, anticlockwise from the south-east
# corner. The PDF lists them in timetable order, which is not useful in a
# dropdown. Each entry is (key in the JSON, label shown in the app).
GEOGRAPHY = [
    ("South", [
        ("PESCHIERA", "Peschiera"),
        ("SIRMIONE", "Sirmione"),
        ("DESENZANO", "Desenzano"),
        ("PADENGHE", "Padenghe"),
    ]),
    ("West shore", [
        ("MONIGA", "Moniga"),
        ("MANERBA (Dusano)", "Manerba (Dusano)"),
        ("PORTESE", "Portese"),
        ("SALO", "Salò"),
        ("GARDONE", "Gardone"),
        ("MADERNO", "Maderno"),
        ("BOGLIACO", "Bogliaco"),
        ("GARGNANO", "Gargnano"),
        ("TIGNALE", "Tignale"),
        ("CAMPIONE (Tremosine)", "Campione"),
        ("LIMONE centro", "Limone (centro)"),
        ("LIMONE multipiano", "Limone (multipiano)"),
    ]),
    ("North", [
        ("RIVA", "Riva del Garda"),
        ("TORBOLE", "Torbole"),
    ]),
    ("East shore", [
        ("MALCESINE centro", "Malcesine"),
        ("ASSENZA di Brenzone", "Assenza"),
        ("BRENZONE", "Brenzone"),
        ("CASTELLETTO", "Castelletto"),
        ("TORRI", "Torri del Benaco"),
        ("GARDA", "Garda"),
        ("BARDOLINO", "Bardolino"),
        ("CISANO", "Cisano"),
        ("LAZISE", "Lazise"),
    ]),
]


def to_minutes(hhmm):
    hours, minutes = hhmm.split(":")
    return int(hours) * 60 + int(minutes)


LABEL_GAP = 15  # SVG units needed between two labels before they touch


def declutter(points):
    """Nudge labels apart where piers sit almost on top of each other.

    The two Limone piers are 600 m apart, which at this scale is about six units —
    their names would overprint. Each shore is handled separately: push labels down
    until they clear, then shift the whole run back up by half the total push so the
    group stays centred on the piers it belongs to.
    """
    for side in (-1, 1):
        run = sorted((p for p in points if p[2] == side), key=lambda p: p[1])
        for earlier, later in zip(run, run[1:]):
            if later[3] - earlier[3] < LABEL_GAP:
                later[3] = earlier[3] + LABEL_GAP
        if run:
            drift = (run[-1][3] - run[-1][1]) / 2
            for point in run:
                point[3] = round(point[3] - drift, 1)


def build_map(order):
    """Project the lake outline and piers into SVG coordinates.

    Longitude degrees are shorter than latitude ones, by the cosine of the latitude,
    so they are scaled before anything else — without that the lake comes out about
    40% too wide and stops sitting on the wrong side of a bay.
    """
    geo = json.loads(GEO_FILE.read_text(encoding="utf-8"))
    outline, piers = geo["outline"], geo["piers"]

    lats = [lat for _, lat in outline]
    lons = [lon for lon, _ in outline]
    squeeze = math.cos(math.radians(sum(lats) / len(lats)))

    west, east = min(lons) * squeeze, max(lons) * squeeze
    south, north = min(lats), max(lats)
    scale = LAKE_HEIGHT / (north - south)
    width = (east - west) * scale

    def project(lon, lat):
        # y is flipped: latitude climbs northward, SVG counts downward.
        return (round((lon * squeeze - west) * scale + MARGIN, 1),
                round((north - lat) * scale + MARGIN, 1))

    path = "M" + "L".join(f"{x} {y}" for x, y in (project(lon, lat) for lon, lat in outline)) + "Z"

    middle = (west + east) / 2
    points = []
    for stop in order:
        lon, lat = piers[stop]
        x, y = project(lon, lat)
        # Labels go on the outside of whichever shore the pier is on, so they never
        # sit over the water where the route lines are drawn.
        points.append([x, y, -1 if lon * squeeze < middle else 1, y])

    declutter(points)

    return {
        "w": round(width + MARGIN * 2, 1),
        "h": round(LAKE_HEIGHT + MARGIN * 2, 1),
        "path": path,
        "pts": points,
    }


def main():
    timetable = json.loads(SOURCE.read_text(encoding="utf-8"))

    order = [key for _, group in GEOGRAPHY for key, _ in group]
    index_of = {key: i for i, key in enumerate(order)}

    stops = [
        {"n": label, "g": group_name}
        for group_name, group in GEOGRAPHY
        for _, label in group
    ]

    sailings = []
    seen_stops = set()
    reordered = []
    for direction, entries in timetable["directions"].items():
        for sailing in entries:
            calls = []
            for stop, time in sailing["stops"].items():
                seen_stops.add(stop)
                if stop not in index_of:
                    sys.exit(f"Stop {stop!r} is missing from GEOGRAPHY in build.py")
                calls.append([index_of[stop], to_minutes(time)])
            # A handful of sailings are stored in the order the PDF printed the
            # rows rather than the order the boat calls. The times are the
            # authoritative part, so sort by them; the app relies on a sailing's
            # calls running forwards in time to know which way you can travel.
            in_time_order = sorted(calls, key=lambda call: call[1])
            if in_time_order != calls:
                reordered.append(sailing["corsa"])
            sailings.append({
                "c": sailing["corsa"],
                "sr": 1 if sailing["sr"] else 0,
                "s": in_time_order,
            })

    unused = set(index_of) - seen_stops
    if unused:
        sys.exit(f"GEOGRAPHY lists stops absent from the timetable: {sorted(unused)}")

    data = {
        "valid": timetable["valid"],
        "version": VERSION,
        "built": datetime.datetime.now().strftime("%d %b %Y, %H:%M"),
        "stops": stops,
        "sailings": sailings,
        "map": build_map(order),
    }

    html = TEMPLATE.read_text(encoding="utf-8")
    if "/*__DATA__*/" not in html:
        sys.exit("Template is missing the /*__DATA__*/ marker")
    html = html.replace("/*__DATA__*/", json.dumps(data, separators=(",", ":"), ensure_ascii=False))
    OUTPUT.write_text(html, encoding="utf-8")

    print(f"Wrote {OUTPUT.name}: v{VERSION}, {len(sailings)} sailings, {len(stops)} stops, "
          f"{OUTPUT.stat().st_size // 1024} KB")
    if reordered:
        print(f"Sorted into call order: corse {', '.join(sorted(reordered, key=int))}")


if __name__ == "__main__":
    main()
