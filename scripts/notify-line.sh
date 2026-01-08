#!/bin/bash
# LINE Messaging API通知スクリプト
# 使用方法: ./notify-line.sh "メッセージ"

set -e

MESSAGE="$1"

if [ -z "$LINE_CHANNEL_ACCESS_TOKEN" ]; then
  echo "Error: LINE_CHANNEL_ACCESS_TOKEN is not set"
  exit 1
fi

if [ -z "$LINE_USER_ID" ]; then
  echo "Error: LINE_USER_ID is not set"
  exit 1
fi

if [ -z "$MESSAGE" ]; then
  echo "Error: Message is required"
  exit 1
fi

# JSONエスケープ
escape_json() {
  printf '%s' "$1" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))'
}

ESCAPED_MESSAGE=$(escape_json "$MESSAGE")

# LINE Messaging APIに送信
curl -s -X POST "https://api.line.me/v2/bot/message/push" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $LINE_CHANNEL_ACCESS_TOKEN" \
  -d "{
    \"to\": \"$LINE_USER_ID\",
    \"messages\": [
      {
        \"type\": \"text\",
        \"text\": $ESCAPED_MESSAGE
      }
    ]
  }" \
  && echo "LINE notification sent successfully" \
  || echo "Failed to send LINE notification"
