# Tennis Daily Contents

## Purpose

This file stores secondary editorial notes for how the edition may be written, which sources matter, and what kind of coverage the page should prioritize.

Visible page structure, box names, placeholders, labels, section order, and section intent should be taken from `template.md` and `template.html`, not from this file.

## Editorial Intent

- publish a daily HTML page called `Tennis Daily`
- cover all ATP singles matches currently listed on the Svenska Spel card exposed by `https://tennis.egelberg.se/api/oddset`
- exclude doubles, WTA, and Challenger
- use `https://tennis.egelberg.se` as the statistical backbone
- enrich with current reporting when it adds real value, especially for injuries, withdrawals, and recent developments
- write the edition in Swedish, using normal Swedish spelling with `å`, `ä`, and `ö`

## Coverage Rules

- include all ATP singles matches on the current card from `https://tennis.egelberg.se/api/oddset`
- skip matches that are already in progress or otherwise live
- do not add matches that are not on the card
- do not use live matches to drive the odds analysis
- when multiple tournaments are active, include them all but keep the page easy to scan

## Match Analysis Rules

For each match, include as much of this as the sources support:

- tournament, surface, and start time when known
- player ranking and nationality
- overall and surface-specific ELO or rating context when useful
- player strengths, tactical identity, and likely match pattern
- recent form
- recent inactivity, layoffs, or long breaks from the tour when they meaningfully affect the matchup context
- head-to-head when relevant
- odds context from Svenska Spel, Tennis Abstract, and Vitel
- injuries, withdrawals, or fitness questions when they are currently and credibly reported
- a short closing judgement on what is most likely to decide the match

## Source Order

1. `https://tennis.egelberg.se/api/oddset` for the card and bookmaker prices
2. `https://tennis.egelberg.se` for rankings, odds, history, and model context
3. ATP Tour and tournament pages for official context
4. reliable current reporting for injuries and recent developments

## Page Contract

- `template.md` defines the visible content contract in human language
- `template.html` implements that contract in rendered HTML
- if the user wants to change a visible heading, box, placeholder, section order, table shape, or label, update `template.md` first and then sync `template.html`
- do not introduce front-page style sections such as `Front Page`, `I Blickfånget`, or `Dagsläget` unless the template files are changed to ask for them

## Presentation Rules

- the page should feel calm, readable, and match-focused
- keep the masthead in a restrained broadsheet direction rather than an oversized poster look
- the current preferred title treatment is `Libre Baskerville`, with the masthead and running text in serif while labels, rails, and small structural headings stay in sans serif
- do not make any single surface the master narrative of the whole page
- let the current event surface act as matchup context
- keep labels plain rather than decorative
- prefer flat box colors over visible gradients inside cards
- use proper Swedish characters in all rendered copy instead of ASCII fallback spellings
- use surface themes:
  - clay = warm red/terracotta
  - grass = green
  - hard court = blue
- prefer ATP SVG flags over emoji
- render those flags as circular `background-image` slots
- keep mobile readability strong
- in the `Odds` block, show `Svenska Spel`, `Tennis Abstract`, and `Vitel` when the data supports it
- do not render a separate match-meta box such as `Svenska Spel / modell` above the `Odds` block; all price comparison belongs inside `Odds` and, when useful, in `Marknad och modell`
- if one odds or model source is temporarily unavailable for a matchup, omit that row and keep rendering the rest of the match section
- if edge is shown, place it inline after the odds in the same cell using the same rule as `vitel`
- define edge as implied-probability difference: `((1 / model_odds) - (1 / bookmaker_odds)) * 100`
- round displayed edge to whole percentages with no decimals
- show only positive edge values; omit negative edge labels entirely
- do not render separate edge rows
- never abbreviate `Tennis Abstract` to `TA` in the rendered page
- use one consistent primary model reference for `Spelidé`
- let `Spelidé` follow the inline `Tennis Abstract` edge first when it is available
- keep `Vitel` as a secondary experimental comparison when useful
- do not let `Spelidé` follow one signal while the visible main odds line follows another
- when `Spelidé` compares model signals, normalize values to numbers first; if a source returns empty or non-numeric signal data, omit that source from the comparison instead of crashing the render
- avoid unexplained shorthand like `pp` in rendered output
- keep full player names in the main match title
- use player surnames rather than first names in odds-table headers and in `Spelidé`
- avoid anonymous layoff phrasing such as only giving a date gap; say which player has been inactive
- do not abort the whole page just because one matchup is missing one model row
- prefer dates normalized to `YYYY-MM-DD` and avoid leaking raw ISO timestamps into visible copy
- in tables, avoid unnecessary line breaks; keep dates, scorelines, and short comparative rows on one line when space allows
- if the template asks for a specific visible table format, subsection split, label, or wording pattern, follow the template version over any older prose here

## What To Avoid

- generic filler
- unsupported injury claims
- long stat dumps without interpretation
- repeated biography text
- turning the page into a pure betting sheet
