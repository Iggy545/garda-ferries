# Changelog

Notable changes to the app, newest first. Dates are YYYY-MM-DD.

Add new entries under **Unreleased** as you go, then rename that heading to the date
when you push. Group them under *Added*, *Changed*, *Fixed* or *Removed*, and write
them for a reader who wasn't there — what changed and why, not which lines moved.

## Unreleased

### Added

- The trip back is now shown underneath the outbound one, so a day out can be
  planned without swapping the stops over and losing your place. It lists the boats
  leaving after you actually arrive — a sailing that left before you got there is no
  use — and the **last boat** of the day is tagged, in both directions.
- When nothing is left, it says when the last one went rather than showing an empty
  list.

### Changed

- Results are split into **Out** and **Back** sections with headings, so each card no
  longer repeats the route. The *routes with a change* toggle is now per section.

## 2026-07-31 — first version

### Added

- Journey search between any two of the 27 ferry stops, from the Navigazione Laghi
  summer 2026 timetable (93 sailings, valid 16 May – 4 Oct 2026).
- Direct sailings around a chosen time — two before, four after — each showing
  departure, arrival, journey time, *corsa* number and the stops called at on the way.
  The first departure at or after the chosen time is marked *next*.
- Connections with one change for stop pairs that have no direct boat, showing both
  legs and the wait. Available on a toggle for pairs that do have a direct sailing.
  Of 702 possible pairs, 498 are direct, 175 need one change and 29 cannot be done
  in a day.
- *Servizio rapido* sailings flagged, since they carry a supplement.
- Swap button for the return trip, and a *Now* button.
- Last-used stops remembered between visits; the time resets to now when the app is
  reopened, so a stale sailing is never left marked as *next*.
- Home-screen install on iOS: full-screen, no address bar, and fully offline once
  loaded. Icon drawn by `make_icon.py` using only the standard library.
- `build.py`, which bakes the timetable JSON into `app.template.html` to produce the
  single self-contained `index.html`.

### Fixed

- Nine sailings — corse 6, 15, 22, 27, 111, 113, 114, 156, 159 — are stored in the
  source JSON in the order the PDF printed the rows rather than the order the boat
  calls, so their times ran backwards through the stop list. The search assumes calls
  run forwards in time, so these produced wrong and missing routes. `build.py` now
  sorts every sailing by time and reports which ones it reordered.

### Known gaps

- The bicycle and wheelchair symbols printed against each column in the PDF were not
  captured in the JSON, so the app cannot show them.
- The timetable is summer 2026 only. After 4 October 2026 it is out of date.
