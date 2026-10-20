#!/usr/bin/env bash
# Call the Zameret agent API as Mark.
#   zameret.sh docs | me            shorthand for {"action":"docs"} / {"action":"me"}
#   zameret.sh '<json body>'        any other action
# The key is read from ZAMERET_API_KEY and never printed.
set -euo pipefail

URL="https://zameres.base44.app/api/apps/6ad66dc9b84e0b844217b719/functions/agent-api"

case "${1:-}" in
  "") echo "usage: $0 docs|me|'<json>'" >&2; exit 2 ;;
  docs|me) body="{\"action\":\"$1\"}" ;;
  *) body="$1" ;;
esac

if [ "${1:-}" = "docs" ]; then
  exec curl -sS --fail-with-body -X POST "$URL" -H "Content-Type: application/json" -d "$body"
fi

if [ -z "${ZAMERET_API_KEY:-}" ]; then
  echo "ZAMERET_API_KEY is not set" >&2
  exit 1
fi

# Pass the key via a header file on stdin so it never appears in the process list.
printf 'X-Api-Key: %s\n' "$ZAMERET_API_KEY" |
  curl -sS --fail-with-body -X POST "$URL" -H "Content-Type: application/json" -H @- -d "$body"
