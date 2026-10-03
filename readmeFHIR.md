# Phase 4 — draft FHIR export

Phase 4 adds base FHIR R4 `ServiceRequest` proposals to the sampling plan and
checks their shape in Python. It does not post anything to the public sandbox.

The deadline is **October 5, 2026, 04:00 UTC / 09:30 IST**. Submission text,
the video script, and a public repository are later phases.

## Profile check

On 2026-10-04 the `hl7-eu/oah` master tree contained 61 FSH files under
`input/fsh`. The only `Profile:` declarations are:

- `GroupOah`
- `LibraryOah`
- `LocationOah`
- `ObservationHealthMeasureOah`
- `ObservationIndicatorsOah`
- `ObservationWithCompOah`
- `SpecimenOah`

No line in those files contains `ServiceRequest` or `Task`. AfterStorm therefore
uses base FHIR R4 `ServiceRequest`
(`http://hl7.org/fhir/StructureDefinition/ServiceRequest`). The resources do not
claim an OneAquaHealth profile. This is not sandbox certification. The HL7
validator jar was not downloaded, and sandbox `$validate` was not called.

## What changed, where, and why

1. **`plan.py`: two-decimal category scores, and "tied highest" when the top
   values are equal.** `highest_category_phrase` compares the stored numbers.
   Equal top categories stay in `faecal`, `pathogen`, `antibiotic resistance`
   order. C5 is the real example: faecal and pathogen are both 1, so the reason
   says `faecal and pathogen categories 1.00 (tied highest of 3, relative score)`.
   A single top value still says `highest of 3`. Rain millimetres and sewage
   distance keep their source formatting. `source_health` is not rounded.
   Ranking math is unchanged. Rerunning `python plan.py` rebuilds `plan.json`
   and removes any ServiceRequest fields until `fhir_export.py` runs again.

2. **`web/index.html`: the same scores in the Why card.** Faecal, pathogen, and
   antibiotic-resistance values render with two decimals. When two decimals
   would hide a difference, the source number stays beside them. C5 shows
   `1.00`, `1.00`, and `0.35 (source 0.3465)`. Sewage distance and rain still
   use the source numbers (`2398.28 m`, `24.43 mm` on the C5 replay).

3. **`fhir_export.py`: one draft ServiceRequest per ranked site.** It writes the
   resource onto every site in `ranking`, for every city and both modes, in that
   order. Sites outside the ranking get none. The local category system is
   `urn:afterstorm:assessment-category` (`faecal`, `pathogen`,
   `antibiotic-resistance`). It is not an HL7 or OneAquaHealth code system.
   `ServiceRequest.code` is one CodeableConcept, which is the R4 limit, with one
   coding entry per recommended category. `subject` is an identifier only:
   system `https://api.enora-oah.eu/api/sites`, value = site code. There is no
   `subject.reference` in the saved file. `occurrencePeriod` uses date precision
   and is omitted when the visit has no storm window. `reasonCode.text` is the
   site reason. The note says `precautionary`, the mode, and the sample year
   when a lab date exists; a baseline says `no lab result on file`. A draft
   contact notice is copied into that note. It is not a `Communication`, and it
   is not marked completed or sent.

4. **`web/data/fhir-bundle.json`: the default screen.** Oslo LIVE, budget 5 from
   `config.json`. `Bundle.type` is `transaction`. `Bundle.meta.tag` says
   `mode=live; budget=5; city=OS`. The five entries are O12, O11, O14, O13, O4,
   with `occurrencePeriod` `2026-10-09` to `2026-10-10`. The page link "Saved
   file: Oslo LIVE, budget 5" points at this file.

5. **`web/index.html`: "Download FHIR bundle".** The button slices
   `ranking` to the current budget and wraps the Python-built resources in a
   transaction Bundle. The script does not create resource content. Changing
   Coimbra replay from budget 5 to budget 1 changes the download from
   C5, C12, C6, C7, C20 to C5 alone. Budget 0 disables the button. Benevento
   LIVE has no visits, so the button stays disabled and the empty-state sentence
   remains.

