# AfterStorm demo script

Target length **4:20**, inside 3:30–4:30. The problem section gained two sentences, so speak it briskly. Speak at a calm pace, about 130 words a minute. The times below include clicks and short pauses. If you run long, shorten the Why-card reading. Do not drop the sandbox shot.

Record the screen with the page already open. Start a local server from `afterstorm/` if it is not running:

```text
python -m http.server 8765 --bind 127.0.0.1 --directory web
```

Have two tabs ready before you hit record:

1. `http://127.0.0.1:8765/?city=CO&mode=replay&visits=5`
2. `https://sandbox.hl7europe.eu/oneaquahealth/fhir/ServiceRequest/1046` (leave this tab in the background until 3:30)

Do not refresh the forecast unless you mean to. If you do run `python fetch.py` and `python plan.py` before recording, the Live card will change. Read whatever it shows. Do not recite a weather sentence from memory.

## 0:00–0:20 · Hook (about 45 words)

**On screen:** Coimbra, Archive replay, budget 5. The banner is visible: `REPLAY of real storm on 2026-05-10`, and the line `replay scenario of the real 2026-05-10 storm — demonstration`. Do not start on Live.

**Say:**

Ninety-six lab records. Ninety-five are from 2023. One is from 2024. The official roster has 106 streams, and 10 of them have never had a lab result. This is Coimbra on a real archived storm, 10 May 2026. It is a replay, not a forecast.

## 0:20–0:50 · Problem (about 65 words)

**On screen:** Stay on the same banner. Gesture at the date.

**Say:**

Heavy rain carries street runoff and sewer overflows into these streams. Faecal contamination, pathogens and antibiotic resistance are where stream health meets the health of people and pets. The lab file does not say what is in the water this week. Existing tools forecast risk, or they rank overdue sites from past data. AfterStorm does something narrower. It plans the sampling that refreshes the evidence: which stream, which category, and which days, inside a visit budget. This is our Track 6 entry: early warning and resilience planning.

## 0:50–2:25 · Coimbra replay (about 180 words)

**On screen, in order:**

1. Point at the archived-rain figure, 24.43–24.6 mm on 10 May 2026, and at the dates 11 May–12 May. The amber label says the window is experimental and not validated.
2. Scroll to the map. Five dark pins are the planned visits. The legend is text as well as colour.
3. Visit 1 is **C5 Mina Hospital**, faecal and pathogen, 11 May 2026 – 12 May 2026. The line under it reads **Filed as FHIR ServiceRequest/1046**.
4. Open **Why this site?** Leave it open. The reason says faecal and pathogen are tied at 1.00. Sewage works are 2398.28 m. Archived rain at this site is 24.43 mm. Antibiotic resistance shows 0.35, source 0.3465.
5. Set the site-visit budget to **1**. The list becomes C5 only. Set it back to **5**. The list returns to C5, C12, C6, C7, C20.
6. Open the draft-notice panel. Six notices. Open C5. The text says precautionary, avoid water contact for people and pets, and that the coordinator decides whether to issue it.

**Say:**

Every site in Coimbra cleared 20 millimetres on 10 May 2026. The proposed dates are the next two calendar days, 11 and 12 May. The page calls that an experimental window. Daily totals never tell us the hour the rain stopped, and this is not a safety clearance.

C5, Mina Hospital, is first. Faecal and pathogen are tied at the top of its 2023 record. The lab team chooses the method. We do not name an assay. Under the visit: filed as FHIR ServiceRequest 1046.

The budget is five site visits. One visit collects every category on that line. Drop it to one visit, and only C5 remains. Put it back.

These six notices are drafts. Nothing has been sent. A person decides whether to warn people and pet owners, and when to lift that warning.

## 2:25–3:00 · This week's forecast (about 40 words, then read the card)

**On screen:** Click **Live forecast**. You may stay on Coimbra or switch the city to Oslo. Either is fine. Bring the weather card and the seven-day chart fully into frame.

**Say:**

Live forecast. This is this week's cached city-centre forecast. The time beside the Live badge is when that forecast was fetched. Here is what the card shows today.

**Then read the screen. Do not use a memorised weather line.**

Say the city, the fetched-at time, the large figure on the card, the dates under the chart, and how many visits are listed. If the card names a heavy-rain day and lists storm visits, open the first visit and read its dates. If the card does not schedule storm sampling, say the words that are actually printed, and if baseline visits are listed, say that those sites have no lab result yet.

**Cache note, not a line to memorise.** If you have not fetched again, this repository still holds the forecast from 2026-10-03T20:04:20Z, covering 3–9 October 2026. In that file Oslo's highest day is 17.4 mm on 8 October, and no city day reaches 20 mm. Oslo's card then plans no visits. Coimbra's Live card still lists two baseline sites, C17 and C18. Read whichever card you are showing. If you refresh first, ignore these numbers.

## 3:00–3:40 · Filing, including 10 seconds on the sandbox

**On screen:**

1. Return to Coimbra replay, budget 5, if you left it. The status line names ServiceRequests 1046, 1047, 1048, 1049, and 1050.
2. Click **Download FHIR bundle** only if you want to show the file. Do not upload it. Say it was not sent by the button.
3. At **3:30**, switch to the prepared tab and leave this address visible for about **10 seconds**:

   `https://sandbox.hl7europe.eu/oneaquahealth/fhir/ServiceRequest/1046`

   A normal browser gets an HTML view of the resource. Keep the whole URL readable. Do not click away early.

**Say, before the tab switch:**

The five Coimbra visits were posted once, as draft proposals. C5 is 1046, C12 is 1047, C6 is 1048, C7 is 1049, C20 is 1050. Each note says this is a replay scenario of the real 10 May 2026 storm, for demonstration. The page download only wraps those requests. It does not send them.

**Say, while the sandbox tab is up. Keep it to two sentences so the page stays visible for the full 10 seconds:**

This is ServiceRequest 1046 on the public sandbox. Draft proposal, site C5, dates 11 to 12 May 2026. A filing receipt, not a certification.

If the sandbox page fails to load, say so. Do not substitute a screenshot or describe a resource you cannot see.

## 3:40–4:10 · Difference and limits (about 70 words)

**On screen:** Split the last frames between the Coimbra Why card and the footer, or stay on the sandbox page if the switch would rush the 10 seconds. The footer is the safer background once 1046 has had its full 10 seconds.

**Say:**

Existing tools forecast risk or rank overdue sites from past data. AfterStorm plans the sampling that refreshes the evidence.

The scores are relative categories from 2023 and 2024, not concentrations. The window is a heuristic, not a clearance. Notices stay drafts. The visit order is a simple greedy sort. Nobody has validated this in the field. The FHIR guide has no ServiceRequest profile, so these are base R4 drafts.

## 4:10–4:20 · Close (about 20 words)

**On screen:** The footer line `AfterStorm · From streams to systems.`

**Say:**

From streams to systems. A person approves the visit. The sample is what makes the evidence current.

## Checklist before you upload

- The first frame is Coimbra replay, dated 2026-05-10, with the demonstration line visible.
- The Live segment quotes the card on the screen. It does not depend on a sentence written here.
- ServiceRequest 1046 is on screen for about 10 seconds, URL included.
- Spoken claims stay inside the measured facts: 96 lab records (95 from 2023, 1 from 2024), 106 official sites, 10 without lab results, the five replay dates, and ids 1046–1050.
- Runtime is between 3:30 and 4:30.
