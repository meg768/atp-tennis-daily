# ATP Tennis Daily

ATP Tennis Daily is the repo behind the public page [Tennis Daily](https://tennis-daily.egelberg.se).

## What It Does

- builds one daily HTML edition for the current ATP singles card
- writes the local output to `tennis-daily.html`
- can publish that edition as `index.html` on the site

The full workflow, rendering contract, and scan rules live in the project memory. This file is only a short public-facing overview.

## Main Files

- `template.html` renders the page structure
- `tennis-daily.html` is generated output
- `run.sh` runs one scan or the scheduled daily publish flow

## Runtime

- canonical backend: `https://tennis.egelberg.se`
- public site: `https://tennis-daily.egelberg.se`
- scheduled runner on Kato: `/home/pi/atp-tennis-daily/run.sh --publish --daily 09:00`

## Common Commands

```bash
./run.sh
./run.sh --publish
./run.sh --daily 09:00
./run.sh --publish --daily 09:00
```

## Scope

- ATP singles only
- skip live or already started matches
- use Svenska Spel prices plus ATP data and current reporting
- publish a readable daily edition in Swedish
