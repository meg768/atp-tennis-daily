#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CODEX_HOME_DIR="${CODEX_HOME:-$HOME/.codex}"
SCAN_COMMAND="atp-tennis-daily-scan"
PUBLISH_DIR="/var/www/html/tennis-daily"
TIMEZONE="Europe/Stockholm"
PUBLISH=false
DAILY_TIME=""

if [[ -f "$REPO_DIR/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$REPO_DIR/.env"
  set +a
fi

PUSHOVER_TOKEN="${PUSHOVER_TOKEN:-}"
PUSHOVER_USER="${PUSHOVER_USER:-}"
PUSHOVER_DEVICE="${PUSHOVER_DEVICE:-}"
PUSHOVER_SOUND="${PUSHOVER_SOUND:-}"
LAST_RUN_MESSAGE=""
LAST_RUN_TOKENS=""
PUSHOVER_WARNING_SHOWN=false

usage() {
  cat <<'EOF'
Usage: ./run.sh [--publish] [--daily HH:MM]

  --publish       Copy editions/latest.html to the web root as index.html after each scan
  --daily HH:MM   Wait for the next daily run at HH:MM in Europe/Stockholm

Defaults:
  publish is off
  daily scheduling is off, so the script runs one scan and exits
EOF
}

is_gnu_date() {
  date --version >/dev/null 2>&1
}

set_last_run_message() {
  LAST_RUN_MESSAGE="$1"
}

set_last_run_tokens() {
  LAST_RUN_TOKENS="$1"
}

token_suffix() {
  local tokens="$1"

  if [[ -z "$tokens" ]]; then
    return 0
  fi

  printf ' Tokens: %s.' "$tokens"
}

warn_pushover_unavailable() {
  local reason="$1"

  if [[ "$PUSHOVER_WARNING_SHOWN" == "true" ]]; then
    return 0
  fi

  echo "Pushover unavailable: $reason" >&2
  PUSHOVER_WARNING_SHOWN=true
}

extract_codex_token_usage_since() {
  local marker_file="$1"
  local sessions_dir="$CODEX_HOME_DIR/sessions"

  if [[ ! -d "$sessions_dir" ]]; then
    return 0
  fi

  python3 - "$REPO_DIR" "$sessions_dir" "$marker_file" <<'PY'
import json
import sys
from pathlib import Path

repo_dir = sys.argv[1]
sessions_dir = Path(sys.argv[2])
marker_file = Path(sys.argv[3])
try:
    marker_mtime = marker_file.stat().st_mtime
except Exception:
    marker_mtime = None

paths = []
if marker_mtime is not None:
    for path in sessions_dir.rglob("*.jsonl"):
        try:
            if path.stat().st_mtime > marker_mtime:
                paths.append(path)
        except Exception:
            continue

best = None

for path in paths:
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        continue

    if repo_dir not in text:
        continue

    score = 2 if "atp-tennis-daily-scan" in text else 0
    latest_timestamp = ""
    latest_tokens = None

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        try:
            obj = json.loads(line)
        except Exception:
            continue

        if obj.get("type") != "event_msg":
            continue

        payload = obj.get("payload") or {}
        if payload.get("type") != "token_count":
            continue

        info = payload.get("info") or {}
        usage = info.get("last_token_usage") or info.get("total_token_usage") or {}
        tokens = usage.get("total_tokens")
        if not isinstance(tokens, int):
            continue

        latest_timestamp = obj.get("timestamp") or latest_timestamp
        latest_tokens = tokens

    if latest_tokens is None:
        continue

    candidate = (score, latest_timestamp, latest_tokens)
    if best is None or candidate > best:
        best = candidate

if best is not None:
    print(f"{best[2]:,}")
PY
}

check_pushover_before_scan() {
  if [[ -z "$PUSHOVER_TOKEN" || -z "$PUSHOVER_USER" ]]; then
    warn_pushover_unavailable "missing PUSHOVER_TOKEN or PUSHOVER_USER before scan start."
    return 0
  fi

  if ! command -v curl >/dev/null 2>&1; then
    warn_pushover_unavailable "curl is not installed before scan start."
    return 0
  fi
}

send_pushover() {
  local title="$1"
  local message="$2"
  local priority="${3:-0}"

  if [[ -z "$PUSHOVER_TOKEN" || -z "$PUSHOVER_USER" ]]; then
    warn_pushover_unavailable "missing PUSHOVER_TOKEN or PUSHOVER_USER."
    return 0
  fi

  if ! command -v curl >/dev/null 2>&1; then
    warn_pushover_unavailable "curl is not installed."
    return 0
  fi

  local curl_args=(
    -fsS
    --retry 2
    --max-time 10
    -F "token=$PUSHOVER_TOKEN"
    -F "user=$PUSHOVER_USER"
    -F "title=$title"
    -F "message=$message"
    -F "priority=$priority"
  )

  if [[ -n "$PUSHOVER_DEVICE" ]]; then
    curl_args+=(-F "device=$PUSHOVER_DEVICE")
  fi

  if [[ -n "$PUSHOVER_SOUND" ]]; then
    curl_args+=(-F "sound=$PUSHOVER_SOUND")
  fi

  if ! curl "${curl_args[@]}" https://api.pushover.net/1/messages.json >/dev/null; then
    warn_pushover_unavailable "request to api.pushover.net failed."
  fi
}

current_epoch() {
  TZ="$TIMEZONE" date +%s
}

target_epoch_today() {
  local target_time="$1"
  if is_gnu_date; then
    TZ="$TIMEZONE" date -d "$(TZ="$TIMEZONE" date +%F) ${target_time}:00" +%s
  else
    TZ="$TIMEZONE" date -j -f "%Y-%m-%d %H:%M:%S" "$(TZ="$TIMEZONE" date +%F) ${target_time}:00" +%s
  fi
}

next_daily_sleep_seconds() {
  local target_time="$1"
  local now_epoch target_epoch
  now_epoch="$(current_epoch)"
  target_epoch="$(target_epoch_today "$target_time")"

  if (( now_epoch >= target_epoch )); then
    target_epoch=$((target_epoch + 86400))
  fi

  echo $((target_epoch - now_epoch))
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --publish)
      PUBLISH=true
      shift
      ;;
    --daily)
      if [[ $# -lt 2 ]]; then
        echo "Missing value for --daily" >&2
        usage >&2
        exit 1
      fi
      DAILY_TIME="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -n "$DAILY_TIME" ]] && ! [[ "$DAILY_TIME" =~ ^([01][0-9]|2[0-3]):([0-5][0-9])$ ]]; then
  echo "--daily must be in HH:MM format" >&2
  exit 1
fi

run_scan() {
  local session_marker=""
  local token_usage=""

  mkdir -p "$REPO_DIR/.codex"
  mkdir -p "$REPO_DIR/editions"

  set_last_run_tokens ""
  session_marker="$(mktemp "$REPO_DIR/.codex/codex-session-marker.XXXXXX")"

  if ! codex exec --sandbox danger-full-access -C "$REPO_DIR" "$SCAN_COMMAND" < /dev/null; then
    token_usage="$(extract_codex_token_usage_since "$session_marker" 2>/dev/null || true)"
    set_last_run_tokens "$token_usage"
    rm -f "$session_marker"
    set_last_run_message "Scan command failed.$(token_suffix "$token_usage")"
    echo "Scan command failed." >&2
    return 1
  fi

  token_usage="$(extract_codex_token_usage_since "$session_marker" 2>/dev/null || true)"
  set_last_run_tokens "$token_usage"
  rm -f "$session_marker"

  if [[ "$PUBLISH" == "true" ]]; then
    mkdir -p "$PUBLISH_DIR"
    cp "$REPO_DIR/editions/latest.html" "$PUBLISH_DIR/index.html"
  fi

  set_last_run_message "Tennis Daily klar. Publish: ${PUBLISH}.$(token_suffix "$token_usage")"
}

run_once() {
  check_pushover_before_scan

  if run_scan; then
    send_pushover "Tennis Daily klar" "${LAST_RUN_MESSAGE:-Tennis Daily klar.}" 0
    return 0
  fi

  local exit_code=$?
  send_pushover "Tennis Daily fel" "${LAST_RUN_MESSAGE:-Tennis Daily misslyckades.}" 1
  return "$exit_code"
}

if [[ -z "$DAILY_TIME" ]]; then
  run_once
  exit 0
fi

while true; do
  sleep "$(next_daily_sleep_seconds "$DAILY_TIME")"
  run_once
done
