# Round 2, Part 2 — protection check

## WHAT

A protection card names what the current visit budget leaves out for people-and-pets notices. It uses stored site values only. It does not re-rank, does not change the budget by itself, and does not use a percentage.

## WHERE

`web/index.html`

- A `#protection` section in `.right-column`, above `#visit-panel`.
- `renderProtection(plan, allocated)`, called from `render()` after `renderVisits`.
- A click on `[data-cover-notices]` calls `applyBudget` and then writes the change into `#plan-status`.

## HOW

Impact and innovation. On Coimbra replay at budget 5, the card says C2 (faecal 0.51, sewage works 762 m) and C16 (pathogen 0.51, sewage works 572 m) have draft notices outside the budget, visit 5 (C20) reassesses antibiotic resistance and drafts no notice, and C19 faecal 0.46 sits just under the 0.5 prototype setting. The button offers 8 visits, which is the lowest budget that reaches every notice site, because C16 is rank 8. The filed order stays C5, C12, C6, C7, C20.

## CHECKS

- `python test_fetch.py`: 14 tests, OK.
- `python test_plan.py`: 22 assert-based checks passed. The structural report inside that run is still 24 passes.
- `python plan.py`: exit 0, 24 structural passes, Coimbra anchor still 2026-05-10, allocated order still C5, C12, C6, C7, C20. The rebuild changed only `generated_at` and `built_at`. Those two timestamps were restored so this part does not rewrite the plan.
- All 10 city × mode views rendered with no console error. Tile HTTP 429 was ignored.
- Coimbra replay, budget 5, shows the sentences above, including "Show a budget that covers every notice site (8 visits)".
- Clicking that button sets the URL to `visits=8`, shows 8 visit cards and 8 numbered pins, and `#plan-status` says the budget now covers every notice site and the order is unchanged. Filed lines remain only on C5, C12, C6, C7, and C20 (ServiceRequests 1046–1050).
- Setting the budget input back to 5 restores 5 cards and the original outside-budget sentences.
- Toulouse replay lists T12, T10, and T13 as visits with no notice, and T14, T11, T1, T4, and T6 outside the budget. The button says 13 visits, which is the largest notice rank.
- Screenshots: `C:\Users\ankit\Downloads\oneaqua\_shots\r2-2.png` and `r2-2-mobile.png`. On a 390-wide screen the card stacks above the visit list, with the amber left edge and the amber button.
