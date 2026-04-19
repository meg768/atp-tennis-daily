# Tennis Daily Template Guide

This file is the human-readable companion to `template.html`.

Use this file when you want to edit what each visible section is supposed to do, without digging through raw HTML first.
`template.html` still controls the actual rendered structure, slot names, and final layout contract.

## How To Use This File

- edit this file when you want to rethink a section in plain language
- edit `template.html` when you want to change the actual rendered markup, labels, table headers, placeholder text, or structure
- if these files drift apart, this file is the source of truth for content intent and `template.html` should be updated to match it

## Page-Level Intent

- the page should feel like a calm, intelligent tennis daily edition
- the writing should be in Swedish
- the tone should be editorial rather than robotic
- every match should follow the same visible structure
- the page should favor clarity over cleverness

## Masthead

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

## Match Title

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

## Match Summary

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

## Match Meta

### Tid

Should show:
- start date and time
- tournament and round as subtext

### YTD

Should show:
- season record for both players in compact form

### Surface Profile

Should show:
- one short label for the surface view
- one compact surface-specific comparison
- one small supporting line with rank or rating context

## Odds

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

Edge Rule:
- use implied-probability difference
- round to whole percentages
- show only positive edge
- never show separate edge rows

Spelidé:
- one short Swedish takeaway
- grounded in the visible prices
- `Tennis Abstract` should lead when available
- `Vitel` can support, but should stay secondary

## Spelbild

Purpose:
- describe how the match is likely to be played

Should include:
- tactical pattern
- stylistic contrast
- what each player wants to do
- where the matchup probably turns

Should avoid:
- biography
- generic “both are strong players” language

## Form Och Historik

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

## Ranking Och Yta

Purpose:
- give a compact strength snapshot for the surface

Columns:
- `Spelare`
- `Rank`
- `Yt-ELO`
- `Ytfaktor`

Should do:
- make the surface-specific relationship easy to compare at a glance

## Vinstprocent

Variables

| Variable | Meaning |
| -------- | ------- |
| `@WinRatePlayerAName` | Show Player A surname in the win-rate table |
| `@WinRatePlayerBName` | Show Player B surname in the win-rate table |
| `@WinRatePlayerA3m` | Show Player A 3 month win rate and win rate against better-ranked players over the same period, percentage only |
| `@WinRatePlayerA6m` | Show Player A 6 month win rate and win rate against better-ranked players over the same period, percentage only |
| `@WinRatePlayerA12m` | Show Player A 12 month win rate and win rate against better-ranked players over the same period, percentage only |
| `@WinRatePlayerB3m` | Show Player B 3 month win rate and win rate against better-ranked players over the same period, percentage only |
| `@WinRatePlayerB6m` | Show Player B 6 month win rate and win rate against better-ranked players over the same period, percentage only |
| `@WinRatePlayerB12m` | Show Player B 12 month win rate and win rate against better-ranked players over the same period, percentage only |
| `@WinRateNote` | Explain briefly that each cell shows overall win rate / win rate against better-ranked players for the same period |

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

## Senaste Resultat

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

## Head-to-Head

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

## Skador Och Dagsläge

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

## Marknad Och Modell

Purpose:
- explain how the market and the models relate

Should do:
- stay short
- stay plain
- stay in Swedish
- explain the relationship rather than repeat the raw numbers

## Det Avgör

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
