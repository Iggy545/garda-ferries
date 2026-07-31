#!/usr/bin/env python3
"""Read the bicycle and wheelchair marks out of the timetable PDF.

The marks are vector drawings, not characters, so they cannot be lifted out with the
text. Each is built the same way — a disc, a ring, then the bicycle or chair drawn on
top — and the *state* is carried entirely by the fill colours:

    bicycle     white disc, black ring    bikes welcome
                white disc, red ring      bikes not carried
                yellow disc               bikes subject to space
    wheelchair  navy disc                 step-free, recommended
                white disc, grey ring     ask before travelling

Matching a mark to its sailing is done by column position, not by the text beside it:
the corsa numbers are drawn with kerned advances the text matrix never records, so
their x coordinates are useless. The marks themselves are evenly spaced, so they are
clustered into columns and zipped against the corsa numbers in the order the PDF
draws them, which is the printed left-to-right order.

Writes garda-symbols.json, which is committed; `build.py` reads it. Re-run only if
the PDF is replaced.

    python extract_symbols.py
"""

import collections
import json
import pathlib
import re
import zlib

HERE = pathlib.Path(__file__).parent
PDF = HERE / "Orari-Orizzontali-Web-Estate-2026.pdf"
OUTPUT = HERE / "garda-symbols.json"

TOKEN = re.compile(rb"""
    \((?P<str>(?:\\.|[^\\()])*)\) | <(?P<hex>[0-9A-Fa-f\s]*)>
  | (?P<num>-?\d*\.?\d+) | /(?P<name>[^\s/\[\]<>(){}]+)
  | (?P<op>[A-Za-z'"*]+) | (?P<delim>[\[\]])
""", re.X)

# Subpaths are identified by their point count, which is stable because every copy on
# the page is the same artwork at a different scale.
BIKE, CHAIR, DISC, RING = 105, 42, 16, 33

RED = (1.0, 0, 0)
YELLOW = (1.0, 0.9, 0.05)
WHITE = (1.0, 1.0, 1.0)
NAVY = (0, 0, 0.5)
GREY = (0.2, 0.2, 0.2)

TIMETABLE_Y = 300      # above this is the timetable; the legend sits far below
COLUMN_GAP = 6         # marks more than this far apart belong to different columns


def like(a, b, tol=0.08):
    return a is not None and all(abs(x - y) <= tol for x, y in zip(a, b))


def streams():
    raw = PDF.read_bytes()
    out = []
    for m in re.finditer(rb"stream\r?\n(.*?)endstream", raw, re.S):
        try:
            out.append(zlib.decompress(m.group(1)))
        except Exception:
            pass
    return out


def mul(a, b):
    return [a[0]*b[0]+a[1]*b[2], a[0]*b[1]+a[1]*b[3], a[2]*b[0]+a[3]*b[2],
            a[2]*b[1]+a[3]*b[3], a[4]*b[0]+a[5]*b[2]+b[4], a[4]*b[1]+a[5]*b[3]+b[5]]


def tail(stack, count):
    """The last `count` operands, if they really are all numbers."""
    if len(stack) < count:
        return None
    values = stack[-count:]
    return values if all(isinstance(v, float) for v in values) else None


