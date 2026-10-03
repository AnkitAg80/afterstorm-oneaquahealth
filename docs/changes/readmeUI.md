# Phase 3 — coordinator page

The page is implemented in **`web/index.html`**, with inline CSS and vanilla
JavaScript. It reads the committed `web/data/plan.json` from Phase 2. The
planner, policy configuration, generated plan and raw source responses were
not changed in this phase.

The default is **Oslo LIVE**, showing the cached **42.9 mm forecast on
2026-10-08**, five proposed visits, and the experimental **2026-10-09 to
2026-10-10** window. The page puts the selected forecast's original retrieval
time beside the LIVE badge: **2026-10-03 14:29:10 UTC**. LIVE identifies the
forecast mode; the timestamp identifies the saved snapshot. It is not a
continuous API connection.

## What changed, where, and why

1. **`web/index.html`: one coordinator workspace.** City, evidence-mode and
   visit-budget controls sit above the rain evidence and proposed dates. The
   map and ranked visit cards follow, with notices, the complete city roster,
   source-data exclusions and source/policy details. A restrained layout keeps
   the evidence and next action easy to identify without adding a framework.
2. **The browser slices the Python ranking.** Changing the budget takes the
   first N codes from `ranking`; it does not recalculate historical scores,
   category choices or ordering. Each visit collects all recommended categories.
   Map status, visit cards and the full roster use that same selected set.
3. **Plain explanations replace empty visit lists.** Benevento LIVE says that
   no storm is forecast in the cached period and every site already has a lab
   record. A zero budget instead says the visit budget is zero. Unknown rain
   and missing eligible sites have their own explanations. Invalid budgets
   receive a visible error rather than changing allocation.
4. **Evidence remains inspectable.** Each visit's “Why this site?” disclosure
   shows the Python reason, original category values, sample date, sewage
   distance, the selected rain value, experimental-window caveat, source URLs
   and original retrieval times. The map uses only first-party roster positions.
   T21/T24 visibly say **“Missing sewage distance · last among baseline sites”**
   on their baseline visit cards, as well as in their source details.
5. **Replay and notices stay explicit.** A banner names the actual replay
   anchor and calls it a historical scenario. Draft notices display their
   review requirement, original text, actual historical sample year and the
   coordinator's responsibility for issuing/lifting them. Notice eligibility
   does not change when the visit budget changes.
6. **`web/vendor/`: approved local map assets.** The user explicitly approved
   downloading Leaflet. The JavaScript, CSS and licence are local; no package
   manager or runtime dependency was installed. `.gitattributes` now preserves
   their bytes across Git checkouts, just as it already does for raw data.
7. **`docs/screenshots/`: browser captures.** Oslo LIVE, Coimbra REPLAY with C5
   evidence and notice expanded, the plain map, and the narrow layout are saved
   for review and later submission documentation.

## Run locally

From the `afterstorm/` repository:

```text
python -m http.server 8765 --bind 127.0.0.1 --directory web
```

