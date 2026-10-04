# Phase 4 — draft FHIR export

Phase 4 adds base FHIR R4 `ServiceRequest` proposals to the sampling plan and
checks their shape in Python. `python plan.py` writes both `web/data/plan.json`
and the default Oslo LIVE bundle.

One sandbox write was approved and completed: the Coimbra REPLAY budget-5
bundle. The Oslo LIVE bundle was not posted. This is not sandbox certification.

The deadline is **October 5, 2026, 04:00 UTC / 09:30 IST**. The Phase 5 video
script is not written here. When it is written, it must open on Coimbra REPLAY,
then show LIVE honestly reporting no storm.

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
claim an OneAquaHealth profile. The HL7 validator jar was not downloaded, and
sandbox `$validate` was not called.

## What changed, where, and why

1. **`plan.py` calls `fhir_export.write_export` at the end.** One command
   rebuilds the visit plan, stores a draft ServiceRequest on every ranked site,
   runs the structural checks, and writes `web/data/plan.json` plus
   `web/data/fhir-bundle.json`. The default bundle is always Oslo LIVE at the
   configured budget of 5. Tied scores still say `tied highest` to two decimals.
   C5 remains the real example: faecal and pathogen are both 1.

2. **`fhir_export.py`: the demonstration sentence is added only for Coimbra
   replay while the archive anchor is `2026-05-10`.** The exact sentence is
   `replay scenario of the real 2026-05-10 storm — demonstration`. It is appended
   to each Coimbra-replay note and added as `Bundle.meta.tag`. Other cities and
   LIVE notes do not carry it. `plan.fhir.demonstration` lets the page copy that
   tag into a download. `--post` refuses every target except
   `--city CO --mode replay --budget 5`, and it refuses again when
   `web/data/filed.json` already lists resources. The saved default bundle is
   not replaced by the posted payload.

3. **`web/data/fhir-bundle.json`: Oslo LIVE, and it is empty.** After the
   forecast refresh, Oslo has no day at or above 20 mm and every Oslo site
   already has a lab result, so the ranking is empty. The file is a transaction
   Bundle with 0 entries. Its tag says `mode=live; budget=5; city=OS`. It was
   not posted.

4. **`web/data/fhir-bundle-coimbra-replay.json`: the payload that was posted,
   saved before any sandbox Location reference was added.** Five entries, in
   ranking order: C5, C12, C6, C7, C20. `subject` in this file is identifier
   only. The tag list includes the demonstration sentence.

5. **`web/data/filed.json` and the page.** The returned ids are below. Coimbra
   replay shows `Filed as FHIR ServiceRequest/{id}` on each of those five visit
   cards and repeats the ids in the FHIR status line. LIVE screens do not show
   those ids. The download button still only slices and wraps the Python
   resources. It does not build them and it does not send them.

6. **`python fetch.py` on 2026-10-03 20:04 UTC.** 114 live responses. Roster
   106, lab records 96, coordinates 106. The same 10 sites still have no lab
   result. No city forecast day from 3 Oct through 9 Oct reaches 20 mm:

   | City | Highest day | mm |
   | --- | --- | --- |
   | Benevento | 2026-10-08 | 17.1 |
   | Coimbra | 2026-10-06 | 4.3 |
   | Ghent | 2026-10-08 | 18.0 |
   | Oslo | 2026-10-08 | 17.4 |
   | Toulouse | 2026-10-07 | 9.3 |

   Oslo’s 8 Oct total is 17.4 mm, down from the earlier cached 42.9 mm. LIVE
   for every city says no storm. Oslo and Benevento plan no visits. Coimbra,
   Ghent, and Toulouse still list first-baseline visits for sites with no lab
   result. Those baseline visits are not storm visits.

## Sandbox resources

Posted once at `2026-10-03T20:05:07Z` to
`https://sandbox.hl7europe.eu/oneaquahealth/fhir`. HTTP 200. Each entry was
`201 Created`. A second `--post` of the same command stopped before any network
call because `filed.json` already had resources.

| Site | ServiceRequest id | Location header |
| --- | --- | --- |
| C5 | 1046 | `ServiceRequest/1046/_history/1` |
| C12 | 1047 | `ServiceRequest/1047/_history/1` |
| C6 | 1048 | `ServiceRequest/1048/_history/1` |
| C7 | 1049 | `ServiceRequest/1049/_history/1` |
| C20 | 1050 | `ServiceRequest/1050/_history/1` |

The search before that post found exactly one sandbox Location per site
(C5 `892`, C12 `899`, C6 `893`, C7 `894`, C20 `907`). Those references were
added only on the copy sent to the sandbox. The saved bundle and `plan.json`
still have no `subject.reference`. Sandbox coordinates were not used for the
plan. Returned ids are sandbox assignments, not certification.

## Structural checks that ran

`python plan.py` checked the refreshed plan: 53 ranked ServiceRequests across
five cities and both modes, 159 unranked sites with none, and the empty Oslo
LIVE budget-5 bundle. The Coimbra replay budget-5 bundle was checked again
immediately before the post. All 22 passed both times:

