# AfterStorm — Devpost submission text

**Tagline:** From streams to systems: a post-storm reassessment plan that refreshes old stream evidence.

**Primary track:** Track 6 — Resilience Informatics

**Demo URL:** Add after deployment approval.

**Code repository:** Add after public push approval.

**Built with:** Python standard library, static HTML/CSS/JavaScript, Leaflet, OpenStreetMap tiles, Open-Meteo, OneAquaHealth Resilience Map API, HL7 FHIR R4, HL7 Europe OneAquaHealth sandbox, and Geist fonts.

## Why it matters

WHO's 2021 recreational water guidelines recommend warning water users when rain may raise faecal indicators, before a new lab result exists; AfterStorm drafts such a notice for a coordinator to review. [WHO](https://www.who.int/publications/i/item/9789240031302)

Berlin's FLUSSHYGIENE work samples rivers after rain and then runs a forecast model; storm samples like the ones AfterStorm plans are what such a model would need. AfterStorm does not run that forecast. [FLUSSHYGIENE](https://bmbf.nawam-rewam.de/en/projekt/flusshygiene/)

Under the EU Bathing Water Directive, one extra sample confirms that a short-term pollution incident has ended; AfterStorm lets the coordinator plan that confirmation sample. [Directive 2006/7/EC, Annex IV.4](https://eur-lex.europa.eu/eli/dir/2006/7/oj)

## The problem

The public OneAquaHealth Resilience Map has **96 lab records**, 95 from 2023 and one from 2024. The official roster has **106 urban stream sites** across five case-study cities; ten have no lab result in the public feed. Historical relative categories cannot tell a coordinator what is in the water now. A storm forecast creates urgency, but a city still needs to decide which sites to revisit, which categories to reassess, and when, inside a fixed travel budget.

## What AfterStorm does

AfterStorm turns a **20 mm daily rain trigger** into a reviewable post-storm reassessment proposal. The threshold follows the WMO/ETCCDI R20mm precipitation index, but is a prototype setting, not a contamination or warning threshold. LIVE uses the latest saved seven-day city forecast. Archive replay uses a real past day only when **every site** in the city has a valid archived total of at least 20 mm; missing archive dates break a wet run. The Coimbra replay is the real storm on **10 May 2026**.

The plan orders sites by historical faecal, pathogen or antibiotic-resistance categories, then sewage distance, and assigns up to the chosen number of **site visits**. One visit collects samples for every recommended category at that site; the lab team chooses the assays. The proposed sampling window is the **two calendar days after the wet day**. It is explicitly experimental: rain is daily, and in-storm peaks might be missed. Sites without public lab results are offered first-baseline visits. No current health rating or new risk score is invented.

The **Protection check** names draft-notice sites left outside the chosen visit budget and lets a coordinator see the budget required to include them. Every notice stays draft until a person approves it. The coordinator can plan a confirmation sample after the reassessment window; the date never automatically lifts a notice. Approvals are bound to the evidence signature, so a changed site, test, timing or notice asks for review again.

A **citizen task card** in each city's language gives safe bank-side checks: outfalls, sewage smell, animal faeces, sheen, people or pets in water, dead fish or other animals, and unusual colour or algae. It links to the official OneAquaHealth Citizen Science App for the full assessment. These translations are drafts for native-speaker review. Citizen answers provide context but do **not** reorder visits, tests or notices.

## What judges can try

Open the Coimbra replay, budget 5. On **Overview**, read the storm and experimental dates, then press the Protection check to see how C2 and C16 sit outside the budget. On **Plan & map**, see the official map and C5, C12, C6, C7, C20 in order. Open C5's Portuguese Task card, approve a visit, download the Excel-ready **Lab sheet (CSV)**, or export/import review decisions for a colleague. On **Notices**, inspect C16's urban setting and confirmation-sample control. On **Evidence & data**, see the rain chart, all sites, source timestamps and assumptions. The three-step **How it works** guide orients first-time users.

## Technical implementation and proof

`fetch.py` caches the public OneAquaHealth site roster, health risks, urban parameters and weather archive with timestamps and hashes, plus one Open-Meteo forecast per city. `plan.py` runs offline from the cache and writes the plan and draft base FHIR R4 ServiceRequests. The browser only displays and slices Python-built requests. The CSV contains exactly the visits shown, including review state, draft-notice status, confirmation date and any existing sandbox id. Review files are local JSON, checked for size, format and keys on import. Static hosting needs no application server or database.

Five Coimbra replay proposals were filed **once** to the HL7 Europe OneAquaHealth sandbox as **resource shape v1**: [ServiceRequest/1046](https://sandbox.hl7europe.eu/oneaquahealth/fhir/ServiceRequest/1046) through 1050. The current **v2** export places one request-type code in `code` and the assessment categories in `orderDetail`. The official HL7 validator against **core FHIR R4 4.0.1** reported **0 errors, 17 warnings and 8 information** on the five-entry v2 replay bundle (2026-10-04). The messages concern local `urn:afterstorm:*` CodeSystems. The OneAquaHealth IG has no ServiceRequest profile, and its package URL could not be loaded, so no IG conformance is claimed. No v2 bundle was posted.

## Impact and adoption

The immediate output is a concrete trip plan, a lab sheet, and human-reviewed notices. It could help a coordinator refresh old stream evidence and warn people or pet owners while awaiting a new result. The One Health connection is explicit in the source categories and in the card's animal and ecosystem observations. **No health outcome, field benefit or user adoption has yet been measured.**

The first deployment would pilot one city with a coordinator and ecologist who calibrate the 20 mm trigger and 0.5 notice setting. Volunteers could record observations in the official app. Where a city publishes sewer-overflow alerts, those could become another trigger. Over time, measured storm samples could support a forecast model. The prototype itself does not predict contamination.

## Limitations

The lab categories are relative 2023–24 scores, not concentrations. The window is a heuristic, not a validated sampling protocol or safety clearance. The forecast is a cached city-centre forecast with its retrieval time shown. Allocation is greedy. The urban density field is **not a head count**. Reviews and citizen answers are shared by file only. Map tiles need internet. Translations are drafts. There has been **no field validation or user test**.
