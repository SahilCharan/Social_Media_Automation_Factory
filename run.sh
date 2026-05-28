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

# ── Resolve channel ───────────────────────────────────────────────────────────
case "${PM,,}" in
  kavitha) CHANNEL_ID="${SLACK_KAVITHA_CHANNEL:?SLACK_KAVITHA_CHANNEL not set}" ;;
  muskan)  CHANNEL_ID="${SLACK_MUSKAN_CHANNEL:?SLACK_MUSKAN_CHANNEL not set}" ;;
  *)       echo "ERROR: Unknown PM '$PM'. Use kavitha or muskan."; exit 1 ;;
esac

# ── Render HTML ───────────────────────────────────────────────────────────────
TMPDIR_WORK=$(mktemp -d)
trap "rm -rf $TMPDIR_WORK" EXIT

echo "→ Rendering HTML report..."
HTML_PATH=$(python3 "$SCRIPT_DIR/render.py" "$JSON_INPUT" "$TMPDIR_WORK/${PM}_${REPORT_TYPE}_report.html")

echo "→ HTML written to: $HTML_PATH"

# ── Upload to Slack ───────────────────────────────────────────────────────────
TYPE_LABEL=$(echo "$REPORT_TYPE" | tr '[:lower:]' '[:upper:]')
PM_LABEL=$(echo "$PM" | sed 's/./\u&/')
MSG="📊 WorkinX ${TYPE_LABEL} Report — ${PM_LABEL} | $(date +'%d %b %Y')"

bash "$SCRIPT_DIR/upload_slack.sh" "$HTML_PATH" "$CHANNEL_ID" "$MSG"

echo "✅ Done: $PM $REPORT_TYPE report delivered to Slack."
