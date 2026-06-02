#!/usr/bin/env bash
# run.sh — WorkinX PM Report Runner
# Usage: bash run.sh <pm_name> <report_type> <json_input_file>
#   pm_name:     kavitha | muskan
#   report_type: morning | eod
#   json_input:  path to Claude's JSON output (or - for stdin)
#
# Env vars required:
#   SLACK_BOT_TOKEN        — xoxb-... Slack bot token
#   SLACK_KAVITHA_CHANNEL  — Kavitha's Slack channel ID (e.g. C0XXXXXX)
#   SLACK_MUSKAN_CHANNEL   — Muskan's Slack channel ID
#   SLACK_FOUNDERS_WEBHOOK — Founders Slack incoming webhook URL (for final summary)

set -euo pipefail

PM="${1:?Usage: $0 <kavitha|muskan> <morning|eod> <json_file>}"
REPORT_TYPE="${2:?Missing report_type: morning|eod}"
JSON_INPUT="${3:?Missing json_input file or -}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Validate args ─────────────────────────────────────────────────────────────
case "${REPORT_TYPE,,}" in
  morning|eod) ;;
  *) echo "ERROR: Unknown report_type '$REPORT_TYPE'. Use morning or eod." >&2; exit 1 ;;
esac

if [[ "$JSON_INPUT" != "-" && ! -s "$JSON_INPUT" ]]; then
  echo "ERROR: JSON input '$JSON_INPUT' does not exist or is empty" >&2
  exit 1
fi
if [[ "$JSON_INPUT" != "-" ]]; then
  python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$JSON_INPUT" \
    || { echo "ERROR: '$JSON_INPUT' is not valid JSON" >&2; exit 1; }
fi

# ── Resolve channel ───────────────────────────────────────────────────────────
case "${PM,,}" in
  kavitha) CHANNEL_ID="${SLACK_KAVITHA_CHANNEL:?SLACK_KAVITHA_CHANNEL not set}" ;;
  muskan)  CHANNEL_ID="${SLACK_MUSKAN_CHANNEL:?SLACK_MUSKAN_CHANNEL not set}" ;;
  *)       echo "ERROR: Unknown PM '$PM'. Use kavitha or muskan." >&2; exit 1 ;;
esac

: "${SLACK_BOT_TOKEN:?SLACK_BOT_TOKEN not set}"

# ── Pre-flight: Slack auth must work before we render anything ────────────────
AUTH=$(curl -sS --fail-with-body "https://slack.com/api/auth.test" \
  -H "Authorization: Bearer $SLACK_BOT_TOKEN") \
  || { echo "ERROR: Slack auth.test HTTP call failed" >&2; exit 1; }
AUTH_OK=$(echo "$AUTH" | python3 -c "import sys,json;print(json.load(sys.stdin).get('ok',False))")
if [[ "$AUTH_OK" != "True" ]]; then
  echo "ERROR: Slack auth.test failed: $AUTH" >&2
  exit 1
fi

# ── Render HTML ───────────────────────────────────────────────────────────────
TMPDIR_WORK=$(mktemp -d)
trap "rm -rf $TMPDIR_WORK" EXIT

echo "→ Rendering HTML report..."
HTML_PATH=$(python3 "$SCRIPT_DIR/render.py" "$JSON_INPUT" "$TMPDIR_WORK/${PM}_${REPORT_TYPE}_report.html")
[[ -s "$HTML_PATH" ]] || { echo "ERROR: render.py produced no output at $HTML_PATH" >&2; exit 1; }

echo "→ HTML written to: $HTML_PATH ($(wc -c < "$HTML_PATH") bytes)"

# ── Upload to Slack ───────────────────────────────────────────────────────────
TYPE_LABEL=$(echo "$REPORT_TYPE" | tr '[:lower:]' '[:upper:]')
PM_LABEL=$(echo "$PM" | sed 's/./\u&/')
MSG="📊 WorkinX ${TYPE_LABEL} Report — ${PM_LABEL} | $(date +'%d %b %Y')"

bash "$SCRIPT_DIR/upload_slack.sh" "$HTML_PATH" "$CHANNEL_ID" "$MSG"

echo "✅ Done: $PM $REPORT_TYPE report delivered to Slack."
