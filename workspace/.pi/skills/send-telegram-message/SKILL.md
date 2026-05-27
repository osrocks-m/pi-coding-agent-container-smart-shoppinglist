---
name: send-telegram-message
description: Send Telegram messages to users via the Telegram Bot API using curl. Use when the user wants to send notifications or messages via Telegram.
---

# Send Telegram Message

Send messages to Telegram users via the Telegram Bot API using curl.

## Base URL

```
https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/<METHOD>
```

read `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` from the environment variable

## Get Chat ID

First, send any message to your bot in Telegram, then run:

```bash
curl -s https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates
```

Then extract the chat ID from the JSON response (look for `"chat":{"id":TELEGRAM_CHAT_ID`). You can also use grep:

```bash
curl -s https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates | grep -o '"id":[0-9]*' | head -1 | cut -d: -f2
```

## Send Text Message

```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -d '{"chat_id": <CHAT_ID>, "text": "Your message here"}' \
  https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/sendMessage
```

## Send Message with Markdown Formatting

```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -d '{"chat_id": <CHAT_ID>, "text": "*Bold* and _italic_ text", "parse_mode": "Markdown"}' \
  https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/sendMessage
```

## Other Useful Methods

### Get Bot Info
```bash
curl https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getMe
```

### Get Updates
```bash
curl -s https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/getUpdates
```

**Important:** Do not use jq or other JSON processing tools as they may not be available. Use raw curl output only.

### Send Silent Message (no notification)
```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -d '{"chat_id": <CHAT_ID>, "text": "Silent message", "disable_notification": true}' \
  https://api.telegram.org/bot<TELEGRAM_BOT_TOKEN>/sendMessage
```

## Environment Variables (Optional)

Set these to avoid repeating tokens:

```bash
export TELEGRAM_BOT_TOKEN="<TELEGRAM_BOT_TOKEN>"
export TELEGRAM_CHAT_ID="<CHAT_ID>"
```

Then reference them in commands:

```bash
curl -X POST \
  -H 'Content-Type: application/json' \
  -d "{\"chat_id\": $TELEGRAM_CHAT_ID, \"text\": \"Hello!\"}" \
  https://api.telegram.org/bot$TELEGRAM_BOT_TOKEN/sendMessage
```

## Full API Documentation

See https://core.telegram.org/bots/api for all available methods and parameters.
