#!/usr/bin/env bash
# upload_slack.sh — Upload HTML report to Slack channel
# Usage: bash upload_slack.sh <html_file> <channel_id> "<message_text>"
# Requires: SLACK_BOT_TOKEN env var
#
# Uses Slack's current (non-deprecated) 3-step upload flow:
#   1. files.getUploadURLExternal  → get upload URL + file_id
#   2. POST multipart to upload URL → upload file bytes
#   3. files.completeUploadExternal → share to channel
#
# ───────────────────────────────────────────────────────────────────────────
# CRITICAL — DO NOT REGRESS. Three failure modes encountered in production:
#   1. Step 2 multipart field name MUST be `filename`. Using `file` returns
#      "OK" but produces a record with empty mimetype that Step 3 won't share.
#   2. Step 3 MUST be form-encoded (--data-urlencode). If sent as JSON with
#      Content-Type: application/json, Slack returns ok:true but SILENTLY drops
#      channel_id — the file uploads but never shares.
#   3. Slack's upload pipeline is eventually-consistent. Even with correct
#      params, Step 3 called immediately after Step 2 returns ok:true with
#      empty channels[] — the file is in a half-processed state. Wait 2-4s
#      between Step 2 and Step 3, and verify .files[0].channels contains the
#      target channel_id. Retry Step 3 with backoff if channels[] is empty.
#   Notes:
#   • `ok:true` is NEVER a reliable success signal. The post-share check
#     (channel_id present in files[0].channels) is the only ground truth.
#   • permalink_public (slack-files.com/...) only resolves if
#     public_url_shared:true, which a bot token cannot set. Never give that
#     link to users — use permalink (workinxworkspace.slack.com/...) instead.
# ───────────────────────────────────────────────────────────────────────────

set -euo pipefail

HTML_FILE="${1:?Usage: $0 <html_file> <channel_id> <message>}"
CHANNEL_ID="${2:?Missing channel_id}"
MESSAGE="${3:-WorkinX PM Report}"
TOKEN="${SLACK_BOT_TOKEN:?SLACK_BOT_TOKEN env var not set}"

[[ -f "$HTML_FILE" ]] || { echo "ERROR: file not found: $HTML_FILE" >&2; exit 1; }

FILENAME=$(basename "$HTML_FILE")
FILESIZE=$(wc -c < "$HTML_FILE")

echo "→ Step 1: Getting Slack upload URL for $FILENAME ($FILESIZE bytes)..."
STEP1=$(curl -s -X POST "https://slack.com/api/files.getUploadURLExternal" \
  -H "Authorization: Bearer $TOKEN" \
  --data-urlencode "filename=$FILENAME" \
  --data-urlencode "length=$FILESIZE")

UPLOAD_URL=$(echo "$STEP1" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('upload_url',''))")
FILE_ID=$(echo "$STEP1"    | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('file_id',''))")

if [[ -z "$UPLOAD_URL" || -z "$FILE_ID" ]]; then
  echo "ERROR: Step 1 failed. Response: $STEP1" >&2
  exit 1
fi

echo "→ Step 2: Uploading file bytes (multipart, field name MUST be 'filename')..."
# NOTE: Slack's upload endpoint requires multipart field name `filename`. Using
# `file` (or anything else) returns "OK" but produces an incomplete file record
# (is_public:false, mimetype empty) that Step 3 refuses to share to a channel.
STEP2=$(curl -s -X POST "$UPLOAD_URL" -F "filename=@$HTML_FILE")
if [[ "$STEP2" != OK* ]]; then
  echo "ERROR: Step 2 upload failed. Response: $STEP2" >&2
  exit 1
fi

# Slack's upload pipeline is eventually-consistent: Step 2 returns "OK - <bytes>"
# but the file is not immediately shareable. Calling completeUploadExternal too
# quickly returns ok:true with empty channels[] and a half-processed orphan.
# We retry with backoff and verify channels[] contains $CHANNEL_ID.
echo "→ Step 3: Completing upload to channel $CHANNEL_ID (with retry until shared)..."
FILES_JSON="[{\"id\":\"$FILE_ID\",\"title\":\"$FILENAME\"}]"

MAX_ATTEMPTS=6
SHARED=0
for ATTEMPT in $(seq 1 $MAX_ATTEMPTS); do
  sleep $((ATTEMPT < 3 ? 2 : 4))  # 2s, 2s, 4s, 4s, 4s, 4s

  STEP3=$(curl -s -X POST "https://slack.com/api/files.completeUploadExternal" \
    -H "Authorization: Bearer $TOKEN" \
    --data-urlencode "files=$FILES_JSON" \
    --data-urlencode "channel_id=$CHANNEL_ID" \
    --data-urlencode "initial_comment=$MESSAGE")

  VERIFY=$(echo "$STEP3" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if not d.get('ok'):
    print('FAIL'); sys.exit()
files = d.get('files', [])
if not files: print('FAIL'); sys.exit()
channels = files[0].get('channels', [])
if '$CHANNEL_ID' in channels:
    print('OK ' + files[0].get('permalink', ''))
else:
    print('RETRY mimetype=' + repr(files[0].get('mimetype','')) + ' channels=' + str(channels))
")

  case "$VERIFY" in
    OK*)
      SHARED=1
      echo "✅ Report posted to Slack channel $CHANNEL_ID (attempt $ATTEMPT) — ${VERIFY#OK }"
      break
      ;;
    RETRY*)
      echo "   attempt $ATTEMPT/$MAX_ATTEMPTS: $VERIFY — Slack file not yet ready, retrying..."
      ;;
    *)
      echo "ERROR: Step 3 hard failure. Response: $STEP3" >&2
      exit 1
      ;;
  esac
done

if [[ $SHARED -ne 1 ]]; then
  echo "ERROR: File never shared to channel after $MAX_ATTEMPTS attempts." >&2
  echo "Last response: $STEP3" >&2
  exit 1
fi
