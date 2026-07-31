# CLAUDE.md

Personal Lake Garda ferry timetable app. One HTML file, opened from an iPhone home
screen, works offline. Not a product — there is no build toolchain, no dependencies
and no tests beyond checking results against the source PDF.

## Layout

| File | Role |
|---|---|
| `Orari-Orizzontali-Web-Estate-2026.pdf` | The original Navigazione Laghi timetable. Ground truth. |
| `garda-ferry-2026-summer.json` | Transcription of the PDF. **The data source the app is built from.** |
| `garda-ferry-2026-summer.md` | Same data, human-readable, with accuracy notes. Use it to eyeball corrections. |
| `garda-geography.json` | Lake outline and pier coordinates from OpenStreetMap. **Generated, but committed** — see below. |
| `app.template.html` | The whole app — markup, CSS, search logic. Edited by hand. |
| `build.py` | Bakes the JSON into the template and writes `index.html`. |
| `fetch_geo.py` | Refreshes `garda-geography.json` from OpenStreetMap. The only part needing a network. |
| `make_icon.py` | Draws `icon.png`, the home-screen icon, with zlib only. |
| `index.html`, `icon.png` | **Generated. Never edit these directly** — the next build overwrites them. |
| `CHANGELOG.md` | Running history of changes. Keep it current — see below. |

## Working on it

Edit `app.template.html` or the JSON, then:

```bash
python build.py
```

`make_icon.py` only needs re-running if the icon design changes. Python 3 is the
only requirement; both scripts use the standard library.

**Record anything a user would notice in `CHANGELOG.md` before committing** — a new
feature, changed behaviour, a fixed wrong result, corrected times. Put it under
*Unreleased*, and rename that heading to the date when it gets pushed. Internal
refactoring that changes nothing visible does not need an entry.

To see it in a browser: `python -m http.server 8731` and open `localhost:8731`.
A `.claude/launch.json` is set up for the Browser pane preview.

## How the search works

`DATA.sailings` is a flat list; each sailing is `{c: corsa, sr: 0|1, s: [[stopIndex, minutes], …]}`
with calls **in time order**. Everything depends on that ordering:

- **Direct** — `findDirect(a, b)` looks for a sailing calling at `a` and then, later
  in the same list, at `b`.
- **One change** — `findOneChange(a, b)` joins two sailings at a shared stop, needing
  `MIN_TRANSFER` (10 min) between arrival and the next departure and refusing waits over
  `MAX_WAIT` (3 h). Results are pruned to those not beaten outright by a later departure
  arriving sooner.

Connections with a change are shown only when the pair has no direct sailing at all,
or when the user taps the toggle. That was a deliberate choice: most real trips are
direct and a mixed list gets noisy.

Around the chosen time it shows `BEFORE` (2) sailings earlier and `AFTER` (4) later,
marking the first departure at or after that time as *next*. If nothing is left that
day it falls back to showing the last few.

## The map

`fetch_geo.py` pulls the lake outline from Nominatim and the piers from
OpenStreetMap's `amenity=ferry_terminal` nodes via Overpass, then writes
`garda-geography.json`. **That file is committed on purpose** — `build.py` must not
need a network, so builds stay reproducible and work offline. Re-run `fetch_geo.py`
only if a stop is added or the outline looks wrong.

`PIERS` in that script maps our stop names to OSM pier names explicitly rather than
fuzzy-matching. Several piers are near neighbours — `Limone centro` and
`Limone P multipiano` are 600 m apart — and a wrong guess puts a dot somewhere
plausible but incorrect. The script exits rather than guessing if a name stops
matching.

`build_map()` in `build.py` projects lon/lat to SVG units. Longitude is scaled by
`cos(latitude)` first; skip that and the lake comes out about 40% too wide.
`declutter()` then pushes labels apart where piers nearly coincide.

Everything is checked geometrically rather than by eye: every pier lands within 1.4
SVG units (~130 m) of the drawn shoreline, and the drawing is 1.74 times taller than
wide, matching the real 50 km by 28 km. If a change breaks the projection those
numbers move immediately.

## Things that will bite you

- **The JSON stores nine sailings in the PDF's printed row order, not call order** —
  corse 6, 15, 22, 27, 111, 113, 114, 156, 159. Their times run backwards through the
  stop list. `build.py` sorts every sailing by time to fix this, and prints which ones
  it reordered. If that list changes after a JSON edit, something moved — check it.
- `LIMONE centro` and `LIMONE multipiano` are **different stops** and some sailings use
  one, some the other. You cannot change between them; the app treats them as separate,
  which is correct.
- Every stop key in the JSON must appear in `GEOGRAPHY` in `build.py`, which also sets
  the display names and the dropdown order (geographic, anticlockwise from Peschiera).
  The build fails loudly if the two drift apart.
- Times are local, minutes-from-midnight integers. No sailing crosses midnight, so no
  day-rollover handling exists anywhere.
- The timetable has **no weekday/weekend variation** — confirmed against the PDF legend,
  which only carries SR, bicycle and wheelchair symbols. Do not add day-of-week logic
  without re-checking the source.
- Bicycle and wheelchair symbols from the PDF were **not** captured in the JSON, so the
  app cannot show them. Adding them means re-extracting from the PDF.

## Next season

The timetable is valid 16 May – 4 Oct 2026 and then it is wrong. Transcribe the new PDF
into the same JSON shape, update `GEOGRAPHY` if stops changed, and rebuild.
