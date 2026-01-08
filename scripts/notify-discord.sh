#!/bin/bash
# Discord Webhook通知スクリプト
# 使用方法: ./notify-discord.sh "メッセージ"

set -e

MESSAGE="$1"

if [ -z "$DISCORD_WEBHOOK_URL" ]; then
  echo "Error: DISCORD_WEBHOOK_URL is not set"
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

# Discord Webhookに送信
curl -s -X POST "$DISCORD_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d "{\"content\": $ESCAPED_MESSAGE}" \
  && echo "Discord notification sent successfully" \
  || echo "Failed to send Discord notification"
