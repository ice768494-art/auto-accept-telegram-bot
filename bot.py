import os
import json
import logging
import threading

from flask import Flask
from telegram import Update
from telegram.ext import (
ApplicationBuilder,
CommandHandler,
ChatJoinRequestHandler,
ContextTypes,
)

#==================== CONFIGURATION ====================

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID", "")

if not TOKEN:
raise RuntimeError(
"BOT_TOKEN is missing! Add it to Render Environment Variables."
)

FILE_NAME = "approved_users.json"

#==================== LOGGING ====================

logging.basicConfig(
format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
level=logging.INFO,
)

logger = logging.getLogger(name)

#==================== WEB SERVER ====================

web_app = Flask(name)

@web_app.route("/")
def home():
return "Auto Acceptor Bot is running!", 200

def run_web_server():
port = int(os.getenv("PORT", "8080"))
web_app.run(host="0.0.0.0", port=port)

#==================== LOCAL JSON STORAGE ====================

def load_users():
if not os.path.exists(FILE_NAME):
return []

try:
    with open(FILE_NAME, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data if isinstance(data, list) else []

except (OSError, json.JSONDecodeError):
    logger.exception("Failed to load approved users.")
    return []

def save_user(user):
users = load_users()

if any(item.get("user_id") == user.id for item in users):
    return

users.append(
    {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
    }
)

try:
    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4)

except OSError:
    logger.exception("Failed to save approved user.")

#==================== ADMIN CHECK ====================

def is_admin(update: Update):
user = update.effective_user

return (
    user is not None
    and ADMIN_ID.isdigit()
    and user.id == int(ADMIN_ID)
)

#==================== START COMMAND ====================

async def start(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):
await update.effective_message.reply_text(
"🤖 Auto Acceptor Bot is online!\n\n"
"Available commands:\n"
"/start - Bot status\n"
"/ping - Check bot response\n"
"/stats - Approval statistics\n\n"
"New join requests are accepted automatically."
)

#==================== PING COMMAND ====================

async def ping(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):
await update.effective_message.reply_text(
"🏓 Pong! Bot is running."
)

#==================== STATS COMMAND ====================

async def stats(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):
if not is_admin(update):
await update.effective_message.reply_text(
"⛔ This command is for the bot admin only."
)
return

users = load_users()

await update.effective_message.reply_text(
    "📊 Approval Statistics\n\n"
    f"Recorded approved users: {len(users)}\n"
    "Database: Not required"
)

#==================== AUTO ACCEPT NEW REQUESTS ====================

async def auto_accept(
update: Update,
context: ContextTypes.DEFAULT_TYPE,
):
request = update.chat_join_request

if request is None:
    return

user = request.from_user

try:
    await context.bot.approve_chat_join_request(
        chat_id=request.chat.id,
        user_id=user.id,
    )

    save_user(user)

    logger.info(
        "Approved user %s (ID: %s) in chat %s",
        user.first_name,
        user.id,
        request.chat.id,
    )

except Exception:
    logger.exception(
        "Failed to approve user %s in chat %s",
        user.id,
        request.chat.id,
    )

#==================== MAIN FUNCTION ====================

def main():
# Start the Render web server.
 threading.Thread(
 target=run_web_server,
 daemon=True,
 ).start()

# Create the Telegram bot application.
application = (
    ApplicationBuilder()
    .token(TOKEN)
    .build()
)

# Register bot commands.
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ping", ping))
application.add_handler(CommandHandler("stats", stats))

# Register automatic join-request approval.
application.add_handler(
    ChatJoinRequestHandler(auto_accept)
)

logger.info("Auto Acceptor Bot is starting...")

# Start polling for Telegram updates.
application.run_polling(
    allowed_updates=[
        "message",
        "chat_join_request",
    ]
)

#==================== PROGRAM ENTRY POINT ====================

if name == "main":
main()
