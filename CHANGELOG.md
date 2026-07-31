# Changelog

Notable changes to the app, newest first. Dates are YYYY-MM-DD.

Add new entries under **Unreleased** as you go, then rename that heading to the
version and date when you push, and bump `VERSION` in `build.py` to match — that is
what the app shows in its footer. Group entries under *Added*, *Changed*, *Fixed* or
*Removed*, and write them for a reader who wasn't there: what changed and why, not
which lines moved.

## Unreleased

Nothing yet.

## 1.6 — 2026-07-31

### Added

- **The corsa number, large, on the map.** It sits in the empty space at the top left
  — the lake's northern arm is well over to the right, so nothing was using it — with
  the departure and arrival underneath. It names the sailing the red line traces and
  the green boat belongs to, so the boat you are looking for can be read at a glance
  without going back to the timetable.

## 1.5 — 2026-07-31

### Added

- **Bicycle and wheelchair information, at last.** Every sailing now says whether
  bikes are welcome, carried only if there is room, or not carried, and whether it is
  step-free or you should ask before travelling. This was the long-standing gap: the
  marks are vector drawings in the PDF, not text, so the original transcription could
  not see them. `extract_symbols.py` now reads them straight from the artwork — the
  state is carried by the fill colours, a red ring meaning no bikes, a yellow disc
  meaning limited — and matches each to its column. All 93 sailings are covered.
- **Times along the route on the map.** Each stop the highlighted sailing calls at
  now shows the time it gets there, in red beside the stop name, so the map answers
  "when does it reach Malcesine" without going back to the timetable.

## 1.4 — 2026-07-31

### Fixed

- **The route line drew the wrong sailing.** It was chosen by the time in the search
  box rather than by the sailing actually highlighted, so tapping a later boat left
  the line tracing a different one — for Desenzano to Riva it drew corsa 160 while
  corsa 6 was the green boat, missing eight stops corsa 6 really calls at. The line
  now always belongs to the highlighted sailing, and touches every one of its calls.

### Changed

- The route line is **red**, with **arrowheads** partway along each leg showing which
  way the boat travels. Legs too short to hold an arrow are left clear. The legend
  now covers the line as well as the boats.

## 1.3 — 2026-07-31

### Changed

- **Tapping the times on a sailing opens the map at that departure.** Tap the 16:07
  on a card and the slider sits at 16:07 with that boat marked as yours, rather than
  wherever the clock happened to be. Each card carries a small *map ›* to show it can
  be tapped. Opening the Map tab directly still starts from the time you searched for.

## 1.2 — 2026-07-31

### Added

- **Your ferry stands out on the map.** The boat carrying the sailing the timetable
  picked for your trip is drawn larger and in green, against the orange of everything
  else under way, with a legend saying which is which. The line under the slider also
  says whether yours is afloat yet.
- **Follow a boat.** Tap any boat and a *Follow from 09:20* button appears. It rewinds
  the slider to where that boat set off, starts playing, and marks it as the one to
  watch, so you can run its whole route through from the beginning.

## 1.1 — 2026-07-31

### Added

- **A time slider on the map**, showing every boat under way at that moment. Drag it
  through the day, or press play to watch the lake fill up and empty out — it peaks at
  17 boats around 11:00. Tap a boat to see its *corsa*, which leg it is on and when it
  is due. Positions between piers are interpolated in a straight line at a steady
  speed, so they are an estimate of where a boat has got to, not a tracker, and the
  app says so.
- **A version number and build date** in the footer, so it is obvious whether the
  phone has picked up a new copy.

- The trip back is now shown underneath the outbound one, so a day out can be
  planned without swapping the stops over and losing your place. It lists the boats
  leaving after you actually arrive — a sailing that left before you got there is no
  use — and the **last boat** of the day is tagged, in both directions.
- When nothing is left, it says when the last one went rather than showing an empty
  list.
- **Show all** button on each section, to scroll the whole day rather than just the
  handful around your time. On the trip back that means every boat leaving after you
  arrive; on the way out, every sailing there is.

- **Times at every stop on the way.** Tap the summary line on a sailing to unfold the
  whole chain of calls with times, so you can get off partway or work out where the
  boat has got to. Works on each leg of a connection too.
- **A map tab.** The real lake outline and all 27 piers, drawn from OpenStreetMap
  data. Tap a stop to set where you are starting, tap another for the destination,
  and it drops you back on the timetable. The sailing you are most likely to catch is
  traced across the water, so the zig-zag between shores is visible.

### Changed

- Results are split into **Out** and **Back** sections with headings, so each card no
  longer repeats the route. The *routes with a change* toggle is now per section.
- The *via* line on each sailing became the tappable stop list described above.

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
