# UX Part 5A — Storm hero redesign

Scope: `web/index.html` only. The planner, the data and the FHIR resources are unchanged.

**Why:** the user felt the top of the page looked plain and generic. Their reference was designeer.xyz, which is a directory of design galleries (Godly, Herogrids, Supahero, Sombra and others), not a component kit. The common pattern on those galleries: one bold, purposeful hero where the key answer is the visual centrepiece and the controls are built into it.

## 1. A full-width "storm band" hero

**What changed:** a deep-green band (`#0d2621` → `#133a32`) runs edge to edge from under the header, with a rounded bottom edge. Its background layers are:
- Two slowly drifting colour glows (forest green and water blue), plus a dim third one at the bottom.
- Faint stream contour lines (inline SVG, 9% opacity, fading out with a mask).
- Animated diagonal rain streaks, shown **only when a storm is in view**. Live weeks with no storm stay calm.

All motion stops when the user asks for reduced motion. Everything is CSS and inline SVG: no image files, no network requests.

**Where:** the `#hero` section replaces the old title block, controls card, replay banner and decision card; the CSS is under `/* Hero (storm band) */`. The header turned dark to join up with the band. `html, body { overflow-x: clip }` stops the full-width band causing a sideways scrollbar (checked: 1293 px page = 1293 px viewport; at phone width 375 = 375).

## 2. The answer is the headline

**What changed:** the plain-English decision is now the page `<h1>` (26–40 px, white, key facts in mint), with a status line above it: a pulsing dot plus "Live forecast · updated …" or "Archive replay · past data". The product description and "Based on 96 lab records from 2023–24" sit at the top of the band.

## 3. Controls in a frosted-glass bar

**What changed:**
- City is now one-tap **pills** instead of a dropdown. An amber dot marks cities that have a storm in the current mode, so you can see where the action is before clicking.
- The mode toggle, stepper and slider are restyled for the dark band.
- The original `<select>` stays in the page, hidden, so all existing logic and links keep working.

## 4. Three visual tiles

| Tile | What it shows |
|---|---|
| **Rain** | A large number that counts up (forecast mm, the replay min–max across sites, or "wettest day this week"), a mini bar chart (7-day forecast or every site's rain, highest first) with the 20 mm line dashed in amber, and a one-line meaning |
| **Sample on** | Calendar-style date tiles (MAY 11 → MAY 12) with the unchanged label "Experimental window (heuristic, not validated)". With no storm: "Any day" for unsampled streams, or "—" |
| **Site visits** | A progress ring (visits used out of budget) that animates on change, the count, how many qualify, how many were never sampled, and "One trip covers every test at a site" |

The tiles lift slightly on hover. The numbers count up only when city or mode changes, not while dragging the budget slider.

## 5. Steps on the band, and the rain chart below

**What changed**
- Storm → Plan visits → Review & file now sit in the band as frosted cards. Done steps show a mint ✓ and the current step has a mint outline.
- The light "Rain evidence" card below now shows the explanation and a chart: the 7-day forecast in live mode, or every site's rain on the storm day in replay (new `siteRainChart`). Its caption explains the dashed 20 mm line.

## Checks run

- All 10 city and mode views render with no app errors. The only console error was an OpenStreetMap tile rate limit (HTTP 429) after rapid automated city switching.
- Hero tile examples:
  - Coimbra replay: "24.43–24.6 mm · all 20 sites above 20 mm", MAY 11 → MAY 12, 5 of 5.
  - Oslo live: "Wettest day this week 17.4 mm · no storm", "No storm, so no sampling window", 0 of 5.
- Rain streaks appear only in storm views. The storm dots are correct (every city has a past storm; none has a storm this week).
- Phone width 375 px: no horizontal overflow, tiles stack, headline 24 px.
