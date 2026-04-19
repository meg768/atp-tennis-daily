# ATP Tennis Daily

## Purpose

This file stores workflow, operating rules, restart behavior, and maintenance instructions for this workspace.

Read this file first at the start of every new thread or restart. Then read `template.md`.

## Memory Split

- this file is the workflow and operations source of truth
- `template.md` is the visible content and presentation source of truth
- `template.html` is the render/layout implementation of `template.md`
- `CONTENTS.md` is secondary editorial notes only, not the visible content contract
- keep project documentation in English
- update this file when workflow, automation, runtime behavior, or developer conventions change
- update `CONTENTS.md` only for secondary editorial notes when they are still useful
- update `template.md` when section purpose, wording intent, visible content rules, or box-by-box guidance change
- update `template.html` when the rendered structure, labels, placeholders, slot wiring, or layout implementation change
- mirror user-facing workflow changes in `README.md`

## Startup Rule

- at the start of every new thread or restart, read this file first and then `template.md` before replying or running commands
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
- a normal scan should not read `README.md` once `CONTEXT.md` and `CONTENTS.md` are already loaded
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

## Rendering Rules

- `template.md` is the main human-editable content spec for the edition
- `template.html` is the main editable layout file
- the scan should follow `template.md` for what gets shown, in what order, and with what intent
- the scan should follow `template.html` for the actual rendered structure, slot placement, and layout wiring
- do not rely on `README.md` or `CONTENTS.md` to invent visible sections, labels, or placeholder meaning
- `playground/` contains local design sandboxes and experiments only; it is not part of scan input or runtime
- generated editions must remain fully standalone HTML files
- keep styling inline unless the user asks otherwise
- generated match sections should follow the canonical named block structure defined in `template.html`; the scan should fill those blocks with data rather than inventing new wrapper patterns per matchup
- treat the hidden `<template id="fixed-match-section-template">` inside `template.html` as the literal per-match scaffold during scans
- when rendering a match, replace the scaffold fields with data and text; do not output free-form alternative wrappers or differently ordered sections
- the official per-match slots are:
  `title`, `summary`, `time`, `event`, `record`, `surface-label`, `surface-value`, `surface-subtext`, `odds-table`, `betting-idea`, `play-pattern`, `form-history`, `head-to-head`, `status`, `ranking-table`, `win-rate-table`, `win-rate-note`, `recent-results-player-a-title`, `recent-results-player-a`, `recent-results-player-b-title`, `recent-results-player-b`, `market-model`, `decider`
- do not invent extra slot names or omit these boxes unless the user explicitly changes the template contract
- all match blocks now belong in a single wide column; do not render a separate narrow side column
- `ranking-table` belongs in that main column
- `win-rate-table` belongs in that main column
- `recent-results` belongs in that main column
- `status` belongs in that main column
- `market` belongs in that main column
- `decider` belongs in that main column
- in `win-rate-table`, each time-period cell should include both overall win rate and win rate against better-ranked players for that same window, using percentages only
- add a short note under `win-rate-table` that explains the format as `overall win rate / win rate against better-ranked players`
- the page theme may follow the dominant surface on the card
- support light and dark mode when practical, but do not let theme work destabilize the scan flow
- prefer ATP SVG flags over emoji
- render match-title flags as circular slots using `background-image:url(...)`
- keep the `match-title__flag` slot visually empty; never place visible country text inside the flag span itself
- for inline flag styles, use `background-image:url(https://...)` without inner quote characters, so the HTML attribute stays valid and browsers do not drop the flag image
- if a flag asset is missing, keep the same slot and rely on the backend fallback SVG
- in `Senaste resultat`, render two undersektioner: one for Player A and one for Player B
- each undersektion should use the full player name as its subsection title
- those subsection titles should stay in sans serif, not serif body styling
- those two undersektioner should be stacked vertically inside one broad `Senaste resultat` block, not rendered as side-by-side columns
- each undersektion should render three columns: `Datum`, `Spelare`, and `Resultat`
- in the `Spelare` column, show winner first in the form `winner vs looser`
- in the `Resultat` column, show the winner's score line
- normalize visible date columns such as `Head-to-head` and `Senaste resultat` to `YYYY-MM-DD`
- never show raw ISO timestamps such as `2026-04-12T22:00:00.000Z` in user-facing output
- in tables, prefer layouts that avoid unnecessary wrapping; keep dates and scorelines on one line whenever practical
- in `Head-to-head`, render three columns: `Datum`, `Spelare`, and `Resultat`
- in the `Spelare` column, show the winner first in the form `winner vs looser`
- in the `Resultat` column, show the winner's score line
- prefer explicit block classes such as `match-block--play`, `match-block--form`, `match-block--head-to-head`, `match-block--status`, `match-block--ranking`, `match-block--recent-results`, `match-block--market`, and `match-block--decider`
- when present, the main price block should sit full-width in the match flow
- keep odds presentation rules in `template.md`; this file should only carry technical render constraints
- if a `Tennis Abstract` or `Vitel` signal is missing, empty, or non-numeric, skip that signal rather than aborting the whole render
- keep full player names in the main match title
- use player surnames rather than first names in odds-table headers and in `Spelidé`

## Scheduling And Run Script

- `run.sh` should default to one scan and exit
- `run.sh --publish` is optional
- `run.sh --daily HH:MM` enables the long-lived daily schedule in `Europe/Stockholm`
- `run.sh` should call `atp-tennis-daily-scan` rather than embedding a long literal prompt
- `template.html` is the only local layout input for a normal scan; `tennis-daily.html` must remain output-only
- during a normal scan, visible content intent should be taken from `template.md`
- during a normal scan, rendered structure should be taken from `template.html`
- `run.sh --publish` should simply copy `tennis-daily.html` to the site root as `index.html`
- `run.sh` may send optional Pushover notifications when `PUSHOVER_TOKEN` and `PUSHOVER_USER` are set in the environment
- notification failures must never make an otherwise successful scan fail

## Restart Reliability

- keep `AGENTS.md`, this file, and `CONTENTS.md` in the project root
- if either memory file is renamed, update `AGENTS.md`
- prefer updating the memory files over hard-coding workflow rules elsewhere