1. Every ranked site has resourceType ServiceRequest — 53 ranked sites
2. Every ServiceRequest status is draft — 53 status fields
3. Every ServiceRequest intent is proposal — 53 intent fields
4. subject.identifier.system is https://api.enora-oah.eu/api/sites — 53 identifiers
5. subject.identifier.value equals the site code — 53 site codes
6. Saved ServiceRequest.subject has no reference field — 53 saved subjects; 0 entries in the Oslo bundle, 5 in the Coimbra bundle
7. code is one CodeableConcept; coding system is urn:afterstorm:assessment-category; codes and displays match the site categories in order — 53 code elements
8. code.text is a non-empty string — 53 code.text values
9. occurrencePeriod is date-only and matches the site window, or is omitted when the site has no window — 53 windows compared
10. reasonCode has one text entry equal to the site reason — 53 reason texts
11. note contains precautionary, the mode, and the sample year when a sample date exists; baselines say no lab result — 53 notes
12. A draft notice, when present, is copied into the note; no Communication resource exists; every status field is draft
13. code.text, reasonCode text, and note text do not contain the whole words Good, Moderate, or Poor — 53 resources scanned
14. The export bundle resourceType is Bundle and type is transaction
15. Bundle.meta.tag states the city, mode, and budget
16. Bundle entry count equals the ranked sites inside the budget — 0 for Oslo LIVE, 5 for Coimbra replay
17. Bundle entry order matches ranking order — Oslo is an empty slice; Coimbra is C5 > C12 > C6 > C7 > C20
18. Each entry is a POST to ServiceRequest and its fullUrl is the site urn:uuid
19. Each entry resource equals the ServiceRequest stored on that ranked site
20. Sites outside the ranking have no ServiceRequest — 159 unranked sites
21. fullUrl values are unique urn:uuid URNs — 53 URNs
22. The demonstration sentence appears only on the Coimbra replay of 2026-05-10, in each ranked note and as a bundle tag

Not checked:

- The HL7 validator jar was not downloaded and was not run.
- OneAquaHealth profile conformance was not claimed; the IG has no ServiceRequest or Task profile.
- Sandbox `$validate` was not called and is not certification.

`python test_plan.py` passed 22 assert-based checks after the refresh. Those
checks compare each city’s LIVE storm flag with its forecast file. They do not
hard-code 17.4 mm. Oslo with no storm must allocate no visits.

## Run

From `afterstorm/`, Python 3 standard library only:

```text
python test_plan.py
python fetch.py
python plan.py
python -m http.server 8765 --bind 127.0.0.1 --directory web
```

`python plan.py` alone writes the plan and the Oslo LIVE bundle. Open
`http://127.0.0.1:8765/` for Oslo LIVE, which currently reports no storm.
Coimbra replay is `http://127.0.0.1:8765/?city=CO&mode=replay&visits=5`.

`python fhir_export.py --city CO --mode replay --budget 5 --post` is the only
command that posts, and it now refuses because `web/data/filed.json` already
records the five resources. Any other city, mode, or budget is refused before
the sandbox is contacted. Do not post the Oslo bundle.

## Page check

Headless Chrome loaded the local page on a 1280-wide desktop viewport and a
390-wide mobile viewport. Coimbra replay showed the demonstration sentence, the
five visit cards, and ServiceRequest ids 1046, 1047, 1048, 1049, and 1050.
Clicking Download FHIR bundle saved a local file with those five draft
resources, the demonstration tag, and no `subject.reference`. It was not sent.

Oslo LIVE, on both viewports, showed “No storm”, the sentence “No storm in the
cached 7-day forecast; no storm sampling needed.”, 17.4 mm on 8 Oct under the
20 mm line, zero visits, and a disabled download button. Benevento LIVE also
had no visits. Coimbra, Ghent, and Toulouse LIVE said no storm and still listed
their baseline visits. Those LIVE screens did not show the Coimbra resource ids.

## Resource shape v1 (filed) vs v2 (current)

ServiceRequests 1046–1050 were filed on 2026-10-03 with resource shape v1.
In that shape, `ServiceRequest.code` held several codings, one per category
(faecal, pathogen, antibiotic resistance). FHIR treats codings inside one
CodeableConcept as equivalent representations of the same concept, so a list
of different categories does not belong there.

The current export uses resource shape v2. `code` is one request type:
`post-storm-reassessment` or `first-baseline-assessment`, from
`urn:afterstorm:request-type`. Each category is its own `orderDetail`
CodeableConcept, still from `urn:afterstorm:assessment-category`, in the
site's category order. Every new resource carries
`meta.tag` code `resource-shape-v2`.

`web/data/filed.json` and `web/data/fhir-bundle-coimbra-replay.json` were not
rewritten and were not posted again. The page labels 1046–1050 as filed with
resource shape v1. A download from the current page uses the v2 resources
built by `plan.py`. The `urn:uuid` fullUrls are unchanged.

## Validation of the current export

On 2026-10-04, the official HL7 validator checked `web/data/fhir-bundle-v2-coimbra-replay.json` against core FHIR R4 4.0.1. It reported **0 errors, 17 warnings and 8 information**. Every warning/information item concerns an undefined local `urn:afterstorm:*` CodeSystem; the local codes have not been published as formal terminology resources. The report is in `docs/validation/fhir-r4-core.html` and the console summary in `docs/validation/fhir-r4-core.txt`. The OneAquaHealth IG package URL returned 404, so this is **not** an IG conformance result. The IG has no ServiceRequest profile. The v2 bundle was never posted to the sandbox.

The current page also downloads a UTF-8 BOM lab sheet CSV and local review JSON. These files are hand-offs, not FHIR transmissions. The five filed IDs remain the earlier shape v1 examples.
