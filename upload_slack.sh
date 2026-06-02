#!/usr/bin/env bash
# upload_slack.sh — Upload HTML report to Slack channel (hardened)
# Usage: bash upload_slack.sh <html_file> <channel_id> "<message_text>"
# Requires: SLACK_BOT_TOKEN env var
#
# Uses Slack's current (non-deprecated) 3-step upload flow:
#   1. files.getUploadURLExternal  → get upload URL + file_id
#   2. POST to upload URL          → upload file bytes (MUST be POST — see note)
#   3. files.completeUploadExternal → share to channel
#
# IMPORTANT: Step 2 MUST use `curl -X POST`, NOT PUT.
# Slack's S3 upload endpoint silently accepts PUT but stores the file with
# no MIME type, making it un-openable from the Slack file viewer.
# Do not "simplify" this script by inlining curl with PUT.

set -euo pipefail

HTML_FILE="${1:?Usage: $0 <html_file> <channel_id> <message>}"
CHANNEL_ID="${2:?Missing channel_id}"
MESSAGE="${3:-WorkinX PM Report}"
TOKEN="${SLACK_BOT_TOKEN:?SLACK_BOT_TOKEN env var not set}"

# ── Pre-flight: validate the file ─────────────────────────────────────────────
[[ -f "$HTML_FILE" ]] || { echo "ERROR: File not found: $HTML_FILE" >&2; exit 1; }
[[ -s "$HTML_FILE" ]] || { echo "ERROR: File is empty: $HTML_FILE" >&2; exit 1; }
if ! head -c 200 "$HTML_FILE" | grep -qi '<!doctype\|<html'; then
  echo "ERROR: $HTML_FILE does not look like HTML (no <!DOCTYPE or <html in first 200 bytes)" >&2
  exit 1
fi

# ── Pre-flight: validate channel format ───────────────────────────────────────
if ! [[ "$CHANNEL_ID" =~ ^[CGD][A-Z0-9]+$ ]]; then
  echo "ERROR: '$CHANNEL_ID' does not look like a Slack channel ID (expected C…/G…/D…)" >&2
  exit 1
fi

FILENAME=$(basename "$HTML_FILE")
FILESIZE=$(wc -c < "$HTML_FILE")

# ── Step 1: get upload URL ────────────────────────────────────────────────────
echo "→ Step 1: Getting Slack upload URL for $FILENAME ($FILESIZE bytes)..."
STEP1=$(curl -sS --fail-with-body -X POST "https://slack.com/api/files.getUploadURLExternal" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data-urlencode "filename=$FILENAME" \
  --data-urlencode "length=$FILESIZE") || { echo "ERROR: Step 1 HTTP call failed" >&2; exit 1; }

OK1=$(echo "$STEP1" | python3 -c "import sys,json;print(json.load(sys.stdin).get('ok',False))")
if [[ "$OK1" != "True" ]]; then
  echo "ERROR: Step 1 returned not-ok. Response: $STEP1" >&2
  exit 1
fi

UPLOAD_URL=$(echo "$STEP1" | python3 -c "import sys,json;print(json.load(sys.stdin)['upload_url'])")
FILE_ID=$(echo "$STEP1"    | python3 -c "import sys,json;print(json.load(sys.stdin)['file_id'])")

[[ -n "$UPLOAD_URL" && "$UPLOAD_URL" != "None" ]] || { echo "ERROR: Empty upload_url. Response: $STEP1" >&2; exit 1; }
[[ -n "$FILE_ID"    && "$FILE_ID"    != "None" ]] || { echo "ERROR: Empty file_id. Response: $STEP1" >&2; exit 1; }

# ── Step 2: POST the file bytes ───────────────────────────────────────────────
# CRITICAL: must be POST. PUT silently stores a broken file with empty MIME.
echo "→ Step 2: Uploading file bytes (POST)..."
HTTP_CODE=$(curl -sS -o /tmp/.slack_upload_resp.$$ -w "%{http_code}" -X POST "$UPLOAD_URL" \
  -H "Content-Type: text/html" \
  --data-binary "@$HTML_FILE") || { rm -f /tmp/.slack_upload_resp.$$; echo "ERROR: Step 2 HTTP call failed" >&2; exit 1; }

if ! [[ "$HTTP_CODE" =~ ^2[0-9][0-9]$ ]]; then
  echo "ERROR: Step 2 upload returned HTTP $HTTP_CODE" >&2
  cat /tmp/.slack_upload_resp.$$ >&2 || true
  rm -f /tmp/.slack_upload_resp.$$
  exit 1
fi
rm -f /tmp/.slack_upload_resp.$$

# ── Step 3: complete upload + share to channel ────────────────────────────────
echo "→ Step 3: Completing upload to channel $CHANNEL_ID..."
PAYLOAD=$(python3 -c "
import json, sys
print(json.dumps({
    'files': [{'id': '$FILE_ID', 'title': '$FILENAME'}],
    'channel_id': '$CHANNEL_ID',
    'initial_comment': sys.argv[1],
}))
" "$MESSAGE")

STEP3=$(curl -sS --fail-with-body -X POST "https://slack.com/api/files.completeUploadExternal" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json; charset=utf-8" \
  -d "$PAYLOAD") || { echo "ERROR: Step 3 HTTP call failed" >&2; exit 1; }

OK3=$(echo "$STEP3" | python3 -c "import sys,json;print(json.load(sys.stdin).get('ok',False))")
if [[ "$OK3" != "True" ]]; then
  echo "ERROR: Step 3 returned not-ok. Response: $STEP3" >&2
  exit 1
fi

# ── Step 4: post-flight verification ──────────────────────────────────────────
# Confirm completeUploadExternal echoed back our file id, so we know the
# share-to-channel actually happened (not just that the bytes uploaded).
RETURNED_ID=$(echo "$STEP3" | python3 -c "
import sys, json
d = json.load(sys.stdin)
files = d.get('files') or []
print(files[0]['id'] if files else '')
")
if [[ "$RETURNED_ID" != "$FILE_ID" ]]; then
  echo "ERROR: Step 3 did not return our file_id. Response: $STEP3" >&2
  exit 1
fi

echo "✅ Report uploaded to Slack channel $CHANNEL_ID (file_id: $FILE_ID)"
