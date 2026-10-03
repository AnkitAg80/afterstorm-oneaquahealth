# Round 2, Part 5b — finish the confirmation sample

## WHAT

The confirmation date is visible without opening the notice. The earliest day is the day after the storm window. A saved date is kept only for the notice evidence it was set against. The notices panel states the Bathing Water Directive rule and the Los Angeles comparison.

## WHERE

`web/index.html`

- `confirmationMin()`, `confirmRecord()`, `confirmStrip()`, and `afterstorm-confirm-v2`.
- The date input and status line sit under the notice head. The purpose, the not-a-class sentence, and the Annex IV.4 quote stay inside "Read the draft notice".
- The notice description ends with the Directive sentence. The Los Angeles sentence is the last paragraph of the notices panel.

## HOW

Impact. A judge sees that the notice has an end, and that the end date cannot fall inside the storm window. If the notice evidence changes, the old date is marked out of date instead of being treated as still valid.

## CHECKS

- `python test_plan.py`: 23 assert-based checks passed.
- `python test_fetch.py`: 14 tests, OK. `plan.py` was not re-run; this part does not change the plan.
- Coimbra replay, notice C5, details closed: the strip reads "No confirmation date set yet" and the date input `min` is 2026-05-13. A value of 2026-05-12 is `rangeUnderflow`.
- Saving 2026-05-13 and appending `x` to that record's `sig` shows "Evidence changed — set the confirmation date again" with the notice still collapsed. It does not say the sample is planned.
- Both sentences are in the notices panel: the EU Bathing Water Directive sentence at the end of the description, and the Los Angeles County 72-hour sentence at the bottom.
