#!/usr/bin/env bash
# קריאה ל־API של צמרת.
#   scripts/zameret.sh '{"action":"me"}'
#   scripts/zameret.sh --upload <file> [name]      # files.upload (בינארי)
# המפתח: משתנה הסביבה ZAMERET_API_KEY, ואם אין — הקובץ ~/.config/zameret/key (מחוץ לריפו).
# לא להדפיס את המפתח ולא לשמור אותו בתוך הריפו.
set -euo pipefail
URL="https://zameres.base44.app/api/apps/6ad66dc9b84e0b844217b719/functions/agent-api"
KEY_FILE="${ZAMERET_KEY_FILE:-$HOME/.config/zameret/key}"
if [[ -z "${ZAMERET_API_KEY:-}" && -r "$KEY_FILE" ]]; then
  ZAMERET_API_KEY="$(tr -d '[:space:]' < "$KEY_FILE")"
fi

if [[ "${1:-}" == "--upload" ]]; then
  file="${2:?usage: zameret.sh --upload <file> [name]}"
  name="${3:-$(basename "$file")}"
  mime="$(file -b --mime-type "$file")"
  : "${ZAMERET_API_KEY:?ZAMERET_API_KEY is not set}"
  curl -sS -X POST "$URL?action=files.upload&name=$name" -H "Content-Type: $mime" \
    -H "X-Api-Key: $ZAMERET_API_KEY" --data-binary @"$file"
  exit
fi

body="${1:?usage: zameret.sh '<json body>'}"
[[ "$body" == @* ]] && body="$(cat "${body#@}")"   # @file.json
if [[ "$body" == *'"docs"'* ]]; then
  curl -sS -X POST "$URL" -H "Content-Type: application/json" -d "$body"
else
  : "${ZAMERET_API_KEY:?ZAMERET_API_KEY is not set}"
  curl -sS -X POST "$URL" -H "Content-Type: application/json" -H "X-Api-Key: $ZAMERET_API_KEY" --data-binary "$body"
fi
