# Phase 2 — transparent sampling proposals

Phase 1 was committed **before** Phase 2 as `a7d32a2` on `phase-1-data`.
Phase 2 adds one planner and one assert-based test file. It reads the committed
cache without contacting an API or rewriting any raw response.

The deadline is **October 5, 2026, 04:00 UTC / 09:30 IST**. This checkpoint
covers the planning logic; the coordinator page and FHIR export are later phases.

## What changed, where, and why

1. **`config.json`: five policy settings.** Rain threshold 20 mm/day, category
   selection and notice thresholds 0.5, five site visits per city, and a two-day
   experimental window. Keeping these in one file makes the prototype's choices
   inspectable. None is presented as a validated clinical or water-safety cutoff.
2. **`plan.py`: cached data into visit proposals.** It retains every official
   roster site, selects live/replay weather, ranks assessment and baseline
   visits, allocates the budget, writes reasons and source references, and drafts
   notices requiring a coordinator's review. The pure `build_plan` function does
   not alter its inputs. The command-line entry point verifies source hashes and
   byte lengths before loading data and writes `web/data/plan.json`.
3. **`test_plan.py`: assert-based behavior checks.** Tests cover threshold
   boundaries, assessment categories, calendar windows, budget/tie ordering,
   invalid source data, missing coordinates/distance, both archive gaps, unknown
   rain, duplicates, notice review, and the real committed data. Small fixtures
   exist only in this test file; the demo uses the real cache.
4. **`web/data/plan.json`: both modes for all five cities.** Each mode contains
   all its roster sites, the complete ranked list, default allocated codes,
   exclusions, draft notices, and the selected weather evidence. Retaining the
   complete ranking lets the future page change the visit budget by slicing the
   same ordered list. FHIR resource content will be added in Phase 4.

## Run and verify

From `afterstorm/`, using Python 3 and the standard library:

```text
python test_plan.py
python plan.py
python -m unittest discover -v
```

The first command runs the Phase 2 asserts; unittest discovery continues to run
the Phase 1 suite. No installation, framework, database, or build step is needed.
Commands were run through the workspace's required `rtk proxy` prefix.

The test suite was written first and failed with an explicit assertion that the
planner was absent. After implementation and review fixes, **18 assert-based
checks passed**. The Phase 1 suite also passed **14/14 before its commit and
again at the final Phase 2 check**. The real-cache
asserts compare every response hash before/after planning and check that all
106 sites appear in each mode. They also compare the full input structures
before/after `build_plan`.

Optional paths:

```text
python plan.py --config config.json --data-dir data/raw --output web/data/plan.json
```

A changed or unverifiable cached source stops the CLI with an error rather than
quietly using untraceable values. An absent optional weather/forecast source
produces unknown weather; missing required roster, health, or urban sources
stop generation. A missing health response cannot turn every site into a
supposed baseline candidate.

## Allocation rules

- **One budget unit is one site visit**, collecting all recommended categories.
- A valid historical profile with a dominant category at or above `TEST_MIN`
  receives a new assessment in that category. The second category is also
  included if it reaches the threshold. Equal category scores use the stable
  order faecal, pathogen, antibiotic resistance. These are categories, not
  specific assays; the lab chooses the method.
- In a storm, these sites rank by dominant score descending, then usable sewage
  distance ascending, then natural site code. Baseline sites follow them.
- With no qualifying storm, or unknown weather, only no-lab-result baseline
  sites receive visits. Their recommended categories are all three; no score
  is imputed. Baselines rank by sewage distance ascending, then natural code.
- **T21 and T24 have no sewage distance.** They retain `null`, rank after every
  baseline with a usable distance, and visibly say "missing sewage distance;
  ranked last among baseline sites". Natural code orders T21 before T24.
- Invalid/missing category values, invalid/missing sample dates, and duplicate
  lab/roster codes prevent allocation, with the source-data reason retained.
  A missing coordinate prevents a map pin, not a visit. Duplicate urban records
  provide no usable distance rather than an arbitrary tie-break value.
- Ranks exceeding the default budget say "if capacity allows". Draft notice
  eligibility is independent of visit allocation and `TEST_MIN`.

## Weather and date integrity

**Replay uses the rule explicitly selected by the user:** every site in the
city must have a valid daily rainfall record at or above `RAIN_MM` on each
qualifying wet day. The city-wide test uses the minimum of those recorded
values; it does not fabricate a city average. The selected event preserves
every site's actual total, and reports the minimum/maximum range. The most
recent qualifying run is selected; its last observed wet date is the anchor.

The archived rainfall differs between sites. An any-site maximum would have
chosen more recent events in Benevento, Ghent and Oslo while including sites
below 20 mm. The all-site policy prevents that mismatch at the cost of an older,
more conservative replay. This policy is a prototype choice, not a scientific
definition of a storm across a city.

**Missing dates are unknown.** In particular, August 4 and August 27, 2026 are
absent from every site's archive. They break wet-day runs; neither can be a
storm anchor. Null/invalid rain, duplicate dates and wrong-site records also
cannot support a city-wide wet day. The output's `archive.unknown_dates` also
includes dates covered by only part of the city's histories, since source
histories start at different dates. Those extra dates are incomplete city
coverage, not additional claims of an API-wide gap.

