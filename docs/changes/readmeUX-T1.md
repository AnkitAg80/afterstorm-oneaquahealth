# UI transformation T1 — App shell, four pages, one dark theme

Scope: `web/index.html` only. No data, planner, ranking or FHIR change.

**Why:** the user found the lower half "really bad". There was a large empty gap beside the visit list, the light lower half had no visual relationship to the dark top band, and everything sat on one very long page. They asked for separate pages and for shadcn/ui, Radix and Base UI as component references.

Our stack is plain HTML, CSS and JS, and those three are React libraries. So we adopt their **design language** (shadcn's dark tokens: subtle 1 px translucent borders, muted surfaces, rounded-xl cards, segmented Tabs; Base UI-style enter animations) without importing them.

## 1. Four pages with real URLs

| Page | URL | Content |
|---|---|---|
| Overview | `#/` | Plain-English answer, rain, dates and visits tiles, the steps, Protection check, and a new **Next steps** card linking to the other pages |
| Plan & map | `#/plan` | The map **pinned at nearly full viewport height** beside the visit list: tracker, review progress, filing chip, visits |
| Notices | `#/notices` | The notices grid with confirmation dates and the Los Angeles comparison |
| Evidence & data | `#/evidence` | Rain chart, "How often do storms like this hit…", full roster, exclusions, data sources and settings, limitations |

- **Routing:** a small hash router (`pageFromHash`, `setPage`, `goPage`). Back and Forward work (checked: evidence → back → notices → back → overview).
- The page changes with a short fade-up, or instantly with reduced motion.
- The steps strip and other in-page jumps switch page first (`PAGE_OF` map), then scroll to the target.
- "Show on map" from the Evidence page's roster switches to Plan & map before panning.
- Deep links still work: `#card-C5` opens Plan & map with the C5 citizen card open; `#notice-C16` opens Notices with C16 open.
- Leaflet is resized and refitted whenever Plan & map becomes visible (`invalidateSize`).

## 2. Shared sticky header and controls

- The header is sticky, dark and frosted, with **segmented page tabs** (shadcn Tabs style). The active tab has a raised surface, and the Notices tab carries an amber count badge (6).
- On the right, a compact status shows city · mode tag · visits, plus the primary **Download FHIR (N)** button. This replaces the old floating summary bar and its scroll observer.
- The city, mode and budget controls sit in one compact control bar at the top of **every** page. The budget stepper and slider share one row.

## 3. One "night water" theme everywhere (fixes "no correlation")

- **shadcn-style dark tokens, tinted to the brand:** canvas `#0a1a17`; cards with a `#132b25 → #10241f` gradient and `#ffffff14` borders; ink `#e7f1ec`; muted `#9db3a9`; emerald accent `#6ee7b7`; amber `#f2c46d` for storms and notices.
- All 54 hard-coded light backgrounds were mapped to dark equivalents: buttons, inputs, steppers, badges, review progress, tracker, notices, task card, roster table and Leaflet controls and popups.
- Category chips use light-on-dark tints: faecal `#f5c46b`, pathogen `#fda4af`, antibiotic resistance `#c4b5fd`.
- Pin, tracker and legend colours now match one another: planned `#1f9d73`, baseline `#3b82c4`, capacity `#d9a441`, no visit `#7d8f86`, excluded `#e0786d`.
- **A dark map:** OpenStreetMap tiles are shown through a CSS filter (invert, hue-rotate, desaturate). The pins and site names stay vivid.
- The rain charts were recoloured for dark: emerald bars, an amber threshold line, light labels.
- The hero background is now transparent over the shared canvas, so there's no seam.

## Checks

- All 10 city × mode views render with the expected visit and notice counts, and no console errors.
- The mode toggle state is correct.
- `python test_plan.py`: 23 checks passed.
- Screenshots: `_shots/t1b-overview.png`, `t1-plan.png`, `t1b-notices.png`, `t1b-evidence.png`.

**Next (T2):**
- Shadcn-style components for the visit list: wide horizontal rows, with the citizen task card and "Why this site?" opening in a **side Sheet** instead of stretching the list.
- Then T3: Notices and Evidence polish, plus the phone layout.
- Then T4: regression checks and gallery re-capture.
