# ATP Tennis Daily

## Purpose

This file is the single project memory and source of truth for this workspace.
It stores workflow, operating rules, content intent, rendering rules, restart behavior, and maintenance instructions.

Read this file first at the start of every new thread or restart.

## Source Of Truth

- this file is the only project memory file
- `template.html` is the render and layout implementation of this file
- keep project documentation in English
- update this file when workflow, visible content rules, section intent, automation, or developer conventions change
- update `template.html` when the rendered structure, labels, placeholders, slot wiring, or layout implementation change
- mirror user-facing workflow changes in `README.md`

## Startup Rule

- at the start of every new thread or restart, read this file before replying or running commands
- this rule applies even to short or casual prompts

## Working Rules

- the main output is HTML, not a chat report
- the normal deliverable is one local root file: `tennis-daily.html`
- after a successful scan, a short confirmation is enough unless the user asks for more
- prefer small, durable rules over brittle prompt micromanagement

## Core Commands

- treat short prompts such as `scan`, `edition`, `refresh`, and `help` as scanner commands
- `scan` means: fetch the current ATP singles card, enrich it with ATP data plus current reporting, and update `tennis-daily.html`
- internal runner shortcut: `atp-tennis-daily-scan`
- `atp-tennis-daily-scan` is a Codex-internal scan prompt, not a shell command in `PATH`
- do not try to run `atp-tennis-daily-scan` directly in a terminal on Mac or Pi; use `./run.sh` or `./run.sh --publish` there
- when handling `atp-tennis-daily-scan`, do the scan work directly in the current session
- never call `run.sh` from inside `atp-tennis-daily-scan`
- never spawn a nested runner from `atp-tennis-daily-scan`
- a normal scan should not inspect `run.sh`, broad repo history, or large unrelated files once the workflow is already known
- a normal scan should not reread the full schema or endpoint docs unless a needed endpoint contract is genuinely unclear
- a normal scan should never read files under `playground/`; that directory is design-only and off limits in scan mode
- when a scan needs to write targeted SQL, it should verify table and column names against `GET /api/meta/schema.sql` rather than guessing

## Runtime Rules

- use `https://tennis.egelberg.se` as the canonical runtime backend
- fetch the current match card and Svenska Spel prices from `https://tennis.egelberg.se/api/oddset`
- use ATP and reliable current reporting only as enrichment
- use bookmaker odds only for matches that have not started yet
- skip matches whose live-card `state` shows that they are already in progress or otherwise live
- `tennis-daily.html` is output only during scans
- do not read from `tennis-daily.html` as scan input, layout source, fallback source, or regeneration template
- every scan run must generate a fresh edition from live sources
- every scan run must rewrite the visible snapshot timestamp and output HTML
- during a normal scan, prefer a short deterministic path: template, card, player lookup, odds, selective SQL, render, write
- do not guess undocumented endpoints during a normal scan; use only documented live endpoints or targeted read-only SQL
- when the edition is opened from `vitel`, it may receive a `theme=` query parameter such as `dark clay`; that override should control both color mode and surface theme for the rendered page
- the standalone HTML edition also supports local keyboard theme toggles: `F3` cycles `hard -> grass -> clay`, and `F6` toggles `light/dark`; the last local choice is stored in browser `localStorage`

## Preferred ATP Endpoints

- `GET /api/oddset`
- `GET /api/player/lookup?query=...`
- `GET /api/player/search?term=...` only as a fallback when lookup is empty or the live card lacks a player id
- `GET /api/oddset/odds?playerA=...&playerB=...`
- `GET /api/odds?playerA=...&playerB=...&surface=...`
- `GET /api/tennis-abstract/odds?playerA=...&playerB=...&surface=...`
- `GET /api/events/calendar`
- `GET /api/flags/:code.svg`
- `GET /api/meta/endpoints`
- `GET /api/meta/schema.sql`
- `POST /api/query` only when the normal endpoints are not enough

## Known Payload Shapes

