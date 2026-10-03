# Phase 1 — setup and data layer

[Certain] Phase 1 is complete. This repository contains a verified public-data cache and join report. Planning, notices, the interface, FHIR export, and publishing remain for later phases and approvals.

## What changed, where, and why

1. **Created `afterstorm/` and initialized local Git on `phase-1-data`.** This is the folder named in the updated brief. No remote, commits, push, deployment, or public sandbox writes were created.
2. **Added `fetch.py`.** It uses Python's standard library and explicit HTTP GET requests. It fetches the first-party roster, historical health-risk records, urban parameters, a weather history for each roster site, and one seven-day forecast per city. Historical queries start on the recorded sampling date, or 1 January 2023 when no sample date is available. Dates sent to the archive have the required `T00:00:00Z` suffix.
3. **Cached unchanged response bytes in `data/raw/`.** Site coordinates come only from `/api/sites/all`. No participant-posted FHIR Locations are used. The source arrays remain separate so missing measurements are not manufactured by merging records.
4. **Added provenance in `data/raw/_manifest.json`.** Each source records its URL, original retrieval time, byte length, and SHA-256. This makes the cached data traceable and detects cache changes. Writes replace files atomically after JSON and source-shape checks succeed.
5. **Added the join report in `data/raw/_join-report.json`.** It counts availability, lists all ten sites without lab records, exposes missing sewage distances, duplicates, invalid health fields, unmatched codes, daily archive gaps, and seven-day forecast coverage.
6. **Added `test_fetch.py`.** Fourteen standard-library tests cover the behavior most likely to corrupt or misrepresent the data layer. Its fixtures are explicitly synthetic and live only in tests; the real cache comes from the public endpoints.
7. **Added `.gitignore` and `.gitattributes`.** Python artifacts and test scratch space are ignored. Real cached data remains eligible for inclusion in the future public repository. Git line-ending conversion is disabled for the raw cache so its byte hashes survive checkout on other operating systems.

## Measured join report

[Certain] The real fetch made 114 successful source retrievals: three core feeds, 106 per-site histories, and five city forecasts. No cached fallback was needed for that run. The original retrieval interval was **3 October 2026, 14:28:52–14:29:10 UTC**. A subsequent offline run reproduced the same joins while retaining those retrieval times.

| Availability | Sites |
|---|---:|
| First-party roster | 106 |
| Valid site coordinates | 106 |
| Historical lab health-risk record | 96 |
| At least one usable historical daily rainfall record | 106 |
| Valid sewage-distance field | 104 |
| All five joined inputs: lab, coordinates, history, sewage distance, complete city forecast | 96 |

[Certain] The cache contains **127,481 historical daily weather rows** and **30,768,409 bytes of original responses**. All 114 file hashes and lengths matched the provenance manifest. The health-risk feed contains 95 records from 2023 and one from 2024.

| City | Roster | Lab records | Coordinates | Histories present | Sewage distance |
|---|---:|---:|---:|---:|---:|
| Benevento | 20 | 20 | 20 | 20 | 20 |
| Coimbra | 20 | 18 | 20 | 20 | 20 |
| Ghent | 22 | 17 | 22 | 22 | 22 |
| Oslo | 20 | 20 | 20 | 20 | 20 |
| Toulouse | 24 | 21 | 24 | 24 | 22 |

[Certain] **No lab health-risk record:** `C17`, `C18`, `G1`, `G17`, `G18`, `G19`, `G20`, `T15`, `T21`, `T24`.

[Certain] **No sewage-distance record:** `T21`, `T24`. Their absence is preserved as unknown, not converted to zero or a guessed value. All 106 sites remain in the roster.

[Certain] No duplicate roster, health, or urban codes were found. No unmatched health or urban codes, invalid health-risk components, missing sample dates in existing health records, missing site coordinates, or missing history datasets were found in this snapshot.

## Archive gaps and freshness

[Certain] Every site's returned archive ends on **26 September 2026**. All 106 histories also lack daily rows for **4 August 2026** and **27 August 2026** within their returned ranges. These are 212 absent site/date pairs. No rain values were interpolated or replaced with zero.

[Certain] The report distinguishes three cases:

- `missing.weather`: a site has no usable historical rainfall at all.
- `missing_rain_days`: existing rows contain unknown or unusable precipitation.
- `missing_calendar_dates`: a daily row is absent inside the returned interval.

[Certain] In the real snapshot, the first two lists/counts are empty or zero, while the third contains the two dates for all 106 sites. Having weather history does **not** mean having an uninterrupted daily series. The later replay implementation must choose from observed dates and respect these gaps.

[Certain] All five forecasts contain seven consecutive local calendar dates, **3–9 October 2026**, with usable precipitation values and units of millimetres. Forecasts are model output; retrieval time is not a claimed model-issuance time, and neither forecast rainfall nor historical relative scores establish current contamination.

## Files and data sources

