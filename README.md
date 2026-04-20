# ATP Tennis Daily

ATP Tennis Daily is the internal project and repo for the public page `Tennis Daily`.

The project produces one daily HTML edition focused on the current ATP singles card from Svenska Spel and publishes it to:

- `https://tennis-daily.egelberg.se`

The goal is not to build a generic tennis news page or a pure odds screen. The workflow starts from the live match card, then enriches each matchup with ATP database history, head-to-head context, form, overall level, event-surface context, and current reporting such as injuries or recent withdrawals. Matches that are already in progress should be skipped rather than written up as edition sections.

## Public Identity

- internal project / repo name: `ATP Tennis Daily`
- public site name: `Tennis Daily`
- public URL: `https://tennis-daily.egelberg.se`

This split is intentional. The codebase keeps the longer technical name, while the rendered page should simply present itself as `Tennis Daily`.

## What This Project Is For

- publish one daily HTML edition for the current ATP singles card
- cover all ATP singles matches on the Svenska Spel card
- exclude doubles, WTA, and Challenger matches
- combine bookmaker pricing with ATP database context
- use current web reporting for injury and availability context that the database does not contain
- present the result in a readable daily-edition layout

## Runtime Backend

In normal runtime, this project should talk to the hosted ATP HTTP service directly.

- the ATP service is the real backend dependency
- the intended runtime base URL is `https://tennis.egelberg.se`

## Core Workflow

The edition should be built in this order:

1. Fetch the current ATP singles card from the Svenska Spel-backed ATP feed
2. Resolve tournament and surface context
3. Enrich each match with ATP rankings, head-to-head, form, and model context from the hosted ATP service
4. Check current web reporting for injuries, withdrawals, absences, or other material updates
5. Write one HTML edition in Swedish
6. Save it as:
   - `tennis-daily.html`

## HTML Edition

The page is intentionally static:

- `CONTEXT.md` is the human-readable project memory and content contract
- `template.html` is the base layout and render file
- `playground/preview.html` is a local design sandbox and is not required for runtime
- `playground/` holds design experiments only and should stay off limits during normal scan runs
- `tennis-daily.html` stores the current local edition

The design is meant to stay focused on the match list itself. It should still work well on both desktop and mobile.
For anything the reader can actually see on the page, `CONTEXT.md` should be treated as the source of truth for content and section intent, while `template.html` should be treated as the render implementation.
The generated HTML can also carry the dominant surface theme in a fully self-contained way and follow the viewer's light/dark system preference without needing any external app runtime.
When opened from `vitel`, the page can also accept a `theme=` query parameter such as `dark clay` or `light hard` to mirror the frontend's current mode and surface selection.
The standalone page also supports keyboard theme shortcuts: `F3` cycles surface (`hard`, `grass`, `clay`) and `F6` toggles `light/dark`, with the latest local choice persisted in `localStorage`.
Match titles should prefer ATP-service SVG flags rather than emoji flags.

At publish time:

- `tennis-daily.html` remains local output only
- `tennis-daily.html` is copied to the public site root as `index.html`

## Quick Prompts

Typical prompts in this workspace:

- `scan`
- `generate today's edition`
- `refresh the html`
- `help`

Expected behavior:

- `scan` or `generate today's edition` should update the local `tennis-daily.html` file
- a normal scan should not create extra helper scripts or new project source files
- `help` should explain how the match list is sourced and how the edition is assembled
- this project uses one command model only; there is no separate user-mode versus developer-mode command split

## Sources

Normal source mix:

- Svenska Spel for the current ATP singles card and bookmaker odds
- `https://tennis.egelberg.se` for rankings, head-to-head, schedule context, model odds, and read-only SQL access
- ATP Tour and tournament pages for official context
- Reuters and other reliable reporting for current injury and availability news

Important interpretation rule:

- do not treat clay, hard, or grass as the default narrative lens of the whole edition
- use the actual event surface as matchup context when relevant
- if the ATP dataset offers useful overall or surface-specific ELO/rating signals, they are valid supporting evidence and may be shown in the edition

## ATP Service Endpoints

The ATP service documents itself now.

- `GET /api/meta/endpoints`
  Returns machine-readable metadata for the service endpoints, including method, params, query usage, and payload notes.

