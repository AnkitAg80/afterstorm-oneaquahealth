# UI pass V1 — Visual system for the lower half

Scope: `web/index.html` only. No data, planner, ranking or FHIR change. No new dependencies: the patterns below are recreated in vanilla CSS and JS.

**Why:** the user felt the area below the hero looked plain next to the storm band. The reference they gave, designeer.xyz → Components, lists the libraries behind most polished dashboards: Tremor (dashboard primitives), Magic UI and Aceternity UI (spotlight cards, dot backgrounds, animated lists), Evil Charts (animated SVG charts) and NumberFlow (rolling numbers). Our page is plain HTML, so we recreate their signature patterns rather than import them.

## 1. Category chips with stored-value meters (Tremor pattern)

**What changed:** each visit's plain "faecal + pathogen" text became coloured chips. A chip shows the category, its **stored** 2-decimal value and a small meter.
- The tooltip reads "Stored 2023 relative score … (not a concentration)".
- One colour per category: faecal amber `#a16207`, pathogen rose `#be123c`, antibiotic resistance violet `#6d28d9`.
- Baseline visits show a blue chip "First baseline · no public lab result", plus outline chips for the three categories.

**Where:** new `catChips(site)`, `CAT_FIELD` and `CAT_CLASS`; `.chip` and `.meter` CSS.

**Honesty:** the meter shows the stored value as-is. No new score, no ranking change.

## 2. "All N sites at a glance" tracker (Tremor Tracker pattern)

**What changed:** a strip at the top of the visit panel with one segment per site. Ranked sites come first. Colours follow planning status (planned storm visit, planned first sample, if capacity allows, no visit, excluded), and a ring marks a draft notice.
- Hover or focus shows the site and its status.
- Clicking a planned site scrolls to and flashes its card; clicking any other site pans the map to its pin.
- A legend shows the counts (Coimbra replay: 5 planned, 5 if capacity allows, 10 no visit).

**Where:** new `renderTracker()` (called from `render()`), a `#tracker` container, one delegated click handler; `.tracker` and `.seg` CSS.

## 3. Texture and motion (Magic UI / Aceternity / Evil Charts patterns)

- A subtle dot-grid layer on the page background (22 px, 7% opacity) so the light half isn't flat.
- A cursor-following spotlight on visit cards, notice cards, the Protection check and the hero tiles (CSS radial gradient driven by `--mx`/`--my` from one passive `pointermove` listener).
- Visit cards cascade in (55 ms stagger) when city or mode changes, not while dragging the budget.
- Rain-chart bars and hero mini-bars grow up from the baseline.
- All motion is off with reduced motion.

## Checks

- All 10 city × mode views render with no app errors (only OpenStreetMap tile rate-limit 429s). Segment counts match the roster: Benevento 20, Coimbra 20, Ghent 22, Oslo 20, Toulouse 24.
- C5 shows "faecal 1.00" and "pathogen 1.00" chips with the not-a-concentration tooltip.
- Clicking the C16 segment (outside the budget) pans the map.
- Visit order and counts are unchanged in every view.