- `GET /api/oddset` returns an array of match objects, not an object wrapper
- each `GET /api/oddset` row uses keys such as `id`, `start`, `tournament`, `state`, `score`, `playerA`, and `playerB`
- `playerA` and `playerB` each use keys such as `id`, `name`, and `odds`
- `GET /api/events/calendar` returns an object with an `events` array
- `GET /api/meta/endpoints` returns an object with an `endpoints` map keyed by path
- `GET /api/player/lookup` returns an array, usually with objects like `{ "id": "..." }`
- `GET /api/player/search` should be treated as a secondary candidate search endpoint, not the default first step
- do not spend scan time rediscovering these known shapes unless the backend clearly changed

## Scan Reliability

- for head-to-head, recent form, inactivity, and recent match lists, prefer targeted `POST /api/query` reads over endpoint guessing
- do not use undocumented paths such as `/api/players/odds` or `/api/players/head-to-head`
- avoid schema introspection queries such as `sqlite_master` during a normal scan
- use `GET /api/meta/schema.sql` as the schema source of truth when building SQL, but read only the narrow excerpt needed for the relevant tables or columns
- avoid broad endpoint probing during a normal scan
- keep shell output compact so the nested runner does not waste time or context on large dumps
- when a live-card player lacks an id, use a short deterministic fallback chain: existing id -> `/api/player/lookup` -> `/api/player/search` -> a tiny known-name alias map -> continue with partial data if still unresolved
- do not turn missing player ids into long exploratory work; spend at most one lookup call and one search call per unresolved player before falling back to partial rendering
- if a difficult but known name mismatch appears, resolve it silently from a tiny inline alias map rather than narrating the discovery process; for example `Diego Dedura-Palomero` should map directly to `D0LJ`
- if a per-match odds or model endpoint returns `404`, `500`, times out, or otherwise fails for one matchup, treat that row as missing data rather than a fatal scan error
- a single failed enrichment request must not abort the whole edition if the rest of the card can still be rendered
- prefer partial completion over restart loops: write the edition with the data that succeeded, and omit only the unavailable row or sentence
- once the fresh edition files are written and the required checks pass, stop immediately rather than continuing with extra endpoint or schema exploration
- do not announce fallback mechanics in the final scan narrative; resolve them quietly and keep the user-facing run summary short
- when the scan uses inline Python, avoid nested quote traps inside f-strings such as `f"{row["winner"]}"` or `f"{BASE}/api/player/search?term={urllib.parse.quote(player["name"])}"`; prefer helper variables, `.format(...)`, or a two-step pattern where dict values are first assigned to local variables
- for head-to-head result strings, prefer a safe pattern like `winner = row["winner"]`, `loser = row["loser"]`, `score = row["score"]`, then format the final sentence from those variables
- use the same safe pattern for URL construction in inline Python: for example `player_name = player["name"]`, `quoted_name = urllib.parse.quote(player_name)`, then build the final URL from `quoted_name`
- before sorting rows in inline Python, normalize nullable fields so the sort key never mixes `None` with strings or numbers
- use explicit safe sort keys such as `(row.get("start") or "", row.get("tournament") or "", row.get("playerA", {}).get("name") or "")` rather than comparing raw nullable values

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

## Page-Level Intent

- the page should feel like a calm, intelligent tennis daily edition
- the writing should be in Swedish
- the tone should be editorial rather than robotic
- every match should follow the same visible structure
- the page should favor clarity over cleverness

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
- if one odds or model source is temporarily unavailable for a matchup, omit that row and keep rendering the rest of the match section
- avoid anonymous layoff phrasing such as only giving a date gap; say which player has been inactive
- do not abort the whole page just because one matchup is missing one model row
- prefer dates normalized to `YYYY-MM-DD` and avoid leaking raw ISO timestamps into visible copy
- in tables, avoid unnecessary line breaks; keep dates, scorelines, and short comparative rows on one line when space allows

## Rendering Rules