- `GET /api/meta/schema.sql`
  Returns the raw database schema SQL, including comments, functions, procedures, and DDL context.

For this project, treat those two metadata endpoints as the canonical documentation layer rather than maintaining a second full endpoint reference here.

## ATP Service Notes

- canonical base URL: `https://tennis.egelberg.se`
- scanner-relevant core endpoints:
  `GET /api/oddset`
  `GET /api/player/lookup`
  `GET /api/odds?playerA=...&playerB=...`
  `GET /api/tennis-abstract/odds?playerA=...&playerB=...&surface=...`
  `GET /api/events/calendar`
  `POST /api/query`
- canonical service docs:
  `GET /api/meta/endpoints`
  `GET /api/meta/schema.sql`
- `/api/query` is read-only by design, but it still exposes broad database reads and should stay private
- if we want the exact same config locally and on the Pi, the scanner should target these HTTP endpoints directly

## Automation

The repo includes a `run.sh` runner for scans.

- `./run.sh`
  Runs one scan and exits.

- `./run.sh --publish`
  Runs one scan, keeps `tennis-daily.html` local, writes it to the web root as `index.html`, and exits.

- `./run.sh --daily 09:00`
  Waits for the next `09:00` in `Europe/Stockholm`, then runs once per day at that time.

- `./run.sh --publish --daily 09:00`
  Publishes after each daily run by copying `tennis-daily.html` to the site root as `index.html`, and keeps the process alive inside PM2.

