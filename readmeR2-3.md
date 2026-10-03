# Round 2, Part 3 — urban setting on each notice

## WHAT

Each site now carries four stored surroundings from the urban-parameters file: distance to a hospital, the human-density proxy within 100 m, impervious surface within 100 m, and vegetation cover within 100 m. A missing or non-numeric value stays `None`. The notice shows those values. They do not change rank, eligibility, or the notice itself.

## WHERE

- `plan.py`: `URBAN_SETTING_FIELDS`, `urban_setting()`, and the `urban_setting` field on every row in `city_plan()`. `provenance.urban_setting` reuses `source_ref("urban-parameters.json", sources)`.
- `test_plan.py`: `test_urban_setting_is_carried_but_never_reorders`.
- `web/index.html`: `settingRows()` and `renderNotices()`. The compact line sits under the notice head. The titled block sits inside "Read the draft notice".

## HOW

Impact and technical use of a data source already in the cache. C16 shows a hospital at 2,014 m, 37.92 % impervious surface, `vegCoverFrac100m` 6.54, and `humanDensityProxy100m` 0, labeled as a relative proxy rather than a head count. Coimbra replay is still C5, C12, C6, C7, C20.

## CHECKS

- `python test_plan.py`: 23 assert-based checks passed, including the new one. C5 is 854.59 m, 9.05, 47.77, and 0.1. Removing the four keys from every urban record leaves every city and mode ranking identical. A site with no urban record gets all four as `None`.
- `python test_fetch.py`: 14 tests, OK.
- `python plan.py`: exit 0. Structural checks still 24 passes. Anchor still 2026-05-10. Allocated order still C5, C12, C6, C7, C20. `filed.json` and the Coimbra replay bundle were not rewritten.
- All 10 city × mode views rendered with no console error. Visit order was unchanged, including Coimbra replay C5 through C20 and Toulouse live T15, T21, T24.
- Coimbra replay notice C16 shows hospital 2,014 m, impervious 37.92 %, `vegCoverFrac100m` 6.54, and density proxy 0, plus the sentence that these values do not change the visit order or the notice.
- Screenshots: `C:\Users\ankit\Downloads\oneaqua\_shots\r2-3.png` and `r2-3-mobile.png`. On a 390-wide screen the setting lines wrap inside the notice card.