| Cache path under `data/raw/` | Source | Use |
|---|---|---|
| `sites.json` | [First-party site roster](https://api.enora-oah.eu/api/sites/all) | Site codes, names, site positions, cities, and city-centre positions |
| `health-risks.json` | [Health-risk feed](https://api.enora-oah.eu/api/resilience-map/health-risks) | Historical scaled categories and sample dates |
| `urban-parameters.json` | [Urban parameters](https://api.enora-oah.eu/api/resilience-map/urban-parameters) | Sewage distance; other returned fields are preserved |
| `weather/<site-code>.json` | `https://api.enora-oah.eu/api/resilience-map/weather` | Original daily history, queried separately for every site |
| `forecasts/<city-id>.json` | [Open-Meteo forecast API](https://open-meteo.com/en/docs) | One seven-day daily forecast per first-party city centre |
| `_manifest.json` | Generated locally | Source URLs, retrieval timestamps, checksums, retrieval status |
| `_join-report.json` | Generated locally | Availability and integrity findings; not an environmental assessment |

[Certain] Forecast city ids are `BE`, `CO`, `GH`, `OS`, and `TO`. Exact query URLs, including coordinates and archive date intervals, are stored in `_manifest.json`.

## Run and verify

Run from the `afterstorm/` directory with Python 3.11 or newer; this phase was verified with Python 3.14.0. No package installation is required.

```text
python fetch.py
python fetch.py --offline
python -m unittest discover -v
```

[Certain] `python fetch.py` refreshes sources using `User-Agent: Mozilla/5.0`, at most eight history-fetch workers, a default 20-second per-attempt timeout, and up to three attempts with bounded backoff. Permanent HTTP errors such as 401/403 are reported rather than repeatedly treated as transient. Optional settings are `--workers 1` through `--workers 8`, `--timeout <seconds>`, and `--data-dir <directory>`.

[Certain] When a refresh fails, a valid existing cache may be used with status `cache_fallback` and an explicit warning. Its original retrieval timestamp is retained. A missing, malformed, or checksum-mismatched cache cannot be presented as a successful source. `--offline` performs no API requests and reports retrieval status `offline`. It checks cached shapes and recorded checksums, then regenerates the join report. For caches without provenance, retrieval time remains unknown; no timestamp is invented.

[Certain] Exit code 0 means all required datasets were obtained or loaded from usable caches. Exit code 1 means one or more history/forecast sources were unavailable and the report is partial. Exit code 2 means a required core feed or manifest could not be used. A dataset can still contain explicitly reported gaps even when the fetch exits successfully.

## Verification performed

[Certain] The final suite passed **14/14 tests**, including real local HTTP tests for retry and cache fallback, unchanged response bytes, User-Agent, offline behavior, checksum mismatches, correct baseline query dates, missing data versus zero, duplicates/unmatched codes, and the offline command-line path.

[Certain] A fresh review identified three important issues. Each received a regression that failed before the fix and passed afterward:

1. **Absent archive dates were not exposed.** The join report now lists missing calendar dates and affected sites while preserving raw files.
2. **Identifierless core records could overwrite good caches and invent baseline sites.** Endpoint-specific validation now rejects those responses before replacement; direct joins reject identifierless records rather than silently discard them.
3. **Incomplete or malformed forecasts could count as available.** Forecast validation now checks nested types, units, seven consecutive dates, and precipitation structure. Null rainfall remains unknown and does not count as complete city coverage. Malformed responses use the documented cache fallback rather than bypass it with an uncaught schema error.

[Certain] The real offline run passed after these fixes. No additional public retrieval was needed to verify the unchanged source bytes. No minor review findings were deferred.

## Decisions and scope

[Certain] Three implementation rulings were recorded:

- Use the requested new `afterstorm/` repository rather than a separate worktree. The parent folder was not a repository. Cost if changed later: relocate an unpublished local repository.
- The revised product rules take precedence over stale mentions of clock times, participant Location exclusions, or static UI download links in later phase text. Cost if interpreted differently: adjust that later-phase text before implementation.
- Use phase documentation and an ignored progress ledger rather than a skill's whole-plan automation or unrequested commits. The user's explicit phase-by-phase approval remains binding. Cost if changed later: bookkeeping only.

[Certain] Python's private temporary-directory permissions initially conflicted with the Windows sandbox. Test fixtures now use checked, isolated directories under ignored project scratch space with inherited permissions. This is a test-environment adaptation; the public data cache is unchanged.

[Certain] This phase did not create a planner, UI, advisory, FHIR resource, remote repository, deployment, submission, or approved field visit. It did not download Leaflet or a validator. Cache availability and software correctness do not establish scientific validity or real-world health impact.

## Next checkpoint

[Certain] Phase 2 is **not started**. After the user types `proceed`, it will implement configurable thresholds, experimental date-only windows, visit-budget allocation, baseline handling, labelled replay, draft notices, and the required planning tests. The source gaps and unknown sewage distances remain visible inputs for that phase.
