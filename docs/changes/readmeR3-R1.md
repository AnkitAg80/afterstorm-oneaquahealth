# R1 — official FHIR validation

## WHAT

The current v2 Coimbra replay bundle, the same five sites as the filed set, was checked with the official HL7 FHIR validator, version 6.10.4, against core R4 4.0.1. The result is 0 errors, 17 warnings, and 8 information messages. Every message is an unknown local code system. The OneAquaHealth IG package did not load.

## WHERE

- `fhir_export.py`: `--write-validation-bundle` writes `web/data/fhir-bundle-v2-coimbra-replay.json` through `bundle_for(plan, "CO", "replay", 5)`. It does not post, and it does not rewrite `filed.json` or `fhir-bundle-coimbra-replay.json`.
- `test_plan.py`: `test_v2_validation_bundle_is_the_coimbra_replay_five`.
- `docs/validation/fhir-r4-core.html` and `docs/validation/fhir-r4-core.txt`.
- `docs/validation/fhir-oah-ig.txt`.
- The jar is outside the repo: `C:\Users\ankit\Downloads\oneaqua\_tools\validator_cli.jar` (200,928,617 bytes).

## HOW

Technical credibility. The v2 shape was run through the official validator instead of only the local structural checks. The unknown `urn:afterstorm:*` systems are recorded and left in place. This is not a claim of OneAquaHealth profile conformance. The IG has no ServiceRequest profile, and its package did not load.

## CHECKS

- Validator command: `java -jar validator_cli.jar web\data\fhir-bundle-v2-coimbra-replay.json -version 4.0.1`. Exit 0. Java 24.0.2. FHIR Validation tool 6.10.4, built 2026-09-04.
- Counted from the generated OperationOutcome (saved with the brief's `.html` filename): 0 errors, 17 warnings, 8 information. All 25 messages concern undefined local `urn:afterstorm:*` CodeSystems. No genuine error was fixed because none was reported. The final refreshed bundle was revalidated with the same counts.
- IG command added `-ig https://build.fhir.org/ig/hl7-eu/oah/package.tgz`. Exit 1. Exact error: `java.io.IOException: 404 Not Found`, caused by `Invalid HTTP response 404 from https://build.fhir.org/ig/hl7-eu/oah/package.tgz`. The package did not load, so no IG issue counts exist. This run only attempted to load the package. It did not check a ServiceRequest profile.
- `python test_plan.py`: 24 assert-based checks passed, including the new bundle test. The five entries are C5, C12, C6, C7, C20, each POST, draft, proposal, one request-type coding, and one orderDetail per category.
- `python test_fetch.py`: 14 tests, OK.
- `python plan.py`: exit 0. It changed only `generated_at` and `built_at`. Those timestamps were restored.
- `filed.json` and `fhir-bundle-coimbra-replay.json` kept their previous SHA-256 values. Nothing was posted.
- All 10 city × mode views, `#/`, `#/plan`, `#/notices`, `#/evidence`, `#card-C5`, and `#notice-C16` rendered with no application console error. Tile HTTP 429 was ignored.
