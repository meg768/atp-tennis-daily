# Tennis Daily Contents

## Purpose

This file stores the editorial brief for what the edition should contain, how it should be written, which sources matter, and how the page should look.

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

## Page Structure

Use this order:

1. `Tennis Daily`
2. date line
3. one section per match

Do not use separate front-page style sections such as `Front Page`, `I Blickfånget`, or `Dagsläget`.

## Match Section Template

Each match section should usually contain:

- heading: flag slot, player name, optional country code, ranking, `vs`, then the same for the opponent
- one short matchup summary
- `Spelbild`
- `Form och historik`
- `Head-to-head` when relevant
- when previous meetings exist, `Head-to-head` should prefer a compact results table with date, tournament, surface, and score rather than only a prose summary
- `Odds` as a full-width primary block rather than a cramped side-column block
- `Skador och dagsläge` when relevant
  This may also cover recent inactivity or a return after a long break when that helps explain a player's current ranking versus likely level.
  When mentioning inactivity or a layoff, explicitly name which player it applies to.
- `Marknad och modell` when relevant
- one short closing line

Use one fixed block order and naming contract:

- `match-block--odds` for the main full-width odds block
- main column in this order:
  `match-block--play`, `match-block--form`, `match-block--ranking`, `match-block--win-rate`, `match-block--recent-results`, `match-block--head-to-head`
- side column in this order:
  `match-block--status`, `match-block--market`, `match-block--decider`
- the generator should fill this structure with content rather than inventing alternative wrapper layouts per match
- the hidden fixed match scaffold in `template.html` should be treated as the source template for every generated match section
- fill the placeholders inside that scaffold with match-specific content instead of writing new section HTML from scratch
- the official slot names for one match are:
  `title`, `summary`, `time`, `event`, `record`, `surface-label`, `surface-value`, `surface-subtext`, `odds-table`, `betting-idea`, `play-pattern`, `form-history`, `head-to-head`, `status`, `ranking-table`, `win-rate-table`, `win-rate-note`, `recent-results`, `market-model`, `decider`

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
- in tables, avoid line breaks when they are not necessary; prefer keeping dates, scorelines, and short comparative rows on one line when space allows
- in `Head-to-head`, keep a compact table but use exactly three columns: `Datum`, `Spelare`, `Resultat`
- in `Spelare`, show the winner first in the form `winner vs looser`
- in `Resultat`, show the winner's score line
- in date columns such as `Head-to-head` and `Senaste resultat`, display dates as `YYYY-MM-DD`
- add a `Vinstprocent` table with columns `Spelare`, `3 mån`, `6 mån`, `12 mån`
- in each time-period column, show both the overall win rate and the win rate against better-ranked players over the same period, using percentages only
- add a short explanatory note under `Vinstprocent` that clarifies the format as `overall win rate / win rate against better-ranked players`
- in `Senaste resultat`, keep the table structure fixed to exactly three columns: `Datum`, `Spelare`, `Resultat`
- in `Spelare`, show the winner first in the form `winner vs looser`
- in `Resultat`, show the winner's score line
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

## What To Avoid

- generic filler
- unsupported injury claims
- long stat dumps without interpretation
- repeated biography text
- turning the page into a pure betting sheet
