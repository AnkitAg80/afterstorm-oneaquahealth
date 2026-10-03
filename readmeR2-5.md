# Round 2, Part 5 — confirmation sample

## WHAT

A notice that follows a storm window now carries a confirmation sample. The plan stores no date. The coordinator picks the day in the browser, after the experimental window. That day is not written into the visit order or the FHIR download. On a citizen task card, a storm window is labeled "(experimental window)" after the dates. A visit with no window still says "any day".

## WHERE

- `plan.py`, inside the draft-notice branch of `city_plan()`: `confirmation_sample` with `date: None`.
- `web/index.html`: `confirmationBlock()` inside each notice, `afterstorm-confirm-v1` in `localStorage` keyed by city, mode, site, and storm anchor date, and `citizenWhen()`.

## HOW

Impact. The draft notice can now end. The extra sample is what lets a coordinator lift or keep it. It is not a bathing-water class and it is not a safety clearance.

## Directive wording

Read on 4 October 2026 from EUR-Lex, Directive 2006/7/EC, Annex IV, point 4:

https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX:32006L0007

> In the event of short-term pollution, one additional sample is to be taken to confirm that the incident has ended. This sample is not to be part of the set of bathing water quality data. If necessary to replace a disregarded sample, an additional sample is to be taken seven days after the end of the short-term pollution.

The page uses the first two sentences. The third sentence is a different sample, taken only if a disregarded sample has to be replaced. The page does not choose that day.

## CHECKS

- `python test_plan.py`: 23 assert-based checks passed.
- `python test_fetch.py`: 14 tests, OK.
- `python plan.py`: exit 0. Coimbra replay is still C5, C12, C6, C7, C20. C5 `confirmation_sample.date` is `None`. The ServiceRequest does not contain the confirmation sample. The sandbox was not posted.
- All 10 city × mode views rendered with no console error.
- On a fresh Coimbra replay notice, the date input is empty. Setting C5 to 2026-06-02 left the ServiceRequest JSON unchanged, and that day is not in the bundle the download builds. The plan date stays `None`.
- The notice shows the Annex IV.4 sentence above, the purpose, and "The coordinator sets the day, after the experimental window. The page does not choose it."
- C5's citizen card reads "11 May 2026 – 12 May 2026 (experimental window)". Ghent live G18 reads "any day".
- Screenshots: `C:\Users\ankit\Downloads\oneaqua\_shots\r2-5.png` and `r2-5-mobile.png`. On a 390-wide screen the confirmation block stays inside the notice.
