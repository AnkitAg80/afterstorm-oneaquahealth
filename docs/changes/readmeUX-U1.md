# UI/UX pass U1 — Layout

Scope: `web/index.html` only. The planner, the data, the FHIR export and ServiceRequests 1046–1050 are unchanged.

## 1. Draft notices became a full-width card grid

**What changed:** the notices panel moved out of the narrow right column into its own full-width section below the map and visits.
- Each notice is now a card in a responsive grid: 3 per row on desktop, 1 on phones (`minmax(min(100%,350px),1fr)`).
- Approved cards turn green and held cards turn amber.
- The description and the Los Angeles comparison span the full width.

**Where:** the `#notice-panel` section is now after `.workspace` (class `notice-wide`); new CSS block "U1: notices as a full-width card grid".

**How it helps (UX):** about 1,300 px of identical stacked rows became two rows of cards. All six notices, with their confirmation dates, are visible at once.

## 2. Protection check moved under the map; the left column no longer goes blank

**What changed**
- The Protection check now sits under the map in the left column, inside a new `.left-inner` wrapper.
- The whole wrapper is pinned while you scroll, but only on screens at least 1000 px tall and 761 px wide. On shorter screens it scrolls normally, so nothing is cut off.
- The right column now holds only the visit list.

**How it helps:** the large empty area beside the visit list is gone (in screenshots too), and the map and protection check stay together, since they talk about the same pins.

## 3. More compact visit cards

**What changed**
- The dates and the "Experimental window (heuristic, not validated)" label sit on one line.
- The "Filed as …" line is smaller.
- The closed "Citizen task card" and "Why this site?" sit side by side and open to full width.

The cards are about 25% shorter. Every label and honesty statement is unchanged.

## 4. Protection check wording

**What changed**
- Visits with the same categories and no notice are grouped into one sentence. Oslo replay now reads "All 5 planned visits (O12, O11, O14, O13, O4) reassess antibiotic resistance and draft no contact notice", instead of the same sentence five times.
- With no storm in view, the card starts with "No storm in this view, so no contact notices are drafted." and says "Closest to the prototype notice setting" instead of "Just under".
- The Coimbra replay text is unchanged (the video script depends on it).

## Checks

- All 10 city × mode views render with no console errors. Visit, notice and pin counts are unchanged:
  - Benevento replay: 5 visits, 6 notices.
  - Coimbra replay: 5 visits, 6 notices.
  - Toulouse replay: 5 visits, 7 notices.
- Hovering card C12 highlights pin 2.
- The "covers every notice site" button gives `visits=8` and 8 cards; setting the budget back to 5 restores the plan.