- `template.html` is the main editable layout file
- the scan should follow this file for what gets shown, in what order, and with what intent
- the scan should follow `template.html` for the actual rendered structure, slot placement, and layout wiring
- do not rely on `README.md` to invent visible sections, labels, or placeholder meaning
- `playground/` contains local design sandboxes and experiments only; it is not part of scan input or runtime
- generated editions must remain fully standalone HTML files
- keep styling inline unless the user asks otherwise
- generated match sections should follow the canonical named block structure defined in `template.html`; the scan should fill those blocks with data rather than inventing new wrapper patterns per matchup
- treat the hidden `<template id="fixed-match-section-template">` inside `template.html` as the literal per-match scaffold during scans
- when rendering a match, replace the scaffold fields with data and text; do not output free-form alternative wrappers or differently ordered sections
- the official per-match slots are:
  `time`, `venue`, `event`, `title`, `summary`, `snapshot`, `match-profile`, `risk-flag`, `key-question`, `record`, `surface-label`, `surface-value`, `surface-subtext`, `odds-table`, `betting-idea`, `play-pattern`, `form-history`, `head-to-head`, `status`, `win-rate-table`, `win-rate-note`, `recent-results-player-a-title`, `recent-results-player-a`, `recent-results-player-b-title`, `recent-results-player-b`, `market-model`, `decider`
- do not invent extra slot names or omit these boxes unless the user explicitly changes the template contract
- all match blocks now belong in a single wide column; do not render a separate narrow side column
- `win-rate-table` belongs in that main column
- `recent-results` belongs in that main column
- `status` belongs in that main column
- `market` belongs in that main column
- `decider` belongs in that main column
- in `win-rate-table`, each time-period cell should include both overall win rate and win rate against better-ranked players for that same window, using percentages only
- add a short note under `win-rate-table` that explains the format as `overall win rate / win rate against better-ranked players`
- the page theme may follow the dominant surface on the card
- support light and dark mode when practical, but do not let theme work destabilize the scan flow
- render match-title flags as circular slots using `background-image:url(...)`
- keep the `match-title__flag` slot visually empty; never place visible country text inside the flag span itself
- for inline flag styles, use `background-image:url(https://...)` without inner quote characters, so the HTML attribute stays valid and browsers do not drop the flag image
- if a flag asset is missing, keep the same slot and rely on the backend fallback SVG
- when a `Tennis Abstract` or `Vitel` signal is missing, empty, or non-numeric, skip that signal rather than aborting the whole render

## Section Contract

### Masthead

Purpose:
- frame the page as `Tennis Daily`
- show that the page is a daily ATP-focused edition
- show when it was updated

Should show:
- `Tennis Daily`
- a centered ATP label in the top rail
- update time
- long-form date under the masthead title

Should feel:
- broadsheet
- restrained
- serif-led in the main title, sans serif in structural labels

### Match Title

Purpose:
- identify the matchup immediately and unambiguously

Should show:
- flag for Player A
- full name for Player A
- country code for Player A when used in the template
- ranking for Player A
- `vs`
- the same pattern for Player B

Important:
- keep full player names here
- keep the title visually aligned and easy to scan

### Match Kicker

Purpose:
- give immediate logistical context before the title and summary

Should show:
- start time
- place
- tournament and round

Should do:
- stay compact
- use one short line
- feel structural rather than editorial

### Match Summary

Purpose:
- give one short top-line read of the matchup

Should do:
- explain what the match likely hinges on
- say why the odds may or may not tell the full story
- stay short and editorial

Should avoid:
- generic filler
- long stat dumps
- repeating the same wording as later sections

### Match Overview

Purpose:
- orient the reader before the deeper blocks begin

Should show:
- one compact `Snabbkoll` line with the market and model read
- one short `Matchprofil` phrase in plain language
- one brief `Dagsläge` note with the most relevant current-status signal

Should do:
- stay compact
- help skimming
- avoid repeating full later sections word for word

Should avoid:
- long prose
- duplicate table data
- generic labels without an actual takeaway

### Match Meta

#### Nyckelfråga

Should show:
- one short question that frames what really decides the matchup

#### YTD

Should show:
- season record for both players in compact form

#### Surface Profile