Internally, `run.sh` sends the short command `atp-tennis-daily-scan` to Codex. That means scan behavior should normally be changed in the project memory rather than by editing a long embedded shell prompt.
`atp-tennis-daily-scan` is an internal Codex shortcut, not a terminal command installed in `PATH`.
Do not run `atp-tennis-daily-scan` directly on your Mac or on `pi-kato`; use `./run.sh` or `./run.sh --publish` in the repo directory instead.
`atp-tennis-daily-scan` is meant to execute the scan directly in the active Codex session. It must not call `run.sh` again or start a nested runner process.
`tennis-daily.html` is output-only and must never be used as scan input, fallback input, or layout source.
`atp-tennis-daily-scan` should stay narrowly focused during a live scan: read `CONTEXT.md` for content intent, read `template.html` for rendered structure, fetch the current card and player context from `https://tennis.egelberg.se`, add current reporting for the specific matches on the card, then write `tennis-daily.html`. It should avoid broad repo searching or wandering through unrelated historical files during a normal scan.
`atp-tennis-daily-scan` should also use the documented ATP service endpoints directly. It should not probe `https://tennis.egelberg.se/`, inspect the frontend app, or scrape bundled JavaScript assets just to rediscover endpoints that are already part of the project memory.
During a normal scan, it should not inspect `run.sh`, broad repo history, or large unrelated files once the workflow is already known.
During a normal scan, it should not read `README.md` again once `CONTEXT.md` is already loaded.
To keep Pi scans stable, `atp-tennis-daily-scan` should keep tool output compact. It should prefer filtered endpoint reads and small excerpts over dumping full HTML, full JSON payloads, or large schema responses into the session.
When the scan needs SQL, it should verify table and column names against `GET /api/meta/schema.sql` and read only the narrow excerpt it needs rather than guessing column names.
The rendered edition should be written in Swedish with proper Swedish characters, including `å`, `ä`, and `ö`, rather than ASCII fallback spellings.
Known payload shapes should be treated as stable defaults during a normal scan: `/api/oddset` returns an array of matches, `/api/events/calendar` returns an object with an `events` array, `/api/meta/endpoints` returns an object with an `endpoints` map keyed by path, and `/api/player/lookup` returns an array of candidate ids. The scan should not keep rediscovering these shapes on every run unless the backend clearly changed.
For player identity resolution, keep the chain short and deterministic: use the live-card id when present, otherwise try `/api/player/lookup`, then `/api/player/search`, then a tiny known-name alias map for repeat offenders, and then continue with partial data instead of exploring further. `GET /api/player/search` is a fallback, not the default first step.
When a known mismatch recurs, prefer a silent inline alias such as `Diego Dedura-Palomero -> D0LJ` rather than spending extra turns rediscovering it. Do not narrate those fallback mechanics in the normal scan summary.
In the `Odds` block, `atp-tennis-daily-scan` should show `Tennis Abstract` rather than a generated `Codex` line. Do not shorten that label to `TA` in the rendered page. Show `Svenska Spel`, `Tennis Abstract`, and `Vitel`, and if edge is shown place it inline after the odds in the same cell using the same rule as `vitel`: `((1 / model_odds) - (1 / bookmaker_odds)) * 100`, rounded to whole percentages with no decimals, and shown only when positive. Do not render separate edge rows. `Spelidé` should follow the inline `Tennis Abstract` edge first, while `Vitel` remains a secondary experimental comparison. Avoid unexplained shorthand like `pp` in user-facing output. Keep full player names in the main match title, but use player surnames rather than first names in odds-table headers and in `Spelidé`.
For flag slots in inline HTML, write the style as `background-image:url(https://...)` without nested quote characters inside `url(...)`. That keeps the HTML attribute valid and avoids browsers dropping the flag image.
When `Spelidé` compares model signals, normalize the values to numeric types first. If a `Tennis Abstract` or `Vitel` signal is missing, empty, or non-numeric, skip that source rather than aborting the whole render.
In the `Head-to-head` block, `atp-tennis-daily-scan` should prefer the existing compact table style when previous meetings exist. Show date, tournament, surface, and a readable result line with winner and score. Fall back to a short prose note only when there are no relevant previous meetings.
Use the named block structure from `template.html` consistently rather than inventing ad-hoc wrappers per match. The intended order is a full-width `match-block--odds`, then one single broad column with `match-block--play`, `match-block--form`, `match-block--win-rate`, `match-block--recent-results`, `match-block--head-to-head`, `match-block--status`, `match-block--market`, `match-block--decider`.
Before the match title, render one compact kicker line with start time, place, and tournament/round context.
Before the metadata cards and deeper match blocks, keep one compact top overview row with `Snabbkoll`, `Matchprofil`, and `Dagsläge` so the page orients the reader before the long-form analysis starts.
In the metadata cards, prefer one creative `Nyckelfråga` card over a plain `Tid` card.
In `Senaste resultat`, split the block into two subsections, one per player, and let each subsection use the full player name as its sans-serif subsection title above the same compact three-column table shape: `Datum`, `Spelare`, `Resultat`. Keep those two subsections stacked vertically inside one broad `Senaste resultat` block rather than rendering them side by side. In `Spelare`, show the winner first in the form `winner vs looser`, and in `Resultat`, show the winner's score line. In visible date columns such as `Head-to-head` and `Senaste resultat`, render `YYYY-MM-DD` rather than full ISO timestamps.
When building inline Python during a scan, avoid brittle nested f-string quoting such as `f"{row["winner"]}"` or `f"{BASE}/api/player/search?term={urllib.parse.quote(player["name"])}"`. Prefer small intermediate variables like `winner`, `loser`, `score`, `player_name`, and `quoted_name`, then build the final text or URL from those variables.
Before sorting rows in inline Python, normalize nullable values first so the sort key never compares `None` with strings or numbers. Prefer keys such as `(row.get("start") or "", row.get("tournament") or "", row.get("playerA", {}).get("name") or "")` instead of sorting directly on raw nullable fields.
In `Skador och dagsläge`, the scan may also call out a meaningful recent inactivity period, comeback, or long layoff when it helps explain why the current ranking may undersell the player's real level.
When doing that, name the player directly in the sentence instead of only describing an anonymous gap in days.
For matchup prices, use the documented live endpoints such as `/api/oddset`, `/api/oddset/odds`, `/api/odds`, and `/api/tennis-abstract/odds`. Do not guess undocumented paths such as `/api/players/odds` or `/api/players/head-to-head`.
For head-to-head, recent form, and inactivity, prefer targeted `POST /api/query` reads over endpoint guessing, but validate the needed SQL columns against `GET /api/meta/schema.sql` first.
If a per-match odds or model request returns `404`, `500`, times out, or otherwise fails for one matchup, treat that source row as unavailable and continue rendering the edition. A single bad model request must not abort the whole scan.
Once `tennis-daily.html` is written, the scan should stop immediately rather than continuing with extra endpoint or schema probing.

