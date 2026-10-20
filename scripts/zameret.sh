#!/usr/bin/env bash
# קריאה ל־API של צמרת. שימוש: scripts/zameret.sh '{"action":"me"}'
# המפתח נקרא ממשתנה הסביבה ZAMERET_API_KEY בלבד — לא להדפיס ולא לשמור בקבצים.
set -euo pipefail
URL="https://zameres.base44.app/api/apps/6ad66dc9b84e0b844217b719/functions/agent-api"
body="${1:?usage: zameret.sh '<json body>'}"
if [[ "$body" == *'"docs"'* ]]; then
  curl -sS -X POST "$URL" -H "Content-Type: application/json" -d "$body"
else
  : "${ZAMERET_API_KEY:?ZAMERET_API_KEY is not set}"
  curl -sS -X POST "$URL" -H "Content-Type: application/json" -H "X-Api-Key: $ZAMERET_API_KEY" -d "$body"
fi
