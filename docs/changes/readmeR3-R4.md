# R4 — Animal and ecosystem signs

## What and where

`web/app.js` adds the animal/ecosystem heading and two observation questions to every language in `CARD_I18N`. The saved answer keys are `q6` and `q7`; print output follows the selected card language.

## Why

The citizen task card now records visible animal mortality and unusual water colour or algae alongside the existing human-contact and sewage observations. The card points people to the official app and tells them to report dead animals to local authorities.

## Checks

The card stores yes/no/unsure for both new questions. Ranking, notice generation, and FHIR export remain driven by the Python plan and are not affected by card answers. Translations remain drafts for native-speaker review.
