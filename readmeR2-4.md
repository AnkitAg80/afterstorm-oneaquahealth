# Round 2, Part 4 — citizen task card

## WHAT

Each planned visit has a citizen task card. A baseline visit is titled "First look — citizen task card". Any other visit is titled "After-storm look — citizen task card". The card names the site, coordinates to 5 decimal places, and the experimental window, or "any day" when the visit has no window. It asks five yes / no / unsure observations and two free fields. Answers stay in this browser. Printing shows only the task cards.

## WHERE

`web/index.html`

- `citizenCard()`, `printTaskCards()`, and `afterstorm-citizen-v1` in `localStorage`, keyed by city, mode, site, and `evidenceSig('visit', code)`.
- A "Citizen task card" disclosure on every visit card.
- "Print this card" on the card, and "Print all task cards" in the visit panel header.
- `#print-area`, shown only while `body` has `print-card`. Each printed card is a `.task-sheet` with `break-after: page`. `afterprint` removes the class and clears the area.

## HOW

Impact (awareness and participation) and innovation (citizen science). The person at the stream records what they can see from the bank. The answers do not change the visit order, the tests, the notices, the review count, or the FHIR download.

The card follows three public practices, cited here and not on the page:

- WHO, *Guidelines on recreational water quality* (2021), sanitary inspection and citizen science for visual monitoring: https://www.who.int/publications/i/item/9789240031302
- US EPA sanitary surveys for recreational waters: observations of wildlife, pollution sources, site conditions, and photos: https://www.epa.gov/beaches/sanitary-surveys-recreational-waters
- OneAquaHealth's statement that volunteer observations complement lab data: https://www.oneaquahealth.eu/citizen-science-project/

## CHECKS

- `python test_plan.py`: 23 assert-based checks passed.
- `python test_fetch.py`: 14 tests, OK.
- `python plan.py`: exit 0. It changed only `generated_at` and `built_at`. Those timestamps were restored. Ranking and the filed files were not changed.
- All 10 city × mode views rendered with no console error. Every visit card has one task card. Cities with no visits have none.
- Coimbra replay C5 is titled "After-storm look — citizen task card". Choosing Yes for a discharging pipe and No for sewage smell, then reloading, kept both answers. Review progress stayed "0 of 11 reviewed". The download button stayed "Download FHIR (5)". The visit order stayed C5, C12, C6, C7, C20.
- Print this card put one sheet in `#print-area`, hid the page header, and did not include the visit list. After the print event, the page class was cleared. Print all task cards produced 5 sheets, one per planned visit.
- Ghent live, site G18, is titled "First look — citizen task card".
- Screenshots: `C:\Users\ankit\Downloads\oneaqua\_shots\r2-4.png` and `r2-4-mobile.png`. On a 390-wide screen the checklist stays inside the visit card.
