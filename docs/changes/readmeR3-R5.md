# R5 — Split web assets

## What and where

Moved the embedded style and main script from `web/index.html` into `web/app.css` and `web/app.js`. The HTML now links the CSS after Leaflet and defers the app script after Leaflet.

## Why

The 140 KB single file made review and maintenance difficult. `index.html` is now about 11 KB, with the same markup, font paths, and behavior.

## Checks

`node --check web/app.js` passes. The Coimbra replay and deep links load without application console errors in the browser.