def walk(stream):
    """Yield ('text', x, y, bytes) and ('fill', x0, y0, x1, y1, points, colour)."""
    ctm = [1, 0, 0, 1, 0, 0]
    tm = tlm = colour = None
    saved, saved_colour, stack, current = [], [], [], []

    for m in TOKEN.finditer(stream):
        kind = m.lastgroup
        if kind == "num":
            stack.append(float(m.group("num")))
        elif kind == "str":
            stack.append(("s", m.group("str")))
        elif kind == "hex":
            digits = re.sub(rb"\s", b"", m.group("hex")).decode()
            stack.append(("s", bytes.fromhex(digits + "0" if len(digits) % 2 else digits)))
        elif kind == "name":
            stack.append(("n", m.group("name").decode("latin-1")))
        elif kind == "delim":
            stack.append(None)
        elif kind == "op":
            op = m.group("op").decode()
            if op == "q":
                saved.append(list(ctm)); saved_colour.append(colour)
            elif op == "Q":
                if saved: ctm = saved.pop()
                if saved_colour: colour = saved_colour.pop()
            elif op == "cm" and tail(stack, 6):
                ctm = mul(tail(stack, 6), ctm)
            elif op == "g" and tail(stack, 1):
                v = tail(stack, 1)[0]; colour = (v, v, v)
            elif op == "rg" and tail(stack, 3):
                colour = tuple(round(v, 3) for v in tail(stack, 3))
            elif op in ("k", "sc", "scn"):
                nums = [v for v in stack if isinstance(v, float)]
                if len(nums) == 3:
                    colour = tuple(round(v, 3) for v in nums)
                elif len(nums) == 1:
                    colour = (round(nums[0], 3),) * 3
                elif len(nums) == 4:
                    c, mm, yy, kk = nums
                    colour = tuple(round(1 - min(1, ch + kk), 3) for ch in (c, mm, yy))
            elif op == "Tm" and tail(stack, 6):
                tm = tlm = list(tail(stack, 6))
            elif op in ("Td", "TD") and tail(stack, 2) and tlm:
                shift = tail(stack, 2)
                tlm = tlm[:4] + [tlm[4] + shift[0], tlm[5] + shift[1]]
                tm = list(tlm)
            elif op == "T*" and tlm:
                tm = list(tlm)
            elif op in ("Tj", "TJ", "'", '"') and tm:
                text = b"".join(v[1] for v in stack if isinstance(v, tuple) and v[0] == "s")
                if text.strip():
                    yield ("text", round(tm[4], 1), round(tm[5], 1), text)
            elif op == "re" and tail(stack, 4):
                x, y, w, h = tail(stack, 4)
                for cx, cy in ((x, y), (x+w, y), (x+w, y+h), (x, y+h)):
                    current.append((ctm[0]*cx + ctm[2]*cy + ctm[4], ctm[1]*cx + ctm[3]*cy + ctm[5]))
            elif op in ("m", "l") and tail(stack, 2):
                cx, cy = tail(stack, 2)
                current.append((ctm[0]*cx + ctm[2]*cy + ctm[4], ctm[1]*cx + ctm[3]*cy + ctm[5]))
            elif op == "c" and tail(stack, 6):
                curve = tail(stack, 6)
                for k in (0, 2, 4):
                    cx, cy = curve[k], curve[k+1]
                    current.append((ctm[0]*cx + ctm[2]*cy + ctm[4], ctm[1]*cx + ctm[3]*cy + ctm[5]))
            elif op in ("f", "F", "f*", "B", "B*", "b", "b*"):
                if current:
                    xs = [p[0] for p in current]; ys = [p[1] for p in current]
                    yield ("fill", min(xs), min(ys), max(xs), max(ys), len(current), colour)
                current = []
            elif op in ("S", "s", "n"):
                current = []
            stack = []


def marks_from(fills):
    """Every bicycle or wheelchair mark among these fills, with its colours.

    Anchored on the bicycle and chair artwork itself rather than on clusters of
    overlapping shapes: a bicycle sits directly above a wheelchair in the same column
    and the two touch, so clustering merges them.

    This must be given a whole page's fills at once. A page's content is split over
    several streams and the disc a bicycle sits on is often drawn in a different one
    from the bicycle, so searching stream by stream loses the colour that carries the
    meaning.
    """
    plates = [f for f in fills if f[5] in (DISC, RING)]
    found = []
    for fill in fills:
        if fill[5] not in (BIKE, CHAIR) or (fill[2] + fill[4]) / 2 < TIMETABLE_Y:
            continue
        x = (fill[1] + fill[3]) / 2
        y = (fill[2] + fill[4]) / 2
        beneath = {}
        for plate in plates:
            if abs((plate[1] + plate[3]) / 2 - x) < 5 and abs((plate[2] + plate[4]) / 2 - y) < 5:
                beneath[plate[5]] = plate[6]
        found.append({"kind": "bike" if fill[5] == BIKE else "chair",
                      "x": x, "disc": beneath.get(DISC), "ring": beneath.get(RING)})
    return found


