# UI transformation T2–T4 (fix-all) — Replay clarity, cited trigger, wide rows, side sheets, gallery

Scope: `web/index.html`, `README.md`, `DEVPOST.md`, `docs/gallery/`, `web/og.png`. No data, planner, ranking or FHIR change.

## 1. Removed the track label from the header
"OneAquaHealth · Track 6" is gone from the visible header (user request). It stays only in the hidden link-preview meta tags.

## 2. Replay clarity (the user asked why "10 May" appeared everywhere)

**Problem:** the date was repeated four times (header tag, banner, kicker line, headline), and nothing explained why a past storm was shown.

**What changed**
- **One explaining banner:** "Replay of a real storm · 10 May 2026 — You're seeing what AfterStorm would have planned the day after this storm, using real past data. No heavy rain is forecast this week." (or "A storm is also forecast this week."). It has a **"See latest forecast →"** button that switches mode.
- The "Archive replay · past data" kicker above the headline is removed in replay mode. Live mode keeps its "Latest saved forecast · fetched …" kicker.
- The header tag says **"Past storm"**, with no date. The headline keeps the date once, because the date is part of the answer.

## 3. The 20 mm trigger now has a cited basis

20 mm per day matches the **WMO/ETCCDI "very heavy precipitation day" index (R20mm)**, an official daily-rain index ([ETCCDI list of 27 core indices](https://etccdi.pacificclimate.org/list_27_indices.shtml)). The 7.6 mm/h WMO/NWS heavy-rain *rate* is an hourly intensity measure. Our data are daily totals, so it can't be checked; the page says so.

**Where:** the Rain evidence card's rule sentence; a new "Why 20 mm?" paragraph in Evidence & data → Data sources and settings; `README.md` (the storm-day paragraph); `DEVPOST.md` (the "What it does" bullet). It remains labelled a prototype setting, to be calibrated per city.

## 4. Wide visit rows (shadcn data-row pattern)

Each visit is now one horizontal row:
- rank;
- **main column:** site code and name, category chips, dates with the experimental-window label, the filed note;
- **action column:** Approve / Hold, then compact **Task card · Why? · Map** buttons.

Below 1100 px the action column wraps under the main column.

## 5. Side sheets (shadcn Sheet pattern, Base UI-style enter animation)

**What changed:** the citizen task card and "Why this site?" no longer stretch the list. They open as a **right-hand side panel** (540 px, full width on phones) over a dimmed, blurred backdrop.
- The panel has a sticky header with the site, and a × close button.
- **Close options:** ×, Escape, or clicking the backdrop.
- Only one sheet is open at a time. Page scroll is locked while a sheet is open.
- Focus moves to the close button when a sheet opens and back to the trigger when it closes.
- It slides in (reduced motion: appears instantly).
- Language switching keeps the sheet open. Printing still uses the separate print layout.
- The `#card-C5` deep link opens the sheet without scrolling the page behind it.

**Bug found and fixed while building this:** entry animations with `fill-mode: both` left an identity `transform` on `.page`, `.workspace` and the visit card. Any transform turns `position: fixed` into "fixed to that element", which trapped the sheet inside the card. In addition, `main{z-index:1}` put it under the header. Those animations now use `fill-mode: backwards`, and `main` has `z-index: auto`. The visit-card spotlight no longer needs `isolation`.

## 6. Notice confirmation strip

The date picker now sits in a tidy dashed box: status line on top, then label and dark date input on one row.

## 7. Gallery re-captured in the new design

`01` Overview hero · `02` Plan & map · `03` Notices grid · `03b` C16 open · `04` citizen card sheet in Portuguese · `05` HL7 sandbox record (unchanged). `web/og.png` was re-cut from the new hero.

## Checks

- All 10 city × mode views: correct visit and notice counts, correct header tag ("Past storm" / "No storm this week"), no console errors.
- **Sheet:** opens fixed at full height on the right, above everything; focus goes to ×; Escape, backdrop and × all close it; the language switch keeps it open.
- **Phone (375 px):** no overflow on any page, and the sheet is full width.
- `python test_plan.py`: 23 passed. `python test_fetch.py`: OK.
