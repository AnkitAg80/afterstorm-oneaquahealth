# R7 — First-visit guide

## What and where

`web/index.html`, `web/app.css`, and `web/app.js` add a three-step guide attached to the controls, answer, and page tabs. The header's How it works button reopens it.

## Why

A new judge can learn the core flow before reading the detailed evidence. The guide only appears once, can be suppressed with `?guide=0`, and does not cover card or notice deep links.

## Checks

Next, Back, and Skip work; focus enters the guide and returns to the opener. Escape and Tab are handled. At a genuine 390 CSS pixel browser viewport, the phone guide uses a bottom sheet, and the document has no horizontal overflow. The guide adds no page layout shift. The headless Chrome `mobile.png` capture is cropped by its minimum window width and should not be used as proof of the phone layout.