def state_of(mark):
    disc, ring = mark["disc"], mark["ring"]
    if mark["kind"] == "bike":
        if like(ring, RED):
            return "no"
        if like(disc, YELLOW):
            return "limited"
        if like(disc, WHITE):
            return "yes"
    else:
        if like(disc, NAVY) or like(ring, NAVY):
            return "yes"
        if like(ring, GREY) or like(disc, GREY):
            return "ask"
    return None


def columns(marks):
    """Group marks into timetable columns by their x position."""
    grouped = []
    for mark in sorted(marks, key=lambda m: m["x"]):
        if grouped and mark["x"] - grouped[-1][-1]["x"] < COLUMN_GAP:
            grouped[-1].append(mark)
        else:
            grouped.append([mark])
    return grouped


def main():
    pieces = streams()

    # A page starts wherever the N.Corsa heading is drawn; the marks may live in later
    # streams belonging to the same page, so each mark joins the most recent heading.
    headings = []
    for index, stream in enumerate(pieces):
        texts = [t for t in walk(stream) if t[0] == "text"]
        if not any(b"N.Corsa" in t[3] for t in texts):
            continue
        header_y = max(t[2] for t in texts if b"N.Corsa" in t[3])
        order = [t[3].strip().decode("latin-1") for t in texts
                 if abs(t[2] - header_y) < 2 and t[3].strip().isdigit()]
        headings.append({"at": index, "corse": order, "fills": []})

    # A page's content is spread over a contiguous run of streams, and the heading is
    # not necessarily in the first of them — here the discs the bicycles sit on are
    # drawn several streams *before* it. Each stream therefore joins the nearest
    # heading, and a page's streams are then walked as one: the graphics state carries
    # across them, so a fill's colour is often set in an earlier stream than the fill.
    for index, stream in enumerate(pieces):
        if not any(op in stream for op in (b"re", b"Tj", b"TJ")):
            continue    # font programs and images, not page content
        owner = min(headings, key=lambda h: abs(h["at"] - index))
        owner.setdefault("streams", []).append(stream)

    for heading in headings:
        joined = b"\n".join(heading.get("streams", []))
        heading["marks"] = marks_from([f for f in walk(joined) if f[0] == "fill"])

    result = {}
    problems = []
    for heading in headings:
        grouped = columns(heading["marks"])
        print(f"page starting in stream {heading['at']}: {len(heading['corse'])} corse, "
              f"{len(heading['marks'])} marks in {len(grouped)} columns")
        if len(grouped) != len(heading["corse"]):
            problems.append(f"stream {heading['at']}: {len(grouped)} columns "
                            f"but {len(heading['corse'])} corse")
            continue
        for corsa, column in zip(heading["corse"], grouped):
            for mark in column:
                state = state_of(mark)
                if state:
                    result.setdefault(corsa, {})[mark["kind"]] = state

    if problems:
        raise SystemExit("Columns did not line up with the corsa numbers:\n  "
                         + "\n  ".join(problems))

    counts = collections.Counter((k, v) for marks in result.values() for k, v in marks.items())
    print(f"\n{len(result)} corse carry a mark")
    for (kind, state), n in sorted(counts.items()):
        print(f"   {kind:6s} {state:8s} {n}")

    OUTPUT.write_text(json.dumps({
        "source": "Orari-Orizzontali-Web-Estate-2026.pdf, per-column bicycle and wheelchair marks",
        "bike": {"yes": "bikes welcome", "limited": "bikes if there is room",
                 "no": "bikes not carried"},
        "chair": {"yes": "step-free, recommended", "ask": "ask before travelling"},
        "corse": dict(sorted(result.items(), key=lambda kv: int(kv[0]))),
    }, indent=1), encoding="utf-8")
    print(f"Wrote {OUTPUT.name}")


if __name__ == "__main__":
    main()
