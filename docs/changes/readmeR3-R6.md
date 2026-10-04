# R6 — Basemap provider check and recovery

## What and where

The requested CARTO `dark_all` layer was implemented and tested. Its returned tiles visibly said **API KEY REQUIRED**. CARTO's current basemap terms require a key, so the final `web/app.js` uses the working OpenStreetMap raster layer with its attribution, and `web/app.css` applies the dark treatment. No key is embedded in the public client.

## Why

An unusable branded tile grid would conceal the streams in the demo. The current layer keeps streets visible behind the official numbered pins. The Street map toggle and offline pins remain available.

## Checks

The Plan page displays numbered pins and OpenStreetMap attribution. Map tiles still require internet. CARTO's documented key requirement was verified on 2026-10-04: https://www.carto.com/basemaps/apikey/ . Native dark tiles can be reconsidered if a licensed key or a reliable keyless source is available.