Should show:
- one short label for the surface view
- one compact surface-specific comparison
- one small supporting line with rank or rating context

### Odds

Purpose:
- show the price picture clearly in one place

Rows:
- `Svenska Spel`
- `Tennis Abstract`
- `Vitel`

Should show:
- player surnames in the table headers
- odds for both players
- positive edge inline after model odds when available

Spelidé:
- one short Swedish takeaway
- grounded in the visible prices
- `Tennis Abstract` should lead when available
- `Vitel` can support, but should stay secondary

### Spelbild

Purpose:
- describe how the match is likely to be played

Should include:
- tactical pattern
- stylistic contrast
- what each player wants to do
- where the matchup probably turns

Should avoid:
- biography
- generic filler

### Form Och Historik

Purpose:
- explain recent form and broader context

Should include:
- concrete record language when possible
- recent wins and losses
- short-term form
- medium-term context when relevant

Preferred style:
- specific and compact
- more match-relevant than encyclopedic

### Vinstprocent

Purpose:
- show consistency over different windows

Columns:
- `Spelare`
- `3 mån`
- `6 mån`
- `12 mån`

Each period cell should show:
- total win rate
- win rate against better-ranked players in the same period

Display rule:
- percentages only
- use a short note under the table to explain the format

### Senaste Resultat

Purpose:
- show what each player has actually been doing lately

Structure:
- one subsection for Player A
- one subsection for Player B
- stacked vertically, not side by side

Subsection title:
- full player name
- sans serif

Table columns:
- `Datum`
- `Spelare`
- `Resultat`

Display rule:
- keep dates as `YYYY-MM-DD`
- show winner first in the `Spelare` column
- include ranking in the player line when the template asks for it
- show the score from the winner's perspective

### Head-to-Head

Purpose:
- show previous meetings between these two players only

Table columns:
- `Datum`
- `Spelare`
- `Resultat`

Display rule:
- keep dates as `YYYY-MM-DD`
- show winner first
- keep the table compact and readable

### Skador Och Dagsläge

Purpose:
- capture verified current-status context that changes how the match should be read

May include:
- injuries
- comeback situations
- long layoffs
- meaningful inactivity
- other verified availability context

Important:
- always name the player the note applies to
- avoid vague anonymous wording
- do not invent injury claims

### Marknad Och Modell

Purpose:
- explain how the market and the models relate

Should do:
- stay short
- stay plain
- stay in Swedish
- explain the relationship rather than repeat the raw numbers

### Det Avgör

Purpose:
- end the matchup with one clean closing thought

Should do:
- be one short line
- focus on the single most likely deciding factor

Should avoid:
- hedging with three different possibilities
- repeating the summary word for word

## General Output Rules

- use Swedish characters correctly: `å`, `ä`, `ö`
- prefer readable, compact sentences
- do not leak raw ISO timestamps into visible output
- keep tables from wrapping unnecessarily when space allows
- keep labels plain and structural
- prefer consistency across all matches

## What To Avoid

- generic filler
- unsupported injury claims
- long stat dumps without interpretation
- repeated biography text
- turning the page into a pure betting sheet

## Scheduling And Run Script

- `run.sh` should default to one scan and exit
- `run.sh --publish` is optional
- `run.sh --daily HH:MM` enables the long-lived daily schedule in `Europe/Stockholm`
- `run.sh` should call `atp-tennis-daily-scan` rather than embedding a long literal prompt
- `template.html` is the only local layout input for a normal scan; `tennis-daily.html` must remain output-only
- during a normal scan, rendered structure should be taken from `template.html`
- `run.sh --publish` should simply copy `tennis-daily.html` to the site root as `index.html`
- `run.sh` may send optional Pushover notifications when `PUSHOVER_TOKEN` and `PUSHOVER_USER` are set in the environment
- notification failures must never make an otherwise successful scan fail

## Restart Reliability

- keep `AGENTS.md` and this file in the project root
- if this file is renamed, update `AGENTS.md`
- prefer updating this file over hard-coding workflow rules elsewhere
