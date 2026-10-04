# Devpost text — AfterStorm

Paste-ready submission text for the OneAquaHealth IEEE Global Hackathon 2026. Do not submit this file until publishing is approved.

**Project name:** AfterStorm

**Tagline:** From streams to systems: the sampling plan that refreshes stale stream evidence.

**Primary track:** Track 6 — Resilience Informatics

**Built with:** Python 3 standard library, one static HTML page, Leaflet with OpenStreetMap tiles, the public OneAquaHealth roster and Resilience Map, Open-Meteo, base FHIR R4 ServiceRequest on the HL7 Europe OneAquaHealth sandbox.

## Track alignment

Track 6 asks for early warning and resilience planning through "predictive dashboards, alerts, and resilience tools". AfterStorm addresses it in three ways:

- **Early warning:** a heavy-rain forecast triggers a sampling plan before the storm arrives.
- **Alerts:** draft contact notices, which a coordinator issues or holds.
- **Resilience planning:** a limited visit budget is spent where stale evidence matters most.

It doesn't predict contamination. It plans the evidence that would show it. A small Track 7 element, draft FHIR R4 ServiceRequests filed to the HL7 Europe OneAquaHealth sandbox, lets the plan move into health systems.

## Expected impact on ecosystem and human health

- **Monitoring:** the 2023–24 lab evidence gets refreshed at the moments it most likely matters, just after heavy rain, rather than at random times.
- **Human and animal health:** the categories it plans (faecal contamination, pathogens, antibiotic-resistance genes) are where stream health meets the health of people and pets. Draft notices give coordinators a ready, reviewable warning for sites with high historical faecal or pathogen scores.
- **Ecosystem and city resilience:** with a fixed visit budget, a team gets more useful evidence per trip. The plan works for any city on the OneAquaHealth roster with no new hardware or model.

## About the project

Ninety-six lab records sit on the public Resilience Map. Ninety-five are from 2023. One is from 2024. The official roster has 106 stream sites, and 10 of them have no lab result at all.

Heavy rain still carries street runoff and sewer overflows into those streams. A coordinator has a small number of site visits and needs a concrete plan: which stream, which old category to assess again, and which days. AfterStorm writes that plan. It does not score today's water and it does not send an alert by itself.

## The problem

The latest public lab evidence for almost every site is from 2023. Waiting for the next heavy-rain day and then guessing which site to revisit wastes the few visits a team can make. Forecasting a risk number does not produce the sample. Ranking sites only because their records are old does not say which category to take, or on which dates after the rain.

People and animals meet these streams. The categories already in the data are faecal contamination, pathogens, and antibiotic resistance. A new sample is what makes those categories current again. A contact warning, if one is warranted, has to be a human decision.

## What it does

AfterStorm is one page for a coordinator.

- Choose a city among Benevento, Coimbra, Ghent, Oslo, and Toulouse.
- **Live** shows the cached 7-day city-centre forecast.
- **Replay** shows a real archived heavy-rain day, labelled with the date. In this cache those days are Benevento 2026-04-01, Coimbra 2026-05-10, Ghent 2025-07-06, Oslo 2026-06-09, and Toulouse 2026-08-03.
- A storm day means at least 20 mm of rain in a day, the WMO/ETCCDI "very heavy precipitation day" index (R20mm). It is a prototype setting, not a regulatory limit: the rain data are daily totals, so hourly intensity can't be checked, and each city should calibrate it locally.
- The page lists up to five site visits. Each visit names the categories to assess and an experimental window: the two calendar days after the heavy-rain day. The window is marked heuristic, not validated.
- Sites with no lab result are offered a first baseline sample of all three categories.
- Where a 2023 or 2024 faecal or pathogen category is at least 0.5, the page drafts a water-contact notice for people and pets. The coordinator decides whether to issue it.
- Download produces a FHIR transaction of draft ServiceRequests for the visits on screen. The page does not build those resources. Python did.

The demonstration filing is the Coimbra replay, budget 5. It was posted once. The sandbox ids are ServiceRequest 1046 (C5), 1047 (C12), 1048 (C6), 1049 (C7), and 1050 (C20). Each note, and the bundle tag, says `replay scenario of the real 2026-05-10 storm — demonstration`.

## How we built it

Python's standard library fetches and caches the official site roster, the health-risk feed, urban parameters, a weather archive per site, and one Open-Meteo forecast per city centre. `plan.py` turns that cache into `plan.json` with no network call. `fhir_export.py` attaches one draft ServiceRequest per ranked visit and writes the bundle. The page is one HTML file with a local copy of Leaflet. Map tiles come from OpenStreetMap and need internet. The pins and the plan still load from the saved files if the tiles do not.

The OneAquaHealth FHIR guide has no ServiceRequest profile. The resources are base FHIR R4. They were checked with 22 structural tests in Python. They were not passed through the HL7 validator jar and they were not certified by the sandbox.

## Challenges

The lab values are scaled categories, not concentrations, and almost all of them are from 2023. Using them as today's water quality would be false, so the plan calls them historical evidence and asks for a new sample.

Daily rain totals do not record the hour the rain stopped, so the sampling window uses dates only and says the rain-stop time is unknown.

The public sandbox already contained duplicate Locations for some site codes. A reference is added only when a search returns exactly one Location. The saved plan keeps the official site identifier either way, and sandbox coordinates never enter the ranking.

## Accomplishments

- A visit plan for 106 official sites, grounded in 96 real lab records and real archived rain.
- An honest live mode: the page shows the cached forecast, including a week with no day at or above 20 mm.
- Draft notices that cannot mark themselves sent.
- Five filed draft proposals, ServiceRequests 1046–1050, readable on the sandbox, each labelled as a demonstration of the 2026-05-10 Coimbra replay.

## What we learned

The per-site decision cannot come from the weather alone. Inside one city the forecast is a single city-centre number, and the lab dates are nearly the same. The category profile and the sewage distance are what separate one stream from the next. Where sewage distance is missing, the site stays last among baselines instead of being treated as zero metres away.

## What's next

A coordinator's sign-off before any request leaves draft. A field check of whether the two-day window actually catches the sample worth taking. A ranking that can use new lab results when they exist, instead of the greedy sort on 2023 scores. No new risk model is planned.

## How this differs

Existing tools forecast risk or rank overdue sites from past data. AfterStorm plans the sampling that refreshes the evidence: which site, which category, which experimental dates, inside a visit budget, filed as a draft a person approves.

## Who it helps

Coordinators get the list. Lab teams get the category and the dates, and they choose the assay. The draft notice is the link to people and pets, and it moves only when a person sends it.

## Limitations, in short

Relative 2023–24 scores, not concentrations. An experimental window, not a safety clearance. Categories, not assays. Draft notices. Greedy allocation. Replay is history. Live is this week's cached forecast and will change when the forecast is fetched again. No field validation yet.
