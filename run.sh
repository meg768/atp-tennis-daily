#!/usr/bin/env bash
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
SCAN_COMMAND="atp-tennis-daily-scan"
PUBLISH_DIR="/var/www/html/tennis-daily"
TIMEZONE="Europe/Stockholm"
PUBLISH=false
DAILY_TIME=""

usage() {
  cat <<'EOF'
Usage: ./run.sh [--publish] [--daily HH:MM]

  --publish       Publish editions/ to the web root after each scan
  --daily HH:MM   Wait for the next daily run at HH:MM in Europe/Stockholm

Defaults:
  publish is off
  daily scheduling is off, so the script runs one scan and exits
EOF
}

is_gnu_date() {
  date --version >/dev/null 2>&1
}

file_mtime() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    return 1
  fi

  if stat --version >/dev/null 2>&1; then
    stat -c %Y "$file"
  else
    stat -f %m "$file"
  fi
}

file_fingerprint() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    return 1
  fi

  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$file" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$file" | awk '{print $1}'
  else
    cksum "$file" | awk '{print $1 ":" $2}'
  fi
}

snapshot_marker() {
  local file="$1"
  if [[ ! -f "$file" ]]; then
    return 1
  fi

  grep -Eo 'Snapshot [0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2} [A-Z]+' "$file" | head -n 1
}

validate_rendered_edition() {
  local file="$1"

  if [[ ! -s "$file" ]]; then
    echo "Edition file is missing or empty: $file" >&2
    return 1
  fi

  if ! grep -q '<!DOCTYPE html>' "$file"; then
    echo "Edition file does not look like standalone HTML: $file" >&2
    return 1
  fi

  if ! grep -q 'Tennis Daily' "$file"; then
    echo "Edition file is missing the expected title marker: $file" >&2
    return 1
  fi

  if ! grep -q 'Snapshot ' "$file"; then
    echo "Edition file is missing a visible snapshot marker: $file" >&2
    return 1
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
  local latest_file="$REPO_DIR/editions/latest.html"
  local before_mtime=""
  local before_fingerprint=""
  local before_snapshot=""
  local after_mtime=""
  local after_fingerprint=""
  local after_snapshot=""
  local dated_count=""

  mkdir -p "$REPO_DIR/.codex"
  mkdir -p "$REPO_DIR/editions"

  before_mtime="$(file_mtime "$latest_file" 2>/dev/null || true)"
  before_fingerprint="$(file_fingerprint "$latest_file" 2>/dev/null || true)"
  before_snapshot="$(snapshot_marker "$latest_file" 2>/dev/null || true)"

  if ! codex exec --sandbox danger-full-access -C "$REPO_DIR" "$SCAN_COMMAND" < /dev/null; then
    echo "Scan command failed before edition verification." >&2
    return 1
  fi

  validate_rendered_edition "$latest_file"

  after_mtime="$(file_mtime "$latest_file" 2>/dev/null || true)"
  after_fingerprint="$(file_fingerprint "$latest_file" 2>/dev/null || true)"
  after_snapshot="$(snapshot_marker "$latest_file" 2>/dev/null || true)"

  if [[ -n "$before_mtime" ]] \
    && [[ "$after_mtime" == "$before_mtime" ]] \
    && [[ "$after_fingerprint" == "$before_fingerprint" ]] \
    && [[ "$after_snapshot" == "$before_snapshot" ]]; then
    echo "Scan finished without refreshing editions/latest.html." >&2
    return 1
  fi

  dated_count="$(find "$REPO_DIR/editions" -maxdepth 1 -type f -name '20??-??-??.html' | wc -l | tr -d ' ')"
  if [[ "$dated_count" == "0" ]]; then
    echo "Scan did not leave any dated edition files under editions/." >&2
    return 1
  fi

  if [[ "$PUBLISH" == "true" ]]; then
    mkdir -p "$PUBLISH_DIR"
    mkdir -p "$PUBLISH_DIR/editions"
    rsync -az --delete "$REPO_DIR/editions/" "$PUBLISH_DIR/editions/"
    cp "$REPO_DIR/editions/latest.html" "$PUBLISH_DIR/index.html"
    validate_rendered_edition "$PUBLISH_DIR/index.html"

    if [[ "$(file_fingerprint "$PUBLISH_DIR/index.html")" != "$after_fingerprint" ]]; then
      echo "Published index.html does not match editions/latest.html after publish." >&2
      return 1
    fi
  fi
}

if [[ -z "$DAILY_TIME" ]]; then
  run_scan
  exit 0
fi

while true; do
  sleep "$(next_daily_sleep_seconds "$DAILY_TIME")"
  run_scan
done
