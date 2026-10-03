# UX Part 1 — Readability foundation

Scope: `web/index.html` only. The planner, the data and the FHIR resources are unchanged.

## 1. Type scale and contrast

**What changed**
- Body text is now 16 px.
- Secondary text is at least 13 px (it used to be 9–11 px).
- Headline figures are 28–34 px.
- The grey text colour is darker (`--muted` changed from `#606e65` to `#536158`).
- Small all-caps labels are now sentence case.
- Numbers use tabular figures, so digits line up.

**Where:** the `<style>` block (the whole block was rewritten; every selector the script uses is kept).

**How it helps:** text is readable at arm's length and in a screen recording, and it meets accessibility guidance for text size and contrast. Judges score "clarity of interface" and "accessibility".

## 2. Fonts, surfaces and interaction basics

**What changed**
- **Geist** (body) and **Geist Mono** (numbers and site codes), bundled locally as variable WOFF2 files: `web/vendor/fonts/Geist-Variable.woff2` (68 KB) and `GeistMono-Variable.woff2` (70 KB).
  - Downloaded with the user's approval from the official `vercel/geist-font` repository on 2026-10-04.
  - SIL Open Font License, included as `web/vendor/fonts/OFL.txt` (the repository's `LICENSE.txt` is kept too).
  - Loaded with `@font-face` (`font-display: swap`); the body font is preloaded.
  - If the files are missing, the page falls back to Segoe UI Variable, then system-ui.
- The headline stays serif (Iowan, Charter, then Georgia) for a serif-headline, sans-body pairing.
- Soft tinted shadows on cards, rounded corners and 44 px tall controls.
- A clearer focus ring, smooth scrolling (turned off when the user asks for reduced motion), and hover and press transitions on buttons.
- The fonts are local files, so the page still works offline (only the map tiles need internet).

**Where:** the `:root` tokens and the base rules in `<style>`.

**How it helps:** the interface feels finished, big targets are easier to hit, and keyboard users can see where they are.

## 3. Plain-language copy

**What changed:** developer wording became coordinator wording.

| Before | After |
|---|---|
| `RAIN_MM`, "wet-day runs" | "a day with 20 mm of rain or more" |
| "Python built each ServiceRequest; this page only slices and wraps" | "Downloads these 5 visits as draft FHIR requests. Nothing is sent." |
| "The next daily total is below the configured storm threshold" | "Rain fell below 20 mm the next day…" |
| "Rain archive coverage" | "How often do storms like this hit Coimbra?" |
| "Policy: …" | "Settings used: …" in full sentences |
| "Forecast fetched 2026-10-03 20:04:20 UTC" | "Forecast updated 3 Oct 2026, 20:04 UTC" |

All honesty labels are kept word for word: "Experimental window (heuristic, not validated)", "Draft — requires coordinator review", the replay demonstration sentence, and "Filed as FHIR ServiceRequest/…".

**Where:** the `renderWeather`, `updateFhirChrome`, `filedSummary`, `renderCoverage` and `renderSources` functions; new `niceTime` and `boundaryText` helpers; the intro paragraph; the budget note.

**How it helps:** a coordinator understands the page without knowing the code.

## 4. Fewer repeated messages

**What changed**
- Removed the LIVE/REPLAY badge (the toggle already shows the mode).
- The one-line status summary is now read out to screen readers only, not shown.
- The replay banner is now one clear message: "Replay of a real storm · 10 May 2026", with the demonstration line beneath it.
- The "saved default bundle" link moved into the "Data sources and settings" section (it named Oslo while you were looking at Coimbra).

**How it helps:** the important facts stop competing with copies of themselves.

## 5. Map zoom with touchpad and mouse (requested by the user)

**What changed:** the map previously zoomed only with the + and − buttons, because wheel zoom was turned off to stop the page getting trapped. It now follows the Google Maps pattern:
- A touchpad pinch (which browsers report as Ctrl + wheel) or Ctrl + scroll zooms the map, and the browser page itself doesn't zoom.
- A plain scroll over the map scrolls the page and briefly shows the hint "Pinch or Ctrl + scroll to zoom · click the map to zoom with scroll".
- Clicking or focusing the map turns on plain-scroll zoom, shown by a green outline. Leaving the map turns it off.
- Zoom moves in quarter steps (`zoomSnap: .25`, `wheelPxPerZoomLevel: 45`), so pinching feels smooth.
- A line under the legend lists every way to zoom.

**Where:** `initializeMap()` (a wheel listener on the map frame that runs first, plus click, focus, blur and mouseleave handlers); a `#map-hint` overlay in the map frame; `.map-hint` and `.map-active` styles.

**How it helps:** zooming works the way people expect on a laptop, without stealing the page scroll.

**Checked with simulated events:**
- A plain scroll burst left the zoom at 10.5 and didn't block page scrolling.
- A pinch-in burst zoomed from 10.5 to 12 and blocked the page zoom.
- A pinch-out burst zoomed back to 10.75.
- After a click, plain scrolling zoomed the map; after leaving the map, it didn't.

## Checks run

- All 10 city and mode views render. No console errors.
- Visit counts are unchanged: Benevento live 0, replay 5; Coimbra live 2, replay 5; Ghent 5/5; Oslo 0/5; Toulouse 3/5.
- The smallest visible text is 11 px, used only for the map's copyright line; everything else is at least 13 px.

**Follow-up for the docs:** `VIDEO-SCRIPT.md` quotes the old banner text "REPLAY of real storm on 2026-05-10". It must be updated to "Replay of a real storm · 10 May 2026" in the final docs pass.
