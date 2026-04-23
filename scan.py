#!/usr/bin/env python3
import html
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import requests


BASE = "https://tennis.egelberg.se"
ROOT = Path(__file__).resolve().parent
TEMPLATE_PATH = ROOT / "template.html"
OUTPUT_PATH = ROOT / "tennis-daily.html"
STOCKHOLM = ZoneInfo("Europe/Stockholm")
UTC = timezone.utc
MONTHS_SV = {
    1: "januari",
    2: "februari",
    3: "mars",
    4: "april",
    5: "maj",
    6: "juni",
    7: "juli",
    8: "augusti",
    9: "september",
    10: "oktober",
    11: "november",
    12: "december",
}
WEEKDAYS_SV = {
    0: "måndag",
    1: "tisdag",
    2: "onsdag",
    3: "torsdag",
    4: "fredag",
    5: "lördag",
    6: "söndag",
}
CURRENT_NOTES = {
    "M0EJ": "Musetti sade till ATP i Madrid den 22 april att skadeproblem efter Australian Open har bromsat säsongen, men kvartsfinalen i Barcelona var ett tydligt friskhetstecken.",
    "F0F1": "ATP noterade den 19 april att Fils tog titeln i Barcelona och fortsätter lyftet efter den långa skadepausen under 2025.",
    "S0AG": "ATP:s Madrid-förhandsartikel den 21 april beskrev Sinner som glödhet inför turneringen efter sin starka Masters 1000-svit.",
}


@dataclass
class PlayerMatch:
    date: str
    event_name: str
    surface: str | None
    winner_id: str
    winner_name: str
    winner_rank: int | None
    loser_id: str
    loser_name: str
    loser_rank: int | None
    score: str | None


def fetch_json(path: str, *, params: dict[str, Any] | None = None) -> Any:
    response = requests.get(f"{BASE}{path}", params=params, timeout=30)
    response.raise_for_status()
    return response.json()


def run_query(sql: str) -> list[dict[str, Any]]:
    response = requests.post(f"{BASE}/api/query", json={"sql": sql}, timeout=60)
    response.raise_for_status()
    return response.json()


def sql_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def format_date_long(dt: datetime) -> str:
    return f"{WEEKDAYS_SV[dt.weekday()]} {dt.day} {MONTHS_SV[dt.month]} {dt.year}"


def format_time_sv(iso_text: str) -> str:
    dt = datetime.fromisoformat(iso_text.replace("Z", "+00:00")).astimezone(STOCKHOLM)
    return dt.strftime("%H.%M")


def normalize_surface(surface: str | None) -> str:
    mapping = {"clay": "Clay", "grass": "Grass", "hard": "Hard"}
    if not surface:
        return ""
    key = str(surface).strip().lower()
    return mapping.get(key, surface)


def surface_label_sv(surface: str | None) -> str:
    mapping = {"Clay": "grus", "Grass": "gräs", "Hard": "hardcourt"}
    return mapping.get(surface or "", "underlaget")


def player_country_name(code: str | None) -> str:
    mapping = {
        "ARG": "Argentina", "AUS": "Australien", "AUT": "Österrike", "BEL": "Belgien", "BIH": "Bosnien",
        "BRA": "Brasilien", "CAN": "Kanada", "CHI": "Chile", "CRO": "Kroatien", "CZE": "Tjeckien",
        "DEN": "Danmark", "ESP": "Spanien", "FRA": "Frankrike", "GBR": "Storbritannien", "GER": "Tyskland",
        "ITA": "Italien", "MON": "Monaco", "NED": "Nederländerna", "PER": "Peru", "POL": "Polen",
        "SRB": "Serbien", "USA": "USA",
    }
    return mapping.get(code or "", code or "Okänt")


def html_escape(value: Any) -> str:
    return html.escape("" if value is None else str(value), quote=True)


def format_rank(rank: Any) -> str:
    return f"#{int(rank)}" if rank not in (None, "", 0) else "rank ?"


def surname(name: str) -> str:
    parts = name.split()
    return parts[-1] if parts else name


