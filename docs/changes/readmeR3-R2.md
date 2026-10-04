# R2 — lab sheet CSV

## WHAT

The Plan & map page downloads a lab sheet with one row per planned site visit, in the displayed rank order. It includes the site, categories, stored relative scores, proposed dates, local review state, draft notice status, confirmation date, sewage distance and any matching filed ServiceRequest. A second button in the header provides the same download. The file is UTF-8 with a BOM, quotes every field and uses CRLF lines for Excel.

## WHERE

- `web/index.html`: visit-panel and header buttons, `labSheetRows()`, `labSheetCsv()` and `downloadLabSheet()`. The header button has an outline style to distinguish it from FHIR download.
- `docs/validation/lab-sheet-coimbra-replay.csv`: actual browser download of Coimbra replay at budget 5, before any review choice.
- `test_labsheet.py`: parses that saved file and checks encoding, line endings, header, row order, scores, dates, the filed C5 reference and an accented site name.
- `fhir_export.py`: corrected an R1 console sentence that still said the official validator jar had not been downloaded. It now points to the separate R1 validation report; no resource content changed.

## HOW IT HELPS

A coordinator can give a ranked list to a lab immediately as a spreadsheet. Held visits remain visible with their review state, so the lab can distinguish a hold from a deleted visit. The sheet copies existing plan and browser review fields; it adds no environmental calculation.

## CHECKS

- `python test_labsheet.py`: passed. The saved download has 6 lines (header plus C5, C12, C6, C7, C20), the required columns, C5's two 1.00 stored scores, ServiceRequest/1046 (shape v1), UTF-8 BOM and CRLF endings.
- Browser download after holding C12: all five rows remained; only C12's `review` cell changed from `not reviewed` to `on hold`. The hold was cleared afterwards.
- Budget 8 browser download: the UTF-8 BOM file contains `Estação Cbr-B` and `São Romão` intact. This checks the bytes and Python CSV decoding; the file was not opened in Excel.
- `python test_plan.py`: 24 assert-based checks passed. `python test_fetch.py`: 14 tests passed.
- `python plan.py`: exit 0, Coimbra replay anchor remained 2026-05-10 and the top five remained C5, C12, C6, C7, C20. Generated plan and default bundle bytes were restored after the check because their only change was generation time.
- All ten city × mode views loaded. The four pages and both `#card-C5` and `#notice-C16` deep links loaded. No local application console errors were reported.
- Headless Chrome captured `C:\Users\ankit\Downloads\oneaqua\_shots\r3-R2-plan.png` using an absolute output path. The Plan page visibly shows both CSV buttons.
- No sandbox POST or outward publication was performed.
