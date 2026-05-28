#!/usr/bin/env bash
# upload_slack.sh — Upload HTML report to Slack channel
# Usage: bash upload_slack.sh <html_file> <channel_id> "<message_text>"
# Requires: SLACK_BOT_TOKEN env var
#
# Uses Slack's current (non-deprecated) 3-step upload flow:
#   1. files.getUploadURLExternal  → get upload URL + file_id
#   2. PUT to upload URL           → upload file bytes
#   3. files.completeUploadExternal → share to channel

set -euo pipefail

HTML_FILE="${1:?Usage: $0 <html_file> <channel_id> <message>}"
CHANNEL_ID="${2:?Missing channel_id}"
MESSAGE="${3:-WorkinX PM Report}"
TOKEN="${SLACK_BOT_TOKEN:?SLACK_BOT_TOKEN env var not set}"

FILENAME=$(basename "$HTML_FILE")
FILESIZE=$(wc -c < "$HTML_FILE")

echo "→ Step 1: Getting Slack upload URL for $FILENAME ($FILESIZE bytes)..."
STEP1=$(curl -s -X POST "https://slack.com/api/files.getUploadURLExternal" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "filename=$FILENAME" \
  --data-urlencode "length=$FILESIZE")

UPLOAD_URL=$(echo "$STEP1" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['upload_url'])")
FILE_ID=$(echo "$STEP1"    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['file_id'])")

if [[ -z "$UPLOAD_URL" || "$UPLOAD_URL" == "None" ]]; then
  echo "ERROR: Could not get upload URL. Response: $STEP1"
  exit 1
fi

echo "→ Step 2: Uploading file bytes..."
curl -s -X POST "$UPLOAD_URL" \
  -H "Content-Type: text/html" \
  --data-binary "@$HTML_FILE" > /dev/null

echo "→ Step 3: Completing upload to channel $CHANNEL_ID..."
STEP3=$(curl -s -X POST "https://slack.com/api/files.completeUploadExternal" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"files\": [{\"id\": \"$FILE_ID\", \"title\": \"$FILENAME\"}],
    \"channel_id\": \"$CHANNEL_ID\",
    \"initial_comment\": \"$MESSAGE\"
  }")

OK=$(echo "$STEP3" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('ok','false'))")
if [[ "$OK" != "True" && "$OK" != "true" ]]; then
  echo "ERROR: Upload complete step failed. Response: $STEP3"
  exit 1
fi

echo "✅ Report uploaded to Slack channel $CHANNEL_ID successfully."
