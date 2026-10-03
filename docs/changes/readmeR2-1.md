# Round 2, Part 1 — correctness

## WHAT

The export now puts one request type in `ServiceRequest.code` and one category in each `orderDetail`. A review is kept only when it still matches the storm date, categories, window, and notice text it was made against. Unknown rain is no longer described as "no storm". The page says "no lab result in the public feed", calls the dates a post-storm reassessment, labels 20 mm and 0.5 as prototype settings, and opens on Coimbra replay with a budget of 5.

## WHERE

- `fhir_export.py`: `REQUEST_SYSTEM`, `request_code()`, `order_details()`, `build_service_request()`, and structural checks 7–9. `proposal_url()` is unchanged.
- `test_plan.py`: `test_c5_replay_tie_and_fhir_requests` expects 24 structural checks and the C5 shape (post-storm reassessment; orderDetail faecal, then pathogen). `test_fhir_slice_baseline_window_and_sandbox_reference_policy` expects the baseline request type and three orderDetails.
- `web/index.html`: `start()` defaults, `renderDecision()`, `renderWeather()`, `evidenceSig()`, `reviewOf()`, `setReview()`, `reviewTally()`, `filedLine()`, `filedSummary()`, the mode button, and the settings paragraph.
- `docs/changes/readmeFHIR.md`: section "Resource shape v1 (filed) vs v2 (current)".
- `plan.py` reason strings did not say "never". They already say "No lab result".

## HOW

Technical credibility. A CodeableConcept no longer lists different categories as if they were the same concept. An old Approve cannot attach itself to a new storm date or a new notice. Incomplete rain stays incomplete. The filed ids 1046–1050 stay the v1 resources that were posted.

## CHECKS

- `python test_fetch.py`: 14 tests, OK.
- `python test_plan.py`: 22 assert-based checks passed. Inside that run, the structural report length is 24 and every check passed.
- `python plan.py`: exit 0. Structural report printed 24 passes, including request-type code, orderDetail order, and `resource-shape-v2`. Oslo bundle still has 0 entries. Coimbra replay anchor is still 2026-05-10. Allocated order is still C5, C12, C6, C7, C20. C5 `code` is `post-storm-reassessment` and `orderDetail` is faecal, pathogen.
- `web/data/filed.json` SHA-256 `1b7f9fb3e57b452c822341d86278aff6306a7b831ab42b213f19acfdb398613b` (936 bytes) before and after. `web/data/fhir-bundle-coimbra-replay.json` SHA-256 `be825bf831f4b95a20f5c9ee61e6402a5434e7b2a9c2bbf8637a23b4eb4f858f` (10299 bytes) before and after. Neither file was posted.
- Headless Chrome, all 10 city × mode views at budget 5: each rendered a decision sentence and reported no console error. Tile HTTP 429 was ignored.
- `http://127.0.0.1:8765/` with no query string landed on `?city=CO&mode=replay&visits=5`. The answer begins "Replay: heavy rain hit Coimbra… Plan post-storm reassessment at 5 streams…". The mode button reads "Latest forecast". C5 reads "Filed as FHIR ServiceRequest/1046 (filed with resource shape v1)".
- Console check `data.cities.OS.modes.live.weather_status='unknown'; render();` produced "Rain data for Oslo is incomplete, so a storm can't be ruled out…" and did not produce "No storm is forecast". The Oslo pill had no storm dot. The rain tile label was "Rain data".
- Approve C5, append `x` to that review's `sig` in `afterstorm-review-v2`, reload: C5 shows "Evidence changed since your review — review again", the Approve button is not pressed, and the progress reads "0 of 11 reviewed".
- Screenshot: `C:\Users\ankit\Downloads\oneaqua\_shots\r2-1.png` (1440×1800). A 390-wide capture, `r2-1-mobile.png`, still shows the reassessment sentence, the date tiles, and the coordinator-confirms line without overlap.

Part 0 commit, before these edits: `8a8ae8602654c8e74f66df2aac997fdcb8061db3`. Part 1 is not committed.
