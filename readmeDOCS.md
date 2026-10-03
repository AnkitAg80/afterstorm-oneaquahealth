# Phase 5 — submission documents

Phase 5 writes the README, the Devpost text, and the demo script. It does not create a GitHub remote, deploy the page, or submit on Devpost.

## What changed, where, and why

1. **`README.md`.** The submission README now has the problem, the solution, the users, the impact, Track 6 alignment, the approach comparison, the limitations, the run commands, the data-source table, and screenshots. The comparison is by approach: existing tools forecast risk or rank overdue sites from past data; AfterStorm plans the sampling that refreshes the evidence. No other team's project is named. Measured facts are limited to the cache: 96 lab records (95 from 2023, one from 2024, site BN14 on 2024-08-05), 106 official sites, 10 without a lab result, the five replay dates, the 2026-10-03 forecast snapshot, and ServiceRequests 1046–1050. The FHIR section states the 22 Python structural checks and says the HL7 validator jar and sandbox `$validate` were not used.

2. **`DEVPOST.md`.** Paste-ready track, problem, solution, build, challenges, and next-step text for the Devpost form. It uses the same approach sentence and the same measured facts. It is not submitted.

3. **`VIDEO-SCRIPT.md`.** A 4:10 script, inside 3:30–4:30. It opens on Coimbra replay of 2026-05-10, including the demonstration line. The Live section tells the recorder to read this week's forecast card and does not give them a weather sentence to memorise. At 3:30 the script holds `https://sandbox.hl7europe.eu/oneaquahealth/fhir/ServiceRequest/1046` on screen for about 10 seconds. A browser GET of that URL on 2026-10-04 returned HTTP 200 and `text/html`, and a FHIR read of the same resource returned draft proposal, identifier C5, dates 2026-05-11 to 2026-05-12, and the demonstration sentence.

4. **`docs/screenshots/`.** New captures from the local page, taken against the committed cache: `coimbra-replay.png`, `coimbra-replay-why.png`, `oslo-live.png`, and `oslo-live-mobile.png`. The older JPEG screenshots showed the previous Oslo forecast (42.9 mm on 8 Oct) and were removed so the folder matches the cache the README describes.

## How it helps

A judge can read the product, the limits, and the filed ids without treating a forecast sentence as permanent. The person recording the video starts on the Coimbra replay, proves the filing in the browser, and describes Live from the card on recording day.
