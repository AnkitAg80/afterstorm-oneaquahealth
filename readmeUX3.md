# UX Part 3 — Map and list working together

Scope: `web/index.html` only. The planner, the data and the FHIR resources are unchanged.

## 1. Numbered pins that match the visit list

**What changed**
- Planned visits are now drop-shaped pins showing their rank (1, 2, 3…) in the visit's status colour. Sites with a draft notice get an amber ring.
- Other sites stay small dots, drawn underneath, so numbered pins are always on top.
- The old permanent code labels, which overlapped (C20, C6 and C12), are gone.
- When you change city or mode, the map now frames the **planned visits**, not all 20 sites. In Coimbra replay all 5 pins are clearly apart.

**Where:** `renderMap()` (Leaflet `L.divIcon` pins for planned sites; `circleMarker` for the rest); `.pin` styles; the map fits once per city and mode.

**How it helps:** "Visit 3" in the list is "3" on the map, so there's no guessing.

## 2. Two-way highlighting

**What changed**
- Hovering or tab-focusing a visit card enlarges its pin and adds a blue halo.
- Hovering a pin highlights its card.
- Clicking a pin scrolls to its card (if it's off-screen) and flashes it.
- "Show on map" still pans to the site and opens its popup.

**Where:** new `highlight()` and `focusCard()` functions; `mouseover`, `mouseleave` and `focusin` listeners on `#visits`; marker `mouseover`, `mouseout` and `click` handlers.

**How it helps:** the map and the list read as one view instead of two separate panels.

## 3. No scrolling inside the page, and a map that stays in view

**What changed**
- The visit list no longer scrolls inside its own box.
- The map column is `position: sticky`, so it stays on screen while you scroll the visits and notices.
- The right column now holds the visit list, then the notices. "How often do storms like this hit…" moved below the workspace.
- On phones the map scrolls normally.

**Where:** the workspace HTML (`.left-column` holds only the map; the new `.right-column` holds visits and notices); `.map-panel{position:sticky}`, `.visits-scroll{max-height:none}`.

## 4. Budget slider

**What changed:** a range slider under the − / + stepper. Dragging it redraws the visits, pins, summary sentence and download count live. The slider runs from 0 to the number of qualifying sites, and the stepper still allows any whole number. It announces "N site visits" to screen readers.

**Where:** `#budget-range` in the HTML; synced in `render()`; an `input` listener in `start()`.

## Checks run

- All 10 city and mode views render with no console errors.
- Pin counts match planned visits (Benevento replay 5, Coimbra live 2, Toulouse live 3, and so on).
- Hovering card C12 highlighted pin 2. Clicking pin C7 highlighted and flashed card C7.
- Slider set to 2: 2 cards, input shows 2, URL becomes `visits=2`.
- `python test_plan.py`: 22 checks passed.
