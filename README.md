# Garda Ferries

A small offline timetable app for the Lake Garda ferries, summer 2026. Pick two stops
and a time, and it shows the sailings around it.

Built from the Navigazione Laghi *Orari Orizzontali — Estate 2026* timetable:
93 sailings, 27 stops, valid **16 May – 4 October 2026**.

## Putting it on an iPhone

1. Open the app's URL in **Safari** (not Chrome — only Safari can add to the home screen).
2. Tap the **Share** button, then **Add to Home Screen**.
3. It gets an icon and opens full-screen, with no address bar.

Everything is baked into the one HTML file, so once it has loaded it works with no
signal — which is the point, on the lake.

## What it does

- **Direct sailings first.** Two before your chosen time, four after, with the next one
  highlighted. Each shows departure, arrival, journey time, the *corsa* number and the
  stops it calls at on the way.
- **SR sailings are flagged** — *servizio rapido*, faster but with a supplement to pay.
- **One change, when needed.** For the stop pairs with no direct boat, it works out
  connections with a single change, showing both legs and the wait. For pairs that do
  have a direct sailing, there's a toggle.
- **Every stop on the way, with times.** Tap a sailing to unfold the full chain of
  calls — handy for getting off partway, or judging where the boat has got to.
- **A map tab.** The real lake and all 27 piers. Tap a stop to set your start, tap
  another for the destination. Your sailing is traced across the water.
- **Bikes and step-free access.** Each sailing says whether bikes are welcome, carried
  only if there is room, or not carried, and whether it is step-free or worth asking
  first. Read out of the printed timetable's symbols.
- **Swap button** for the trip back.

Of the 702 possible stop-to-stop combinations, 498 have a direct sailing, 175 more work
with one change, and 29 cannot be done in a day.

## Building

```bash
python build.py
```

That bakes `garda-ferry-2026-summer.json` into `app.template.html` and writes
`index.html`. Python 3, standard library only, and no network — the map geography is
committed in `garda-geography.json`. Refresh that with `python fetch_geo.py` if a stop
changes. See `CLAUDE.md` for how the search works and what to watch out for.

The bicycle and wheelchair marks come from the PDF itself via `python extract_symbols.py`,
which is likewise only needed if the timetable is replaced.

Map data © OpenStreetMap contributors, licensed ODbL.

## Accuracy

Times were transcribed from the text layer embedded in the official PDF, so the values
are exact; the work was reattaching each time to its column. See the accuracy notes in
`garda-ferry-2026-summer.md`.

**Check [navigazionelaghi.it](https://www.navigazionelaghi.it) before travelling.** Ships
get substituted and times change. This is a personal convenience app, not an authority.