def pct(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{round(value)}%"


def fmt_odd(value: Any) -> str:
    if value in (None, ""):
        return "n/a"
    number = float(value)
    if abs(number - round(number)) < 1e-9:
        return str(int(round(number)))
    return f"{number:.2f}".rstrip("0").rstrip(".")


def edge_from_model(book_odds: float | None, fair_odds: float | None) -> tuple[float | None, float | None]:
    if not book_odds or not fair_odds or fair_odds <= 0:
        return None, None
    probability = 1.0 / fair_odds
    roi = book_odds * probability - 1.0
    return probability, roi


def kelly_fraction(book_odds: float, probability: float) -> float:
    b = book_odds - 1.0
    if b <= 0:
        return 0.0
    return max(0.0, ((b * probability) - (1 - probability)) / b)


def build_rows_table(rows: list[tuple[str, str, str]], *, empty_text: str) -> str:
    if not rows:
        rows = [("—", empty_text, "—")]
    body = []
    for date, players, result in rows:
        body.append(
            "<tr>"
            f"<td>{html_escape(date)}</td>"
            f"<td>{html_escape(players)}</td>"
            f"<td>{html_escape(result)}</td>"
            "</tr>"
        )
    return "<thead><tr><th>Datum</th><th>Spelare</th><th>Resultat</th></tr></thead><tbody>" + "".join(body) + "</tbody>"


def build_simple_table(headers: list[str], rows: list[list[str]]) -> str:
    head = "<thead><tr>" + "".join(f"<th>{html_escape(h)}</th>" for h in headers) + "</tr></thead>"
    body_rows = []
    for row in rows:
        body_rows.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
    return head + "<tbody>" + "".join(body_rows) + "</tbody>"


def replace_placeholder(page: str, placeholder: str, value: str) -> str:
    return page.replace(f"{{{{{placeholder}}}}}", value)


def extract_match_template(template: str) -> tuple[str, str]:
    match = re.search(r'<template id="fixed-match-section-template">\s*(<section class="match-section">.*?</section>)\s*</template>', template, re.S)
    if not match:
        raise RuntimeError("Could not extract fixed match section template")
    section_html = match.group(1)
    page_without_template = template.replace(match.group(0), "")
    return section_html, page_without_template


def date_in_last_days(date_text: str, days: int, *, today: datetime) -> bool:
    match_date = datetime.fromisoformat(date_text).date()
    return match_date >= (today.date() - timedelta(days=days))


def better_ranked(opponent_rank: int | None, player_rank: int | None) -> bool:
    if not opponent_rank or not player_rank:
        return False
    return opponent_rank < player_rank


def compute_win_rates(player_id: str, current_rank: int | None, matches: list[PlayerMatch], *, today: datetime) -> dict[int, str]:
    result = {}
    for days in (92, 183, 366):
        sample = [m for m in matches if date_in_last_days(m.date, days, today=today)]
        played = len(sample)
        wins = 0
        versus_better = 0
        wins_versus_better = 0
        for m in sample:
            is_winner = m.winner_id == player_id
            opponent_rank = m.loser_rank if is_winner else m.winner_rank
            if is_winner:
                wins += 1
            if better_ranked(opponent_rank, current_rank):
                versus_better += 1
                if is_winner:
                    wins_versus_better += 1
        overall_pct = (wins / played * 100) if played else None
        better_pct = (wins_versus_better / versus_better * 100) if versus_better else None
        result[days] = f"{pct(overall_pct)} / {pct(better_pct)}"
    return result


def latest_match_date(player_matches: list[PlayerMatch]) -> str | None:
    return player_matches[0].date if player_matches else None


def inactivity_note(player_name: str, player_matches: list[PlayerMatch], *, today: datetime) -> str | None:
    last_date = latest_match_date(player_matches)
    if not last_date:
        return f"{player_name} saknar färska matchdata i databasen."
    dt = datetime.fromisoformat(last_date).date()
    gap = (today.date() - dt).days
    if gap >= 45:
        return f"{player_name} har inte spelat en registrerad match sedan {last_date}, vilket gör dagsformen svårare att prissätta."
    if gap >= 21:
        return f"{player_name} kommer in efter ett tävlingsuppehåll sedan {last_date}."
    return None


def form_line(player_name: str, player_matches: list[PlayerMatch], *, last_n: int = 5) -> tuple[str, int, int]:
    recent = player_matches[:last_n]
    wins = 0
    for m in recent:
        if m.winner_name == player_name:
            wins += 1
    losses = len(recent) - wins
    if not recent:
        return f"{player_name} saknar färska resultat i databasen.", wins, losses
    opponents = []
    for m in recent[:2]:
        if m.winner_name == player_name:
            opponents.append(f"vinst mot {m.loser_name}")
        else:
            opponents.append(f"förlust mot {m.winner_name}")
    return f"{player_name} är {wins}-{losses} i sina fem senaste matcher, med {', '.join(opponents)} som färskast.", wins, losses


def player_recent_rows(player_id: str, matches: list[PlayerMatch], *, limit: int = 5) -> list[tuple[str, str, str]]:
    rows = []
    for m in matches[:limit]:
        players = f"{m.winner_name} {format_rank(m.winner_rank)} vs {m.loser_name} {format_rank(m.loser_rank)}"
        rows.append((m.date, players, m.score or "—"))
    return rows


def h2h_rows(player_a: str, player_b: str, matches: list[PlayerMatch]) -> list[tuple[str, str, str]]:
    rows = []
    for m in matches:
        ids = {m.winner_id, m.loser_id}
        if {player_a, player_b} == ids:
            players = f"{m.winner_name} {format_rank(m.winner_rank)} vs {m.loser_name} {format_rank(m.loser_rank)}"
            rows.append((m.date, players, m.score or "—"))
    return rows[:5]


def describe_match_profile(a: dict[str, Any], b: dict[str, Any]) -> str:
    serve_gap = (a.get("serve_rating") or 0) - (b.get("serve_rating") or 0)
    return_gap = (a.get("return_rating") or 0) - (b.get("return_rating") or 0)
    if abs(serve_gap) > 0.7 and abs(return_gap) > 0.7:
        return "förstaslag mot kontring"
    if abs(serve_gap) > 0.7:
        return "serve plus första slaget"
    if abs(return_gap) > 0.7:
        return "returtryck från baslinjen"
    return "långa grundslagdueller"


def dominant_surface_value(surface: str, player: dict[str, Any]) -> tuple[int | None, int | None]:
    suffix = surface.lower()
    return player.get(f"elo_rank_{suffix}"), player.get(f"{suffix}_factor")


def round_text_from_models(book_a: float | None, book_b: float | None, odds_data: dict[str, Any] | None) -> tuple[str, str]:
    if not odds_data:
        return "Marknaden står ganska ensam i den här matchen.", "Modellstöd saknas i backend för just den här raden."
    ta = odds_data.get("tennisAbstractOdds") or [None, None]
    vi = odds_data.get("computedOdds") or [None, None]
    notes = []
    if ta[0] and ta[1]:
        notes.append(f"Tennis Abstract {fmt_odd(ta[0])}-{fmt_odd(ta[1])}")
    if vi[0] and vi[1]:
        notes.append(f"Tennis Daily {fmt_odd(vi[0])}-{fmt_odd(vi[1])}")
    market = f"Svenska Spel {fmt_odd(book_a)}-{fmt_odd(book_b)}"
    return f"{market}; " + ", ".join(notes), f"Marknaden öppnar med {market.lower()}, medan modellerna {'är närmare den linjen' if notes else 'saknas'}."


def best_edge(book_a: float | None, book_b: float | None, odds_data: dict[str, Any] | None, a_name: str, b_name: str) -> dict[str, Any] | None:
    if not odds_data:
        return None
    candidates = []
    for source, fair_a, fair_b in (
        ("Tennis Abstract", *(odds_data.get("tennisAbstractOdds") or [None, None])),
        ("Tennis Daily", *(odds_data.get("computedOdds") or [None, None])),
    ):
        prob_a, roi_a = edge_from_model(book_a, fair_a)
        prob_b, roi_b = edge_from_model(book_b, fair_b)
        if roi_a is not None:
            candidates.append({"source": source, "player": a_name, "roi": roi_a, "probability": prob_a, "book": book_a, "fair": fair_a})
        if roi_b is not None:
            candidates.append({"source": source, "player": b_name, "roi": roi_b, "probability": prob_b, "book": book_b, "fair": fair_b})
    candidates = [c for c in candidates if c["roi"] > 0]
    if not candidates:
        return None
    return max(candidates, key=lambda item: item["roi"])


def odds_cell(book_odds: float | None, fair_odds: float | None) -> str:
    if fair_odds in (None, ""):
        return "n/a"
    _, roi = edge_from_model(book_odds, fair_odds)
    label = f" (+{round(roi * 100)}%)" if roi and roi > 0 else ""
    return f"{fmt_odd(fair_odds)}{label}"


def build_kelly_rows(book_a: float | None, book_b: float | None, odds_data: dict[str, Any] | None, a_name: str, b_name: str) -> list[list[str]]:
    rows = []
    ta_odds = (odds_data.get("tennisAbstractOdds") or [None, None]) if odds_data else [None, None]
    vi_odds = (odds_data.get("computedOdds") or [None, None]) if odds_data else [None, None]
    for source, fair_a, fair_b in (
        ("Tennis Abstract", ta_odds[0], ta_odds[1]),
        ("Tennis Daily", vi_odds[0], vi_odds[1]),
    ):
        entries = []
        for player_name, book, fair in ((a_name, book_a, fair_a), (b_name, book_b, fair_b)):
            probability, roi = edge_from_model(book, fair)
            if probability is None or roi is None or roi <= 0:
                continue
            fraction = kelly_fraction(book, probability)
            entries.append((roi, player_name, book, fraction))
        if not entries:
            rows.append([html_escape(source), "Ingen edge", "0 kr", "0 kr", "0 kr"])
            continue
        roi, player_name, book, fraction = max(entries, key=lambda item: item[0])
        bankroll = 1000
        rows.append(
            [
                html_escape(source),
                html_escape(f"{player_name} @ {fmt_odd(book)} (+{round(roi * 100)}% ROI)"),
                html_escape(f"{round(bankroll * fraction / 2)} kr"),
                html_escape(f"{round(bankroll * fraction / 4)} kr"),
                html_escape(f"{round(bankroll * fraction / 8)} kr"),
            ]
        )
    return rows


def build_title(player_a: dict[str, Any], player_b: dict[str, Any]) -> str:
    def player_markup(player: dict[str, Any]) -> str:
        code = (player.get("country") or "ATP").upper()
        flag_url = f"{BASE}/api/flags/{code}.svg"
        return (
            '<span class="match-title__player">'
            f'<span class="match-title__flag" style="background-image:url({flag_url})">{html_escape(code)}</span>'
            f'<span class="match-title__name">{html_escape(player["name"])}</span>'
            f'<span class="match-title__country">{html_escape(player_country_name(code))}</span>'
            f'<span class="match-title__rank">{html_escape(format_rank(player.get("rank")))}</span>'
            "</span>"
        )
    return player_markup(player_a) + '<span class="match-title__separator">vs</span>' + player_markup(player_b)


def render_section(
    template_section: str,
    match: dict[str, Any],
    player_a: dict[str, Any],
    player_b: dict[str, Any],
    tournament: dict[str, Any],
    matches_by_player: dict[str, list[PlayerMatch]],
    all_matches: list[PlayerMatch],
    odds_data: dict[str, Any] | None,
    now: datetime,
) -> str:
    surface = normalize_surface(tournament.get("surface") or "Clay")
    surface_sv = surface_label_sv(surface)
    book_a = match["playerA"].get("odds")
    book_b = match["playerB"].get("odds")
    name_a = player_a["name"]
    name_b = player_b["name"]
    recent_a = matches_by_player[player_a["id"]]
    recent_b = matches_by_player[player_b["id"]]
    h2h = h2h_rows(player_a["id"], player_b["id"], all_matches)
    rates_a = compute_win_rates(player_a["id"], player_a.get("rank"), recent_a, today=now)
    rates_b = compute_win_rates(player_b["id"], player_b.get("rank"), recent_b, today=now)
    best = best_edge(book_a, book_b, odds_data, name_a, name_b)
    snapshot, market_model_text = round_text_from_models(book_a, book_b, odds_data)
    profile = describe_match_profile(player_a, player_b)

    surface_elo_a, surface_factor_a = dominant_surface_value(surface, player_a)
    surface_elo_b, surface_factor_b = dominant_surface_value(surface, player_b)
    surface_line = (
        f"{name_a} {fmt_odd(surface_factor_a) if surface_factor_a is not None else 'n/a'} mot "
        f"{name_b} {fmt_odd(surface_factor_b) if surface_factor_b is not None else 'n/a'} i {surface_sv}faktor."
    )
    if surface_elo_a and surface_elo_b:
        if surface_elo_a < surface_elo_b:
            surface_line = f"Elo på {surface_sv}: {surname(name_a)} rankad {surface_elo_a}, {surname(name_b)} {surface_elo_b}."
        elif surface_elo_b < surface_elo_a:
            surface_line = f"Elo på {surface_sv}: {surname(name_b)} rankad {surface_elo_b}, {surname(name_a)} {surface_elo_a}."

    note_bits = []
    for player in (player_a, player_b):
        if player["id"] in CURRENT_NOTES:
            note_bits.append(CURRENT_NOTES[player["id"]])
        extra_note = inactivity_note(player["name"], matches_by_player[player["id"]], today=now)
        if extra_note:
            note_bits.append(extra_note)
    if not note_bits:
        note_bits.append("Inga färska skadeuppgifter har hittats, så läs matchen främst genom form och underlag.")
    status_text = " ".join(note_bits[:2])

    form_a_text, form_a_wins, form_a_losses = form_line(name_a, recent_a)
    form_b_text, form_b_wins, form_b_losses = form_line(name_b, recent_b)
    form_history = f"{form_a_text} {form_b_text}"

    if best:
        summary = (
            f"{surname(best['player'])} får bäst stöd av modellerna här. "
            f"Matchen ser ut att avgöras av vem som bäst kan ta kommandot i de neutrala rallyna på {surface_sv}."
        )
        betting = f"<strong>Spelidé:</strong> {best['source']} lutar mest åt {html_escape(best['player'])}, där Svenska Spels pris fortfarande ger lite luft."
        decider = f"{surname(best['player'])} behöver få matchen spelad på sina första två slag oftare än marknaden räknar med."
        key_answer = f"Om {surname(best['player'])} får styra första slagväxlingen väger prisbilden över."
    else:
        rank_favorite = name_a if (player_a.get("rank") or 9999) < (player_b.get("rank") or 9999) else name_b
        summary = (
            f"Priserna ligger ganska nära modellerna, så läget handlar mer om spelbild än om en tydlig felprissättning. "
            f"Det här ser ut som en match där {surname(rank_favorite)} måste bära favorittrycket."
        )
        betting = "<strong>Spelidé:</strong> Marknaden och modellerna ligger nära varandra, så spelvärdet ser begränsat ut före start."
        decider = f"Den som tar flest gratispoäng bakom egen serve slipper spela på marginalen i Madrid-höjden."
        key_answer = "Förstaserve och första attack efter serven bör styra mest."

    play_pattern = (
        f"{name_a} vill få spelet in i sitt högsta tryck tidigt i duellen, medan {name_b} helst förlänger poängen och tvingar fram extra slag. "
        f"På {surface_sv} i Madrid blir längd, höjd och första initiativet centralt, särskilt när luften gör att bollen flyger igenom banan snabbare än på tyngre grus."
    )
    if (player_a.get("serve_rating") or 0) - (player_b.get("serve_rating") or 0) > 0.8:
        play_pattern = (
            f"{name_a} har den tydligare servespetsen och vill hålla poängen kortare, medan {name_b} behöver få fler returer i spel och dra matchen mot längre baslinjedueller."
        )
    elif (player_b.get("serve_rating") or 0) - (player_a.get("serve_rating") or 0) > 0.8:
        play_pattern = (
            f"{name_b} har den tydligare servespetsen och vill hålla poängen kortare, medan {name_a} behöver få fler returer i spel och dra matchen mot längre baslinjedueller."
        )

    if h2h:
        h2h_lead = Counter()
        for row in h2h:
            players_text = row[1]
            winner = players_text.split(" vs ")[0].rsplit(" ", 1)[0]
            h2h_lead[winner] += 1
        if h2h_lead:
            leader, wins = h2h_lead.most_common(1)[0]
            market_model_text += f" Inbördes möten senaste två åren lutar {wins}-{len(h2h)-wins} åt {leader}."

    risk_flag = status_text.split(".")[0].strip()
    if not risk_flag.endswith("."):
        risk_flag += "."

    odds_rows = [
        ["Källa", html_escape(name_a), html_escape(name_b)],
    ]
    odds_table = build_simple_table(
        odds_rows[0],
        [
            [html_escape("Svenska Spel"), html_escape(fmt_odd(book_a)), html_escape(fmt_odd(book_b))],
            [html_escape("Tennis Abstract"), html_escape(odds_cell(book_a, (odds_data or {}).get("tennisAbstractOdds", [None, None])[0])), html_escape(odds_cell(book_b, (odds_data or {}).get("tennisAbstractOdds", [None, None])[1]))],
            [html_escape("Tennis Daily"), html_escape(odds_cell(book_a, (odds_data or {}).get("computedOdds", [None, None])[0])), html_escape(odds_cell(book_b, (odds_data or {}).get("computedOdds", [None, None])[1]))],
        ],
    )
    kelly_table = build_simple_table(["Källa", "Spel (%ROI)", "1/2", "1/4", "1/8"], build_kelly_rows(book_a, book_b, odds_data, name_a, name_b))
    win_rate_table = build_simple_table(
        ["Spelare", "3 mån", "6 mån", "12 mån"],
        [
            [html_escape(name_a), html_escape(rates_a[92]), html_escape(rates_a[183]), html_escape(rates_a[366])],
            [html_escape(name_b), html_escape(rates_b[92]), html_escape(rates_b[183]), html_escape(rates_b[366])],
        ],
    )
    recent_a_table = build_rows_table(player_recent_rows(player_a["id"], recent_a), empty_text="Inga färska resultat")
    recent_b_table = build_rows_table(player_recent_rows(player_b["id"], recent_b), empty_text="Inga färska resultat")
    h2h_table = build_rows_table(h2h, empty_text="Inga möten senaste två åren")

    return f"""
<section class="match-section">
  <p class="match-kicker">
    <span data-slot="time">{html_escape(format_time_sv(match["start"]))}</span>
    <span class="match-kicker__sep">·</span>
    <span data-slot="event">{html_escape(f"{tournament['name']} · {tournament.get('type') or 'ATP'} · {surface_sv}")}</span>
  </p>
  <h2 class="match-section__title" data-slot="title">{build_title(player_a, player_b)}</h2>
  <p class="match-section__summary" data-slot="summary">{html_escape(summary)}</p>
  <div class="match-overview">
    <div class="match-overview__item">
      <span class="match-overview__label">Snabbkoll</span>
      <strong data-slot="snapshot">{html_escape(snapshot)}</strong>
    </div>
    <div class="match-overview__item">
      <span class="match-overview__label">Matchprofil</span>
      <strong data-slot="match-profile">{html_escape(profile)}</strong>
    </div>
    <div class="match-overview__item">
      <span class="match-overview__label">Dagsläge</span>
      <strong data-slot="risk-flag">{html_escape(risk_flag)}</strong>
    </div>
  </div>
  <div class="match-meta">
    <div class="match-meta__item">Nyckelsvar<strong data-slot="key-answer">{html_escape(key_answer)}</strong></div>
    <div class="match-meta__item">YTD<strong data-slot="record">{html_escape(f"{name_a} {player_a.get('ytd_wins', 0)}-{player_a.get('ytd_losses', 0)} · {name_b} {player_b.get('ytd_wins', 0)}-{player_b.get('ytd_losses', 0)}")}</strong></div>
    <div class="match-meta__item">
      <span data-slot="surface-label">{html_escape(f"{surface_sv.capitalize()}profil")}</span><strong data-slot="surface-value">{html_escape(surface_line)}</strong>
    </div>
  </div>
  <article class="match-block match-block--primary match-block--odds">
    <p class="match-block__label">Odds</p>
    <table class="odds-table" data-slot="odds-table">{odds_table}</table>
    <p class="odds-callout" data-slot="betting-idea">{betting}</p>
  </article>
  <div class="match-body">
    <div class="match-copy">
      <article class="match-block match-block--kelly">
        <p class="match-block__label">Kelly</p>
        <p data-slot="kelly-intro">{html_escape(f"Förslag på bets enligt Kelly-modellen. {name_a} mot {name_b}.")}</p>
        <table class="mini-table mini-table--kelly" data-slot="kelly-table">{kelly_table}</table>
        <p class="table-note" data-slot="kelly-note">Förslagen utgår från en bankrulle på 1000 kr och jämför modellens sannolikhet med Svenska Spels odds. Kelly är aggressivt, så 1/2, 1/4 och 1/8 visar nedskalade insatser för samma edge.</p>
      </article>
      <article class="match-block match-block--play">
        <p class="match-block__label">Spelbild</p>
        <p data-slot="play-pattern">{html_escape(play_pattern)}</p>
      </article>
      <article class="match-block match-block--form">
        <p class="match-block__label">Form och historik</p>
        <p data-slot="form-history">{html_escape(form_history)}</p>
      </article>
      <article class="match-block match-block--win-rate">
        <p class="match-block__label">Vinstprocent</p>
        <table class="mini-table" data-slot="win-rate-table">{win_rate_table}</table>
        <p class="table-note" data-slot="win-rate-note">Varje ruta visar total vinstprocent / vinstprocent mot bättre rankade spelare under samma period.</p>
      </article>
      <article class="match-block match-block--recent-results">
        <p class="match-block__label">Senaste resultat</p>
        <div class="match-subsections match-subsections--stacked">
          <p class="match-subsection__title" data-slot="recent-results-player-a-title">{html_escape(name_a)}</p>
          <table class="mini-table mini-table--recent-results" data-slot="recent-results-player-a">{recent_a_table}</table>
          <p class="match-subsection__title" data-slot="recent-results-player-b-title">{html_escape(name_b)}</p>
          <table class="mini-table mini-table--recent-results" data-slot="recent-results-player-b">{recent_b_table}</table>
        </div>
      </article>
      <article class="match-block match-block--head-to-head">
        <p class="match-block__label">Head-to-head</p>
        <table class="mini-table mini-table--head-to-head" data-slot="head-to-head">{h2h_table}</table>
      </article>
      <article class="match-block match-block--status">
        <p class="match-block__label">Skador och dagsläge</p>
        <p data-slot="status">{html_escape(status_text)}</p>
      </article>
      <article class="match-block match-block--market">
        <p class="match-block__label">Marknad och modell</p>
        <p data-slot="market-model">{html_escape(market_model_text)}</p>
      </article>
      <article class="match-block match-block--decider">
        <p class="match-block__label">Det avgör</p>
        <p data-slot="decider">{html_escape(decider)}</p>
      </article>
    </div>
  </div>
</section>""".strip()


def main() -> None:
    now = datetime.now(STOCKHOLM)
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    section_template, page = extract_match_template(template)

    raw_matches = fetch_json("/api/oddset")
    matches = [m for m in raw_matches if m.get("state") == "upcoming"]
    matches.sort(key=lambda row: (row.get("start") or "", row.get("tournament") or "", row.get("playerA", {}).get("name") or ""))

    calendar = fetch_json("/api/events/calendar")["events"]
    tournament_map = {event["location"].split(",")[0]: event for event in calendar if event.get("location")}
    tournament_map.update({event["name"].replace("Mutua ", "").replace(" Open", ""): event for event in calendar})

    player_ids = sorted({p["id"] for m in matches for p in (m["playerA"], m["playerB"]) if p.get("id")})
    if not player_ids:
        raise RuntimeError("No player ids found on the current card")

    ids_sql = ", ".join(sql_quote(player_id) for player_id in player_ids)
    player_rows = run_query(
        f"""
        SELECT id, name, country, rank, ytd_wins, ytd_losses,
               serve_rating, return_rating, pressure_rating,
               elo_rank, elo_rank_hard, elo_rank_clay, elo_rank_grass,
               hard_factor, clay_factor, grass_factor
        FROM players
        WHERE id IN ({ids_sql})
        """
    )
    players = {row["id"]: row for row in player_rows}

    match_rows = run_query(
        f"""
        SELECT DATE_FORMAT(e.date, '%Y-%m-%d') AS date,
               e.name AS event_name,
               e.surface AS surface,
               m.winner AS winner_id,
               pw.name AS winner_name,
               m.winner_rank AS winner_rank,
               m.loser AS loser_id,
               pl.name AS loser_name,
               m.loser_rank AS loser_rank,
               m.score AS score
        FROM matches m
        JOIN events e ON e.id = m.event
        LEFT JOIN players pw ON pw.id = m.winner
        LEFT JOIN players pl ON pl.id = m.loser
        WHERE m.status = 'Completed'
          AND e.date >= DATE_SUB(CURDATE(), INTERVAL 730 DAY)
          AND (m.winner IN ({ids_sql}) OR m.loser IN ({ids_sql}))
        ORDER BY e.date DESC, m.id DESC
        """
    )
    all_matches = [
        PlayerMatch(
            date=row["date"],
            event_name=row["event_name"],
            surface=row.get("surface"),
            winner_id=row["winner_id"],
            winner_name=row["winner_name"],
            winner_rank=row.get("winner_rank"),
            loser_id=row["loser_id"],
            loser_name=row["loser_name"],
            loser_rank=row.get("loser_rank"),
            score=row.get("score"),
        )
        for row in match_rows
    ]
    matches_by_player: dict[str, list[PlayerMatch]] = defaultdict(list)
    for m in all_matches:
        matches_by_player[m.winner_id].append(m)
        matches_by_player[m.loser_id].append(m)

    odds_cache: dict[tuple[str, str, str], dict[str, Any] | None] = {}
    surface_counts = Counter()
    sections = []

    for match in matches:
        tournament_name = match["tournament"]
        tournament = next((event for event in calendar if tournament_name.lower() in event.get("name", "").lower() or tournament_name.lower() in event.get("location", "").lower()), None)
        if not tournament:
            tournament = {"name": tournament_name, "type": "ATP", "surface": "Clay"}
        surface = normalize_surface(tournament.get("surface") or "Clay")
        surface_counts[surface.lower()] += 1
        player_a = players[match["playerA"]["id"]]
        player_b = players[match["playerB"]["id"]]
        odds_key = (player_a["id"], player_b["id"], surface.lower())
        if odds_key not in odds_cache:
            try:
                odds_cache[odds_key] = fetch_json("/api/odds", params={"playerA": player_a["id"], "playerB": player_b["id"], "surface": surface.lower()})
            except Exception:
                odds_cache[odds_key] = None
        sections.append(render_section(section_template, match, player_a, player_b, tournament, matches_by_player, all_matches, odds_cache[odds_key], now))

    dominant_surface = surface_counts.most_common(1)[0][0] if surface_counts else "hard"
    page = replace_placeholder(page, "themeClass", f"theme-{dominant_surface}")
    page = replace_placeholder(page, "pageTitle", "Tennis Daily")
    page = replace_placeholder(page, "pageDescription", "Daglig ATP-upplaga med matcher, form, odds och dagsläge.")
    page = replace_placeholder(page, "railItems", f"<span>Tennis Daily</span><span>ATP Tennis</span><span>Uppdaterad {now.strftime('%H.%M')}</span>")
    page = replace_placeholder(page, "title", "Tennis Daily")
    page = replace_placeholder(page, "dateLine", format_date_long(now))
    page = replace_placeholder(page, "matchSections", "".join(sections))
    page = replace_placeholder(page, "footerNote", "Editionen bygger på Svenska Spels ATP-kort, tennis.egelberg.se, ATP:s Madrid-scheman och färska ATP-notiser där dagsläget faktiskt påverkar matchläsningen.")

    OUTPUT_PATH.write_text(page, encoding="utf-8")
    print(json.dumps({"matches_written": len(sections), "output": str(OUTPUT_PATH)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
