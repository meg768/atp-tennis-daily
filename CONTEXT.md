# ATP Tennis Daily

## Purpose

This file stores workflow, operating rules, restart behavior, and maintenance instructions for this workspace.

Read this file first at the start of every new thread or restart. Then read the editorial memory.

## Memory Split

- this file is the workflow and operations source of truth
- `CONTENTS.md` is the editorial, source, and presentation source of truth
- keep project documentation in English
- update this file when workflow, automation, runtime behavior, or developer conventions change
- update `CONTENTS.md` when coverage, writing style, source priorities, or page structure change
- mirror user-facing workflow changes in `README.md`

## Startup Rule

- at the start of every new thread or restart, read this file first and then `CONTENTS.md` before replying or running commands
- this rule applies even to short or casual prompts

## Working Rules

- the main output is HTML, not a chat report
- the normal deliverable is `editions/YYYY-MM-DD.html` plus `editions/latest.html`
- after a successful scan, a short confirmation is enough unless the user asks for more
- prefer small, durable rules over brittle prompt micromanagement

## Core Commands

- treat short prompts such as `scan`, `edition`, `refresh`, and `help` as scanner commands
- `scan` means: fetch the current ATP singles card, enrich it with ATP data plus current reporting, and update the two edition files
- internal runner shortcut: `atp-tennis-daily-scan`
- when handling `atp-tennis-daily-scan`, do the scan work directly in the current session
- never call `run.sh` from inside `atp-tennis-daily-scan`
- never spawn a nested runner from `atp-tennis-daily-scan`

## Runtime Rules

- use `https://tennis.egelberg.se` as the canonical runtime backend
- fetch the current match card and Svenska Spel prices from `https://tennis.egelberg.se/api/oddset`
- use ATP and reliable current reporting only as enrichment
- use bookmaker odds only for matches that have not started yet
- `editions/latest.html` may be read to preserve layout, but it must never be used as a reason to skip regeneration
- every scan run must generate a fresh edition from live sources
- every scan run must rewrite the visible snapshot timestamp and output HTML

## Preferred ATP Endpoints

- `GET /api/oddset`
- `GET /api/player/lookup?query=...`
- `GET /api/players/odds?playerA=...&playerB=...&surface=...`
- `GET /api/players/head-to-head?playerA=...&playerB=...&limit=10`
- `GET /api/events/calendar`
- `GET /api/flags/:code.svg`
- `GET /api/meta/endpoints`
- `GET /api/meta/schema.sql`
- `POST /api/query` only when the normal endpoints are not enough

## Rendering Rules

- `template.html` is the main editable layout file
- generated editions must remain fully standalone HTML files
- keep styling inline unless the user asks otherwise
- the page theme may follow the dominant surface on the card
- support light and dark mode when practical, but do not let theme work destabilize the scan flow
- prefer ATP SVG flags over emoji
- render match-title flags as circular slots using `background-image:url(...)`
- if a flag asset is missing, keep the same slot and rely on the backend fallback SVG
- the `Odds` block may show `Svenska Spel`, `Tennis Abstract`, and `Vitel`
- when edge is shown, append it inline after the odds in the same cell, for example `1.43 (-2%)`
- round displayed edge to whole percentages with no decimals
- do not render separate `Tennis Abstract edge` or `Vitel edge` rows
- when present, the main price block should sit full-width in the match flow rather than being squeezed into the narrow side column
- never abbreviate `Tennis Abstract` to `TA` in user-facing HTML
- let `Spelidé` follow the inline `Tennis Abstract` edge first when that data is available
- keep `Vitel` as a secondary experimental signal, but it must not control `Spelidé` when `Tennis Abstract` is also visible
- do not use the bare suffix `pp` in user-facing output
- do not show a `Codex` odds row in the edition
- keep full player names in the main match title
- use player surnames rather than first names in odds-table headers and in `Spelidé`

## Scheduling And Run Script

- `run.sh` should default to one scan and exit
- `run.sh --publish` is optional
- `run.sh --daily HH:MM` enables the long-lived daily schedule in `Europe/Stockholm`
- `run.sh` should call `atp-tennis-daily-scan` rather than embedding a long literal prompt
- when `run.sh --publish` is used, publish dated files under `editions/` and also mirror `editions/latest.html` to the site root as `index.html`

## Restart Reliability

- keep `AGENTS.md`, this file, and `CONTENTS.md` in the project root
- if either memory file is renamed, update `AGENTS.md`
- prefer updating the memory files over hard-coding workflow rules elsewhere
