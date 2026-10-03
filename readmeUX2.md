# UX Part 2 — Decision header

Scope: `web/index.html` only. The planner, the data and the FHIR resources are unchanged.

## 1. A one-sentence answer at the top

**What changed:** a new "Your plan at a glance" card sits under the controls (and under the replay banner when replay is on). It answers in one plain sentence, with the key facts in bold:

| Situation | Example |
|---|---|
| Storm (replay) | "Replay: heavy rain hit **Coimbra** on **10 May 2026**. Sample **5 streams** on **11 May – 12 May**. **6 contact notices** need your review." |
| Storm (live) | "Heavy rain is forecast for **Oslo** on **8 Oct 2026**. Sample …" |
| No storm, unsampled streams exist | "No storm is forecast for **Coimbra** this week. Use the quiet week to take **2 first samples** at streams that have never been tested." |
| No storm, nothing to do | "… Every stream already has a lab result, so there's nothing to do now. Check again after the next forecast update." |
| Budget 0 | "… Your visit budget is 0, so no visits are planned." |
| Storm plan that includes first samples | "… Sample 5 streams on 7 Jul – 8 Jul (including 4 first samples)." |

**Where:** a new `#decision` section in the HTML; a new `renderDecision()` function, called from `render()`. It uses only fields already in `plan.json`.

**How it helps:** a coordinator, or a judge, gets the decision in five seconds, without reading four cards.

## 2. A clickable progress strip: Storm → Plan visits → Review & file

**What changed:** three step cards under the answer. Each one shows a state (done ✓, current, or still to do) and a short status:
- Storm: "Past storm · 10 May", "Forecast · 8 Oct", "No storm this week"
- Plan visits: "5 of 5 visits used", "Nothing to plan"
- Review & file: "6 notices to review", "Download draft FHIR", "Nothing to file"

Clicking a step scrolls to that section (rain card, visit list, or notices panel), moves keyboard focus there, and briefly flashes a blue outline. With reduced motion turned on, it jumps and shows a static outline. The current step is marked `aria-current="step"` for screen readers.

**Where:** `renderDecision()`, `jumpTo()`, and one delegated click listener in `start()`. The jump targets got `id` and `tabindex="-1"`: `#weather`, `#visit-panel`, `#notice-panel`. New `.decision`, `.steps`, `.step`, `.flash` styles. On phones the steps stack vertically.

**How it helps:** the workflow is visible and can be navigated in one click. It also sets up Part 4, where "Review & file" gets real Approve/Hold actions.

## Checks run

- All 10 city and mode views produce a correct sentence and step states, with no console errors. Examples:
  - Benevento live: "nothing to do".
  - Ghent replay: "including 4 first samples".
  - Toulouse replay: "7 contact notices".
- Setting the budget to 0 shows the zero-budget sentence.
- The "Review & file" step jumps to and focuses `#notice-panel`, with the flash.
- At 375 px phone width, the page measures 375 px with no horizontal overflow. The roster table scrolls inside its own box, as before.
