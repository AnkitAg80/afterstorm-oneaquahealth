# Round 2, S1 — official Citizen Science App link

## WHAT

Every citizen task card now links to the official OneAquaHealth Citizen Science App and to the project's install guide. The footer says the card only adds the after-storm checks, and that the full stream assessment belongs in the official app. Nothing is sent there.

## WHERE

`web/index.html`, in `citizenCard()` and `citizenPrintArticle()`.

- "Open the OneAquaHealth Citizen Science App" → https://apps.oneaquahealth.eu/
- "How to install it" → https://www.oneaquahealth.eu/citizen-science-project/
- Both use `target="_blank"` and `rel="noopener"`.

## HOW

Feasibility and impact. The card points at the project's own app instead of looking like a second citizen-science product. A login is required there. This page does not log in and does not send observations.

## CHECKS

- `python test_plan.py`: 23 assert-based checks passed.
- Coimbra replay, C5 card: both links have the URLs, `target="_blank"`, and `rel="noopener"`. The footer includes "a login is required" and "this card only adds the after-storm checks."
- The printed C5 card contains the same links and footer.
- Ghent live, G18, has the same app link.
- Loading the page and opening the card did not request `apps.oneaquahealth.eu` or the install guide.
