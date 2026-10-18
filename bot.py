import os
import json
import logging
import threading
import asyncio

from flask import Flask
from telegram import Update
from telegram.ext import (
ApplicationBuilder,
ChatJoinRequestHandler,
CommandHandler,
ContextTypes,
)

#================= WEB SERVER =================

web_app = Flask(name)

@web_app.route("/")
def home():
 return "Bot is active!", 200

def run_web_server():
 port = int(os.environ.get("PORT", 8080))
 web_app.run(host="0.0.0.0", port=port)

#================= CONFIGURATION =================

logging.basicConfig(
format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
level=logging.INFO,
)

TOKEN = os.environ.get("BOT_TOKEN")
ADMIN_ID = os.environ.get("ADMIN_ID")

if not TOKEN:
raise ValueError("BOT_TOKEN is missing from environment variables!")

FILE_NAME = "approved_users.json"

#================= LOCAL STORAGE =================

def load_users():
if not os.path.exists(FILE_NAME):
return []

try:
    with open(FILE_NAME, "r", encoding="utf-8") as file:
        return json.load(file)
except (json.JSONDecodeError, OSError):
    return []

def save_user_locally(user_id, username, first_name):
users = load_users()

if not any(user.get("user_id") == user_id for user in users):
    users.append({
        "user_id": user_id,
        "username": username,
        "first_name": first_name,
    })

    with open(FILE_NAME, "w", encoding="utf-8") as file:
        json.dump(users, file, indent=4)

#================= ADMIN CHECK =================

def is_admin(update: Update) -> bool:
if not ADMIN_ID:
return False

user = update.effective_user
return user is not None and str(user.id) == ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.effective_message.reply_text(
"🤖 Auto Acceptor Bot is running!\n\n"
"Commands:\n"
"/start - Bot status\n"
"/ping - Check uptime response\n"
"/stats - Approval statistics\n"
"/acceptall CHAT_ID - Process pending requests"
)

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
await update.effective_message.reply_text("🏓 Pong! Bot is active.")

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not is_admin(update):
await update.effective_message.reply_text("⛔ Admin only.")
return

users = load_users()

await update.effective_message.reply_text(
    f"📊 Local Approval Statistics\n\n"
    f"Recorded approvals: {len(users)}\n"
    f"Storage: {FILE_NAME}\n"
    f"Database: Not required"
)

#================= NEW REQUEST HANDLER =================

async def auto_accept(update: Update, context: ContextTypes.DEFAULT_TYPE):
request = update.chat_join_request
if request is None:
return

user = request.from_user

try:
    await context.bot.approve_chat_join_request(
        chat_id=request.chat.id,
        user_id=user.id,
    )

    save_user_locally(user.id, user.username, user.first_name)

    logging.info(
        "Approved %s (%s) in chat %s",
        user.first_name,
        user.id,
        request.chat.id,
    )

except Exception:
    logging.exception("Could not approve user %s", user.id)

#================= PENDING REQUESTS =================

async def accept_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
if not is_admin(update):
await update.effective_message.reply_text("⛔ Admin only.")
return

if not context.args:
    await update.effective_message.reply_text(
        "Usage:\n/acceptall CHAT_ID\n\n"
        "Example:\n/acceptall -1001234567890"
    )
    return

chat_id = context.args[0]

try:
    chat_id = int(chat_id)
except ValueError:
    await update.effective_message.reply_text(
        "❌ Invalid chat ID. Please provide a numeric chat ID."
    )
    return

await update.effective_message.reply_text(
    "ℹ️ Telegram's Bot API does not provide a method to list "
    "all pending join requests. This command cannot discover "
    "or bulk-approve requests that the bot has not received."
)

#================= MAIN =================

def main():
threading.Thread(target=run_web_server, daemon=True).start()

application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("ping", ping))
application.add_handler(CommandHandler("stats", stats))
application.add_handler(CommandHandler("acceptall", accept_all))

application.add_handler(ChatJoinRequestHandler(auto_accept))

logging.info("Auto Acceptor Bot starting...")

application.run_polling(
    allowed_updates=["message", "chat_join_request"]
)

if __name__ == "main":
main()
