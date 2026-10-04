# Part 7 — publication preparation

## What changed

Added a GitHub Pages Actions workflow to publish the existing static demo from `web/` when `main` is pushed. The workflow is prepared locally; no repository or Pages site has been created by this change.

## Where

`.github/workflows/pages.yml` checks out the commit, packages `web/`, and deploys the artifact to the `github-pages` environment. The entry point stays `web/index.html`; its scripts, styles, fonts, and saved plan use relative paths that work under a project Pages URL.

## How it helps

A direct public demo lets judges try the same committed data, protections and hand-offs shown in the video. Publishing `web/` with Actions avoids a duplicated copy that could drift from the tested prototype. This supports technical implementation and feasibility.

## Checks

- The workflow uses the GitHub-documented `configure-pages@v5`, `upload-pages-artifact@v4`, and `deploy-pages@v4` sequence.
- `python test_fetch.py`: 14 passed; `python test_plan.py`: 24 passed; `python test_labsheet.py`: passed; `node --check web/app.js`: passed.
- Loading `http://127.0.0.1:8765/` opened Coimbra replay, anchored on 2026-05-10, with five proposed visits. The animated rain number settled on 24.43–24.6 mm; the underlying saved values agree.
- Live Pages checks remain for after deployment.
