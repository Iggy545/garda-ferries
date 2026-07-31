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
| `app.template.html` | The whole app — markup, CSS, search logic. Edited by hand. |
| `build.py` | Bakes the JSON into the template and writes `index.html`. |
| `make_icon.py` | Draws `icon.png`, the home-screen icon, with zlib only. |
| `index.html`, `icon.png` | **Generated. Never edit these directly** — the next build overwrites them. |

## Working on it

Edit `app.template.html` or the JSON, then:

```bash
python build.py
```

`make_icon.py` only needs re-running if the icon design changes. Python 3 is the
only requirement; both scripts use the standard library.

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
