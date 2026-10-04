# UI pass — daylight after rain

## WHAT

The page background is an overcast storm field. It is darker than the white mist and lighter than the old night teal. The dot grid, corner washes, and contour lines stay. Cards are storm paper (`#e4eee8`), the same grey-green as the field and one step lighter, so they are not pure white. Inner wells are a step darker (`#d7e6de`). The street map is the normal OpenStreetMap tiles. The old invert filter that forced a dark map is off. Creek green is reserved for text, the selected city, and actions. Rain bars and their labels use the same darker green so they stay readable on the cards.

## WHERE

`web/app.css` tokens, page background, header, hero, cards, sheets, and map chrome. `web/app.js` rain-chart fills, the visit-budget slider maximum, and labels. `web/index.html` theme-color.

## HOW

Night teal (`#1f6b5c`) read as a closed field. Plain mist (`#e4f1ea`) read as white. The field now runs from cloud (`#c5d5cc`) through overcast (`#a3bab0`) to wet ground (`#7f9a8e`), with a deeper water wash and a rain-cloud wash. Ink on that field stays dark enough to read. The headline facts use a deeper green (`#084636`) so they do not disappear into the field.

The overview sentence and the “Latest saved forecast” line sit on storm paper with a visible edge, so they are not bare text on the field. Every decision headline, including the Oslo no-storm sentence, uses the full content width. Line balancing is off, so the first line runs to the edge of the column instead of stopping halfway. The sampling warning and the forecast line do the same. Export and import sit 16px below the review box. Download FHIR uses the creek green (`#0f7a5c`). On a narrow screen the page tabs wrap instead of running off the edge.

The visit slider used the number of sites that qualify right now as its maximum, and that maximum shrank when the budget was lowered. On Coimbra’s latest forecast only 2 sites qualify, so the slider stuck at 2. It now runs from 0 to every site in the city, the same limit as the + button. A higher budget does not invent visits; only qualifying sites are planned.

## CHECKS

Desktop overview, Plan & map, Notices, Evidence, and a 390-wide overview, after the plan loaded, with `?guide=0`. Screenshots under `C:\Users\ankit\Downloads\oneaqua\_shots\` named `daylight-overview.png`, `daylight-plan.png`, `daylight-notices.png`, `daylight-evidence.png`, and `daylight-mobile.png`.