Then open [AfterStorm locally](http://127.0.0.1:8765/index.html).
The current preview uses this command; it does not publish a website.
The workspace requires shell commands to use the `rtk` prefix:

```text
rtk proxy python -m http.server 8765 --bind 127.0.0.1 --directory web
```

Direct links preserve city, mode and budget:

- [Oslo LIVE](http://127.0.0.1:8765/index.html?city=OS&mode=live&visits=5)
- [Coimbra REPLAY](http://127.0.0.1:8765/index.html?city=CO&mode=replay&visits=5)
- [Benevento LIVE](http://127.0.0.1:8765/index.html?city=BE&mode=live&visits=5)

An ordinary HTTP server is needed to load the JSON; opening the HTML directly
with `file://` is not the supported run path. No build command is needed.

## The four requested presentation details

- **Zero visits:** an explanatory sentence, never an empty visit list. The
  full roster remains available regardless of the selected budget.
- **LIVE timestamp:** `sources["forecasts/{city_id}.json"].fetched_at`, not
  `generated_at` or `read_at`. The original UTC zone is shown explicitly.
- **Archive coverage:** exactly **“days without data at every site (includes
  days before some site histories begin)”**. Unknown days are not relabelled dry.
- **Demo order:** start with Oslo LIVE's real forecast; switch to Coimbra
  REPLAY to open C5's Why card and review its draft contact notice. Benevento
  REPLAY is also suitable for notices. Oslo has none at the default thresholds.

Sampling windows remain local calendar dates with date precision; no rain-stop
time is invented. Retrieval timestamps are separate metadata and retain their
original zone. The experimental-window label appears in the rain summary,
each relevant visit card and the explanation.

## Map, offline behavior and accessibility

**Map tiles need internet.** The page loads street-map tiles from OpenStreetMap
with its attribution displayed. The map's “Street map” checkbox can turn those
tiles off. Pins remain on a plain grid using the saved official coordinates.
The same map remains usable when tile requests fail, with an explanatory
message. Leaflet itself and all plan data are local.

The page never calls the OneAquaHealth API, Open-Meteo API or FHIR sandbox.
Their URLs are evidence links a user can choose to open. The main page and
data still need the local server; this is not an installable offline app.

Controls have labels, native keyboard behavior, visible focus, budget-error
feedback and a skip link. Status is expressed with text as well as colour.
“Show on map” buttons provide a keyboard-accessible way to locate sites without
requiring pointer interaction with a marker. Reduced-motion preferences are
respected. Narrow screens stack the map and visit list and keep controls from
overlapping. Missing coordinates omit a map pin/button without removing a visit.

The archive-coverage disclosure shows the number of fully covered city days
and threshold-reaching days. Historical frequency is calculated as:

```text
threshold-reaching days / fully covered city days * 365.25
```

It is labelled **per observed year**, based on the conservative all-site replay
policy, and describes the archive only. It is not a future storm-frequency or
contamination forecast. Partial histories and missing calendar dates are
excluded from its denominator.

## Verification

The first browser check failed because the page did not exist. Initial
rendering then exposed a JavaScript template syntax error, which was fixed and
checked with Node's syntax checker. Browser checks subsequently verified:

| City | Roster/pins | LIVE visits | REPLAY visits | REPLAY draft notices | Replay anchor |
|---|---:|---:|---:|---:|---|
| Benevento | 20 | 0 | 5 | 6 | 2026-04-01 |
| Coimbra | 20 | 2 | 5 | 6 | 2026-05-10 |
| Ghent | 22 | 5 | 5 | 0 | 2025-07-06 |
| Oslo | 20 | 5 | 5 | 0 | 2026-06-09 |
| Toulouse | 24 | 3 | 5 | 7 | 2026-08-03 |

All ten combinations were checked with street-map tiles switched off. Each
retained its complete roster and the corresponding number of saved-coordinate
pins. Additional checks covered:

- Oslo's forecast value, exact window, original forecast retrieval time and
  Python visit order `O12, O11, O14, O13, O4`;
- budgets 2 and 0, invalid negative input, and the distinct zero-budget message;
- Benevento LIVE's zero-visit explanation and Coimbra LIVE's two baselines;
- Coimbra's replay banner, C5's 24.43 mm archive value, and its expanded draft
  notice mentioning people and pets and coordinator review;
- locating C5 on the plain map while all 20 pins remained present;
- Toulouse's baseline order `T15, T21, T24` and visibly stated missing distances;
- the exact archive-coverage wording;
- a 390-pixel browser override: no horizontal page overflow, no overlapping
  controls, and a normal-size excluded-status legend marker. The override was
  reset before finishing.

The missing-distance visibility assertion failed before its card note was
added and passed afterward. A CSS class clash that enlarged the excluded
legend marker was also corrected. The existing **18 planner checks** pass;
the inline JavaScript syntax check passes. A fresh read-only review found no
Critical or Important defects and no Minor issue requiring a change.

Tile-off behavior was exercised directly. Forced external network failure
was not separately injected; the tile-error fallback was checked in code.

## Local vendor provenance

[Leaflet's official download page](https://leafletjs.com/download.html) lists
1.9.4 as the stable release and publishes the following SHA-256 values. The
downloaded JavaScript and CSS matched them:

| Local file | Source | SHA-256, Base64 |
|---|---|---|
| `web/vendor/leaflet.js` | `https://unpkg.com/leaflet@1.9.4/dist/leaflet.js` | `20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo=` |
| `web/vendor/leaflet.css` | `https://unpkg.com/leaflet@1.9.4/dist/leaflet.css` | `p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY=` |
| `web/vendor/LICENSE.txt` | `https://raw.githubusercontent.com/Leaflet/Leaflet/v1.9.4/LICENSE` | `U+jcJYYgFOQyR0HKGPvjYR4R1C72n1n4bqjFOJZH1Ms=` |

Default-marker and layer-control images are not used: pins are circle markers
and the basemap checkbox is this page's own control. No unused image assets
were downloaded.

## Screenshots

Oslo LIVE, with the cached forecast, experimental window and proposed visits:

![Oslo LIVE coordinator page](docs/screenshots/oslo-live.jpg)

Coimbra REPLAY, with C5's source evidence and coordinator-review draft notice:

![Coimbra replay with C5 evidence and draft notice](docs/screenshots/coimbra-replay.jpg)

[Plain-map screenshot](docs/screenshots/oslo-live-plain-map.jpg) ·
[Narrow-layout screenshot](docs/screenshots/oslo-live-mobile.jpg)

## Checkpoint

Phase 3 has been reviewed and approved for a local commit. Phase 4 adds FHIR
resource content and export; no FHIR download button is shown before that work
exists. No remote, push, deployment, sandbox write or Devpost submission was
performed. **Stop here and wait for explicit “proceed” before Phase 4.**