6. **`test_plan.py`: tie wording and structure.** Twenty-one assert checks
   passed, including the C5 tie, a budget slice, a baseline with no window, and
   a corrupted `completed` status or a premature `subject.reference`, both of
   which fail the checker. `--post` is covered only by an in-memory rule: a
   sandbox reference is added only when exactly one Location id matches; two ids
   are logged and neither is chosen. That test does not contact the sandbox.

## Structural checks that ran

`python fhir_export.py` checked the saved plan (58 ranked ServiceRequests across
five cities and both modes; 154 unranked sites have none) and the Oslo LIVE
budget-5 bundle. All 21 passed:

1. Every ranked site has resourceType ServiceRequest — 58 ranked sites
2. Every ServiceRequest status is draft — 58 status fields
3. Every ServiceRequest intent is proposal — 58 intent fields
4. subject.identifier.system is https://api.enora-oah.eu/api/sites — 58 identifiers
5. subject.identifier.value equals the site code — 58 site codes
6. Saved ServiceRequest.subject has no reference field — 58 saved subjects and 5 bundle entries
7. code is one CodeableConcept; coding system is urn:afterstorm:assessment-category; codes and displays match the site categories in order — 58 code elements
8. code.text is a non-empty string — 58 code.text values
9. occurrencePeriod is date-only and matches the site window, or is omitted when the site has no window — 58 windows compared
10. reasonCode has one text entry equal to the site reason — 58 reason texts
11. note contains precautionary, the mode, and the sample year when a sample date exists; baselines say no lab result — 58 notes
12. A draft notice, when present, is copied into the note; no Communication resource exists; every status field is draft — 63 resources walked for status
13. code.text, reasonCode text, and note text do not contain the whole words Good, Moderate, or Poor — 58 resources scanned
14. The export bundle resourceType is Bundle and type is transaction — city=OS mode=live budget=5
15. Bundle.meta.tag states the city, mode, and budget — mode=live; budget=5; city=OS
16. Bundle entry count equals the ranked sites inside the budget — 5 entries
17. Bundle entry order matches ranking order — O12 > O11 > O14 > O13 > O4
18. Each entry is a POST to ServiceRequest and its fullUrl is the site urn:uuid — 5 entries
19. Each entry resource equals the ServiceRequest stored on that ranked site — 5 resources copied, not rebuilt
20. Sites outside the ranking have no ServiceRequest — 154 unranked sites
21. fullUrl values are unique urn:uuid URNs — 58 URNs

Not checked:

- The HL7 validator jar was not downloaded and was not run.
- OneAquaHealth profile conformance was not claimed; the IG has no ServiceRequest or Task profile.
- Sandbox `$validate` was not called and is not certification.
- `--post` was not run. The public sandbox was not modified.

## Run

From `afterstorm/`, Python 3 standard library only:

```text
python test_plan.py
python plan.py
python fhir_export.py
python -m http.server 8765 --bind 127.0.0.1 --directory web
```

Open `http://127.0.0.1:8765/` for Oslo LIVE. Coimbra replay, the C5 tie, is
`http://127.0.0.1:8765/?city=CO&mode=replay&visits=5`.

`python fhir_export.py --post` would POST the default Oslo bundle to
`https://sandbox.hl7europe.eu/oneaquahealth/fhir`. It first looks up
`Location?identifier=https://api.enora-oah.eu/api/sites|{code}`. It adds
`subject.reference` only when that search returns exactly one Location. It does
not use sandbox coordinates for the plan. Do not run it without explicit
approval. It was not run for this phase.

## Page check

Headless Chrome loaded the local page. Coimbra replay showed C5 Mina Hospital
first, with the tied-highest sentence, Why-card values `1.00`, `1.00`, and
`0.35 (source 0.3465)`, sewage `2398.28 m`, and archived rain `24.43 mm`.
Clicking Download FHIR bundle produced a 5-entry draft transaction for
C5, C12, C6, C7, C20 and did not send it. Budget 1 produced C5 only. Oslo LIVE
showed 42.9 mm and five planned visits. Benevento LIVE kept the no-visit
sentence and disabled the button. Desktop (1280) and mobile (390) layouts kept
the existing controls readable; the download control sits in the visit-list header.
