#!/usr/bin/env python3
"""Generate index.html from the timetable JSON.

The app ships as a single self-contained HTML file so it works offline on a
phone. This script bakes the timetable into app.template.html at the
/*__DATA__*/ marker. Re-run it after editing the JSON, or next season after
transcribing a new PDF.

    python build.py
"""

import json
import pathlib
import sys

HERE = pathlib.Path(__file__).parent
SOURCE = HERE / "garda-ferry-2026-summer.json"
TEMPLATE = HERE / "app.template.html"
OUTPUT = HERE / "index.html"

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
        "stops": stops,
        "sailings": sailings,
    }

    html = TEMPLATE.read_text(encoding="utf-8")
    if "/*__DATA__*/" not in html:
        sys.exit("Template is missing the /*__DATA__*/ marker")
    html = html.replace("/*__DATA__*/", json.dumps(data, separators=(",", ":"), ensure_ascii=False))
    OUTPUT.write_text(html, encoding="utf-8")

    print(f"Wrote {OUTPUT.name}: {len(sailings)} sailings, {len(stops)} stops, "
          f"{OUTPUT.stat().st_size // 1024} KB")
    if reordered:
        print(f"Sorted into call order: corse {', '.join(sorted(reordered, key=int))}")


if __name__ == "__main__":
    main()
