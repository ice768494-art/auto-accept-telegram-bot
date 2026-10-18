# Auto Acceptor Telegram Bot

## Render setup
- Build command: `pip install -r requirements.txt`
- Start command: `python bot.py`
- Environment variables:
  - `BOT_TOKEN` = token from BotFather
  - `ADMIN_ID` = your numeric Telegram user ID (used for /stats)

Add the bot as an administrator in the target channel/group and grant permission to invite users/manage join requests. The invite link must be configured to require join requests for the bot to receive `chat_join_request` updates.

Commands: `/start`, `/ping`, `/stats`.

Note: This bot automatically approves NEW join requests it receives. Telegram's Bot API does not provide a method to list and approve every already-pending request. The JSON stats file is local storage and may reset when a Render instance is replaced.
