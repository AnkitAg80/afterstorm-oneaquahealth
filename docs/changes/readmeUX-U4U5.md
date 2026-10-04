# UI/UX pass U4 + U5 — Type and colour polish, final checks, gallery

Scope: `web/index.html`, plus new files in `docs/gallery/` and `web/og.png`. No data, planner, ranking or FHIR change.

## U4. Type and colour polish (the user's "fonts don't match the background" feedback)

**What changed**
1. **One consistent text tone in the top band.** The lede and its "Based on 96 lab records" span now share one colour (`#b9cfc5`) and weight. The bold white span that clashed is gone.
2. **Brighter, consistent secondary text.** Labels went from `#a9c2b7` to `#c6d9d0`. Sub-text, step status, timestamps and the header sub-labels went to `#b4cac0`. The kicker is weight 500.
3. **Headline:** weight 500 → 600, tracking −0.03em, line height 1.18.
4. **Crisper accent:** the soft mint `#8fe0b8` became emerald `#6ee7b7` in all 25 places: key facts, toggles, the ring, mini-bars, pulses, the logo and focus rings.

**Contrast check (WCAG ratios, worst case over the brightest glow → best case):**

| Text | Ratio |
|---|---|
| Headline | 7.5 → 15.1 |
| Accent | 5.2 → 10.5 |
| Labels | 5.4 → 10.8 |
| Sub-text | 4.6 → 9.2 |
| Lede | 4.9 → 9.7 |
| Inactive pills | 6.5 → 12.9 |
| Dark text on the active emerald button | 10.5 |

Every one passes AA (4.5:1).

## U5. Final checks and polish

1. **Phone layout bug fixed.** At 375 px the top band's city, mode and budget controls overflowed and were clipped, because the pills row forced its grid column wider. Now `.hero-bar>*{min-width:0}`, with `minmax(0,1fr)` columns. The pills scroll sideways, and the mode buttons fill the width. Checked: no element overflows at 375 px, and page width = 375.
2. **Citizen task card styled.** The open card is a soft panel with an amber safety callout, a segmented City language | English switch, rounded question groups, pill-style Yes/No/Unsure answers (the chosen one turns green), proper text inputs, and styled links and Print button. The content and behaviour are unchanged.
3. **Deep links.** `#card-C5` opens that visit's citizen card; `#notice-C16` opens that notice. They're kept when the URL updates. Useful for sharing, for the video, and for the gallery capture.
4. **Link preview.** A meta description, Open Graph title, description and image (`web/og.png`, 1200×630, from the hero), and a Twitter large-image card.
5. **Gallery** (`docs/gallery/`, captions in `CAPTIONS.md`): 01 hero · 02 map, protection check and visits · 03 notices grid · 03b C16 detail · 04 citizen card in Portuguese · 05 ServiceRequest/1046 in the HL7 Europe sandbox.

## Checks

- All 10 city × mode views were exercised during U1–U3; U4 and U5 are CSS, markup or hash-only changes.
- The phone layout was rechecked after the fix.
- The summary bar's buttons are out of the tab order while it's hidden.
- Reduced motion is respected; the screenshots were taken with it on.
