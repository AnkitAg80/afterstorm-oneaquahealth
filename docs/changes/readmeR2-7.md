# Part 7 — publication preparation

## What changed

Added a GitHub Pages Actions workflow to publish the existing static demo from `web/` when `main` is pushed. GitHub Pages is enabled with Actions as its source, and the public demo is live at https://ankitag80.github.io/afterstorm-oneaquahealth/.

## Where

`.github/workflows/pages.yml` checks out the commit, packages `web/`, and deploys the artifact to the `github-pages` environment. The entry point stays `web/index.html`; its scripts, styles, fonts, and saved plan use relative paths that work under a project Pages URL.

## How it helps

A direct public demo lets judges try the same committed data, protections and hand-offs shown in the video. Publishing `web/` with Actions avoids a duplicated copy that could drift from the tested prototype. This supports technical implementation and feasibility.

## Checks

- The workflow uses the GitHub-documented `configure-pages@v5`, `upload-pages-artifact@v4`, and `deploy-pages@v4` sequence.
- `python test_fetch.py`: 14 passed; `python test_plan.py`: 24 passed; `python test_labsheet.py`: passed; `node --check web/app.js`: passed.
- Loading `http://127.0.0.1:8765/` opened Coimbra replay, anchored on 2026-05-10, with five proposed visits. The animated rain number settled on 24.43–24.6 mm; the underlying saved values agree.
- The published default URL opens the Coimbra replay; the `?guide=0` deep link opens the replay without the introduction overlay; the Oslo LIVE link displays the latest saved forecast and explains why it proposes zero visits. The published plan route shows the official-site map and five ranked Coimbra visits.
- The first Tests run exposed a CRLF-sensitive lab-sheet fixture in Git's index. `.gitattributes` now preserves that fixture's bytes across checkout; the next Tests and Pages runs both passed on commit `77bd4dd`.
