# UI/UX pass U2 + U3 — Compact filing status and sticky summary bar

Scope: `web/index.html` only. No data, planner, ranking or FHIR change. `filed.json` is unchanged.

## U2. Compact filing status

**What changed:** the four-line grey paragraph above the visit list ("Downloads 5 visits as draft FHIR requests… C5 → ServiceRequest 1046, C12 → …") became two compact elements:
1. A tick line: **"5 draft requests ready · nothing is sent"**, plus "· N on hold left out" when relevant.
2. A green chip, **"Filed once to the HL7 Europe sandbox · ServiceRequest 1046–1050 · shape v1"**, shown only on the Coimbra replay view. It opens to a two-column list linking each site to its **live sandbox record**, for example C5 → `https://sandbox.hl7europe.eu/oneaquahealth/fhir/ServiceRequest/1046`. It also says when the drafts were filed and that the current export uses resource shape v2.

**Where:** `updateFhirChrome()` now writes `innerHTML`; new `filedChip()` (`filedSummary()` is kept for other callers); `.fs-line` and `.filed-chip` CSS.

**How it helps:** the visit list starts sooner. A judge can open the real HL7 records in one click (Technical), while the honest "nothing is sent / shape v1" wording stays.

## U3. Sticky summary bar

**What changed:** after you scroll past the top band, a slim dark bar slides in at the top. It shows:
- the city;
- the mode tag ("Replay · 10 May", "Storm forecast 8 Oct", "No storm this week");
- "5 of 5 visits";
- a live review progress bar with "1/11 reviewed";
- buttons: Visits, Notices, Download FHIR (N) (same state as the main button) and ↑ back to top.

The bar is driven by an `IntersectionObserver` on `#hero`. While hidden it's `aria-hidden` and its buttons are out of the tab order. It doesn't print. It slides with motion, or appears instantly with reduced motion. On phones it hides the progress bar and jump buttons.

Jump targets have `scroll-margin-top: 72px`, so headings land below the bar (checked: the Notices panel lands at y = 72).

**Where:** new `#summary-bar` element, `renderSummaryBar()` called from `render()`, an observer and one delegated click handler in `start()`; `.summary-bar` and `.sb-*` CSS.

**How it helps (UX):** on a long page the coordinator always knows which city and mode they're in and how far the review has got, and can download or jump without scrolling back up.

## Checks

- Coimbra replay: the status reads "5 draft requests ready · nothing is sent", and the chip opens links to ServiceRequest/1046 … 1050.
- The bar is hidden at the top, shown after scrolling, and updates from 0/11 to 1/11 after approving C5. "Notices" lands at y = 72.
- No app console errors (only OpenStreetMap tile rate-limit 429s). Test review data cleared afterwards.
