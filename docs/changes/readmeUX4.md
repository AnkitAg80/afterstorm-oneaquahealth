# UX Part 4 — Review workflow, plus background design

Scope: `web/index.html` only. The planner, the data and the FHIR resources are unchanged. The ServiceRequests stay `status: draft`, `intent: proposal`.

## 1. Approve / Hold on every visit and every notice

**What changed**
- Each visit card has **✓ Approve** and **Hold** buttons. Each draft notice has **✓ Approve to issue** and **Hold**.
- Clicking the active choice again clears it.
- Approved visits get a filled rank badge and a pin with a light border. Held visits fade, on the list and on the map.
- Each notice row shows its state ("Draft — needs review", "Approved to issue · not sent", "On hold"). The notice text sits behind "Read the draft notice".

**Where:** new `reviewOf`, `reviewButtons`, `setReview`, `reviewTally` and `renderReview` functions; changes to `renderVisits` and `renderNotices`; one delegated click listener.

**How it helps:** the human-in-the-loop step is something the coordinator actually does, not just text on the page.

## 2. Honest storage: this browser only

**What changed**
- Choices are kept in `localStorage` (`afterstorm-review-v1`), keyed by city, mode, item type and site.
- The progress panel says: "Your choices are saved in this browser only. Nothing is sent anywhere."
- "Clear my review" resets the current city and mode.
- Each change is announced to screen readers ("C2 notice: approved. Saved in this browser only.").
- Focus stays on the button you pressed, and any open "Why this site?" or notice text stays open.

## 3. Review progress tied to the steps

**What changed**
- A progress bar above the visits: "3 of 11 reviewed · 2 approved · 1 on hold".
- Step 3 of the decision strip now shows "3 of 11 reviewed", turns ✓ when everything is reviewed ("All 11 reviewed · ready to download"), and jumps to the progress bar.

## 4. Held visits are left out of the download

**What changed**
- The button reads "Download FHIR (4)".
- The status says "Downloads 4 visits as draft FHIR requests (1 on hold left out). Nothing is sent."
- The page still only selects which Python-built resources go in the file; it never edits them.
- Checked: holding C12 produced a bundle of C5, C6, C7 and C20, all `draft`.

## 5. Background design

**What changed**
- The page background now has soft radial colour washes: mint top-left, water-blue top-right, and a sage glow at the bottom, over a warm off-white base.
- A very light grain texture (inline SVG noise at 6% opacity, multiply blend) gives some texture.
- A faint pattern of flowing stream lines (inline SVG, 22% opacity, fading in from the left) sits behind the page title, echoing the river theme.
- The top bar is frosted glass (translucent white with backdrop blur).
- Cards are near-white with a slightly warmer border; the decision card has a subtle white-to-mint gradient.
- All decoration is pure CSS with inline SVG: no image files and no network requests. It's turned off when printing, and fainter on phones.

**Where:** a CSS block before `.map-hint` (`body`, `body::before`, `.intro:before`, `.topbar`, `.surface`, `.decision`).

**How it helps:** the page feels designed and on-theme, while the content stays high-contrast and readable.

## Checks run

- All 10 city and mode views render with no console errors. Review totals are correct (Coimbra replay 11 = 5 visits + 6 notices; Toulouse replay 12).
- Approve C5 + hold C12 + approve notice C2 gave "3 of 11 reviewed · 2 approved · 1 on hold", the button "Download FHIR (4)", a held pin and an approved pin, focus on the pressed button, and the choices stored in `localStorage`.
- `python test_plan.py`: 22 checks passed.

## Follow-up for the docs pass (`VIDEO-SCRIPT.md`, README screenshots)

- The banner now reads "Replay of a real storm · 10 May 2026".
- Notices open with "Read the draft notice".
- The script could show Approve and Hold, and the "Download FHIR (N)" count.
- The README screenshots need recapturing.
