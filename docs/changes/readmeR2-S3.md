# Round 2, S3 — repository hygiene

## WHAT

The code now has an MIT licence. Change notes live in `docs/changes/`. `readmePRIORITY.md` is gone from the branch and from the unpublished history. A copy remains outside the repository at `C:\Users\ankit\Downloads\oneaqua\_internal\readmePRIORITY.md`.

## WHERE

- `LICENSE` at the repository root. Copyright 2026, AfterStorm contributors.
- `README.md`, section "Licences and data".
- `docs/changes/` and `docs/changes/INDEX.md`.
- `README.md`, `docs/changes/readmeR2-1.md`, and the page error in `web/index.html` now point at `docs/changes/`.

## HOW

Technical quality and feasibility. A public repository can say what may be reused, and the first page of the tree is the submission README rather than a stack of working notes. The internal critique is not in the history a judge would clone.

## CHECKS

- The copy outside the repository has the same SHA-256 as the file that was in the tree: `eccab9c370bbe5030337ef6fcf0b84247c866e76ee7ca075a15a00631b760c48`.
- `git filter-branch` rewrote `phase-1-data`. The backup refs under `refs/original` were deleted afterwards, because they still pointed at the old history. `git log --all -- readmePRIORITY.md` is empty. The commit count is still 14. The only path removed from the tree is `readmePRIORITY.md`.
- `git ls-files` does not list `.superpowers/`, `__pycache__/`, or `_shots/`.
- `python test_fetch.py`: 14 tests, OK. `python test_plan.py`: 23 assert-based checks passed.