**A gap does not prove the rain stopped.** Toulouse's last qualifying observed
wet date is August 3; the absent August 4 breaks the run. Its proposal uses
August 4–5 as the experimental calendar window and explicitly warns that rain
cessation is unknown. A proposed future window does not claim that observations
exist on those dates.

**Live uses the dated cached seven-day city-centre forecast.** It selects the
first threshold-reaching run, preserves actual daily totals and timezone
metadata, and shares that forecast across all sites. Sites are ranked by the
historical category profile and distance, not by invented site-level forecasts.
Malformed forecasts or unknown rain without a detected run produce "unknown",
not "no storm". A known wet run can still trigger a proposal when its following
day is unknown; the boundary warning exposes that uncertainty.

The forecast period and original retrieval timestamps are retained. "LIVE"
identifies the forecast mode, not a continuous connection or an assurance that
the cache has just been refreshed. Refresh with `fetch.py` before a later live
demonstration; `plan.py` never refreshes the cache.

## Experimental windows and notices

For qualifying wet date D, the default window is **D+1 through D+2 inclusive**.
Consecutive wet dates use the last one. Dates remain dates: no clock time is
invented and no timezone conversion is applied. Every storm window carries
"Experimental window (heuristic, not validated)" and its explanatory caveat.

[Directive 2006/7/EC](https://eur-lex.europa.eu/eli/dir/2006/7/oj) is retained as
the brief's context for short-term pollution. The directive's roughly 72-hour
duration is not a validated sampling schedule or a safety clearance. This phase
does not establish that a stream is contaminated, safe, or a designated bathing
water.

Valid historical faecal or pathogen scores at or above `ADVISORY_MIN`, together
with a storm scenario, create a **draft** water-contact notice. It refers to the
actual sample year, including the one 2024 record. It says the coordinator must
review whether to issue it and when to lift it. There is **no expiry field**,
automatic publication, or notice based only on antibiotic resistance.

## Actual cache results

The original data retrieval interval is **2026-10-03T14:28:52Z–14:29:10Z**.
The cached forecasts span October 3–9. Contrary to the brief's earlier
no-storm observation, **Oslo has 42.9 mm forecast on October 8**. Its live plan
therefore allocates five visits, with the experimental window October 9–10.
The other four cached forecasts stay below 20 mm.

| City | Roster | Storm-eligible profiles | Baselines | Live visits | Replay anchor | Replay visits | Replay draft notices |
|---|---:|---:|---:|---:|---|---|---:|
| Benevento | 20 | 6 | 0 | 0 | 2026-04-01 | BN2, BN10, BN3, BN17, BN7 | 6 |
| Coimbra | 20 | 8 | 2 | 2 | 2026-05-10 | C5, C12, C6, C7, C20 | 6 |
| Ghent | 22 | 1 | 5 | 5 | 2025-07-06 | G9, G18, G20, G19, G17 | 0 |
| Oslo | 20 | 5 | 0 | 5 | 2026-06-09 | O12, O11, O14, O13, O4 | 0 |
| Toulouse | 24 | 13 | 3 | 3 | 2026-08-03 | T17, T5, T12, T10, T13 | 7 |

Totals: 106 retained sites, 33 storm-eligible historical profiles, 10 baseline
sites and 19 draft-notice candidates in replay. The actual cache has no invalid
lab exclusions. Ghent uses its spare storm budget on baselines, while Coimbra
and Toulouse have storm candidates ahead of their baselines. Live Toulouse's
baseline order is **T15, T21, T24**.

## Review and boundaries

A fresh read-only review found no Critical or Important bugs. Two Minor
presentation issues were fixed: the live console now names its storm anchor,
and forecast wording no longer calls future wet dates observed. The regression
assert failed before the fix and passed afterward. Baseline reasons also name
their storm scenario and experimental window when one applies.

The planner expects Phase 1's JSON-object rows and the verified APIs' canonical
`YYYY-MM-DD` rain dates. General support for alternate date encodings, arbitrary
row types, or hypothetical future-dated lab results is outside this checkpoint.
The source contract and real cache are tested; no additional parsing framework
or speculative compatibility layer was added. The all-site policy, category
tie order and optional second category are explicit choices documented above.

The page, FHIR resource content, publishing and scientific field validation
remain outside Phase 2. No external system was written to in this phase.

## Output contract for the next phase

`cities[city_id].modes.live` and `.replay` contain:

- `label`, `weather_status`, `message`, `storm`, and forecast/archive coverage;
- `sites`: every roster site, source values, coordinates/map note, categories,
  reason, window, rank, allocation, optional draft notice, and field-source references;
- `ranking`: all eligible site codes in visit order, independent of the default
  budget; `allocated_codes`: its first `VISITS_PER_CITY` entries;
- `notices`: reviewable drafts independent of visit budget; `excluded`: invalid
  source-data reasons.

Top-level `config` records the policy used. `sources` retains URLs, original
retrieval times and hashes from Phase 1. Selected replay totals remain keyed by
site and date; selected forecast totals remain keyed by date. Coordinate
provenance points only to the first-party `/api/sites/all` response.

The user approved committing Phase 2 at this checkpoint. Phase 3 is the
coordinator page using this JSON; it starts only after explicit **proceed**.
