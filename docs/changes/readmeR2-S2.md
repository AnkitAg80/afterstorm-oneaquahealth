# Round 2, S2 — citizen card in the city's language

## WHAT

Each citizen task card opens in the city's language and can switch to English. Coimbra is Portuguese, Toulouse French, Ghent Dutch, Benevento Italian, and Oslo Norwegian Bokmål. Only the title, safety line, five questions, answer labels, and two field labels are translated. The strings are the brief's table, copied as written. A city-language card says, in English, that the translation is a draft.

## WHERE

`web/index.html`: `CARD_I18N`, `CITY_LANG`, `cardPack()`, `citizenCard()`, and `citizenPrintArticle()`. The language choice is kept for the current city in `cardLangChoice`. Radio names and values stay `yes`, `no`, and `unsure`.

## HOW

Impact, participation, and feasibility. A volunteer in Coimbra, Toulouse, Ghent, Benevento, or Oslo can read the bank-side checks in the local language. The rest of the page, including the official app links, stays English. A native speaker still needs to check the draft before field use.

## CHECKS

- `python test_plan.py`: 23 assert-based checks passed.
- Coimbra replay C5 opens with `lang="pt"` and the title "Observação pós-tempestade — ficha de tarefa cidadã". Choosing Yes, then English, keeps Yes checked and shows the English title and safety line. Switching back to the city language keeps Yes and shows "Sim".
- The printed C5 card uses Portuguese and does not print the English safety line.
- Oslo replay O12 opens in `nb` with "Etter uværet — oppgavekort for innbyggere". Toulouse replay T17 opens in `fr` with "Observation après l'orage — fiche de mission citoyenne".