For the Pi runner, `run.sh` should use `codex exec --sandbox danger-full-access` rather than `--full-auto`. In practice, the narrower nested sandbox can block DNS or outbound HTTP for `tennis.egelberg.se` and Svenska Spel-backed feeds even when plain shell networking works on the machine.

## Deployment

Current production layout on `pi-kato`:

- repo clone:
  - `/home/pi/atp-tennis-daily`
- published site root:
  - `/var/www/html/tennis-daily`
- current edition at runtime:
  - `/var/www/html/tennis-daily/index.html`

The domain `tennis-daily.egelberg.se` is served by Apache and should simply display the latest published edition.

## Scheduling

The project runs independently of the older scanner project.

Current PM2 setup on `pi-kato`:

- process name: `atp-tennis-daily`
- script: `/home/pi/atp-tennis-daily/run.sh`
- args: `--publish --daily 09:00`
- timezone intent: `Europe/Stockholm`

That means the public site should refresh automatically every day at `09:00` Swedish time, while manual runs can still be done with:

```bash
cd /home/pi/atp-tennis-daily
./run.sh --publish
```

Optional Pushover notifications can be enabled for both successful and failed runs by setting these environment variables before starting the runner:

```bash
export PUSHOVER_TOKEN="your-app-token"
export PUSHOVER_USER="your-user-key"
export PUSHOVER_DEVICE="optional-device-name"
export PUSHOVER_SOUND="optional-sound"
```

`run.sh` also loads an optional local `.env` file from the repo root before those variables are read, which is the simplest way to keep secrets off the command line and out of git. Add `.env` on the machine that runs PM2, not in the repository.

If `PUSHOVER_TOKEN` and `PUSHOVER_USER` are present, `run.sh` sends a short success notification after a verified run and a failure notification if the scan or publish step aborts. When Codex session metadata is available, the message also includes the detected token count for that run. Notification errors are intentionally non-fatal so they do not break the daily job.

## Separation From The Old Project

This project is meant to stand on its own.

- do not depend on `tennis-scanner-daily` at runtime
- do not publish into the old webroot
- do not reuse the old PM2 process
- keep this repo, webroot, and domain independent so the old project can be retired later without affecting `Tennis Daily`

## Change Log

- 2026-04-06: Initial project scaffold added with project memory, HTML template, and edition workflow.
- 2026-04-07: Locked `atp-tennis-daily-scan` to the documented ATP endpoints so Pi scans do not waste time rediscovering APIs from the hosted frontend bundle.
- 2026-04-07: Added compact-output rules for `atp-tennis-daily-scan` so Pi scans do not bloat the nested Codex session with full HTML, payload, or schema dumps.
- 2026-04-07: Documented the actual endpoint payload shapes from `tennis.egelberg.se`, especially the live contracts for `/api/oddset`, `/api/player/lookup`, `/api/odds`, `/api/events/calendar`, and `/api/query`.
- 2026-04-07: Removed the inherited user-mode versus developer-mode split from this project and simplified command handling to one workflow.
- 2026-04-09: Detached the project from `tennis-scanner-daily`, renamed the public page to `Tennis Daily`, published it at `https://tennis-daily.egelberg.se`, and added an independent PM2 job for daily `09:00` publishing.
- 2026-04-13: Tightened `Spelidé` guidance so scan runs coerce model signals to numbers before comparison and skip malformed signal rows instead of crashing the render.
- 2026-04-13: Tightened normal scan discipline further so runs reuse known payload shapes, avoid re-reading `README.md`, and stop immediately after a verified write instead of wandering into extra probes.
- 2026-04-14: Added optional Pushover notifications to `run.sh` for verified success and failure states without letting notification errors break the daily run.
- 2026-04-14: Tightened the inline Python guidance further so scan runs break out dict lookups before formatting URLs or result strings, avoiding repeated `f-string: unmatched '['` failures.
- 2026-04-14: Tightened player-id fallback guidance so scans use a short lookup -> search -> alias chain, resolve known mismatches like `Diego Dedura-Palomero -> D0LJ` silently, and stop burning tokens on rediscovery.
- 2026-04-14: Tightened inline Python sorting guidance so nullable values are normalized before sort keys are compared, avoiding `TypeError` crashes like `NoneType` versus `str`.
- 2026-04-14: Tightened flag-rendering guidance so inline `background-image:url(...)` values use unquoted URLs and do not break the published HTML attribute.
