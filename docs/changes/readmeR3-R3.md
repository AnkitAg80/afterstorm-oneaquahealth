# R3 — Review file hand-off

## What and where

`web/index.html` now offers Export review and Import review below review progress. The implementation moved to `web/app.js` during R5. A JSON file contains only the selected city and mode's reviews, confirmation dates, and citizen card answers.

## Why

Coordinators can pass a review to a colleague without a server. Import keeps the original evidence signatures, so an outdated approval still shows as stale. Files stay on users' devices; the page never uploads them.

## Checks

Approved C5 and held C12, exported `afterstorm-review-CO-replay.json`, cleared reviews, then imported the file. Both decisions returned, and the status announced two imported decisions. The import rejects files above 1 MB, non-JSON names or data, wrong app/format, foreign keys, invalid decisions/dates/answers, and oversized free text.
