import json
import logging
import os
import threading

from flask import Flask
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ChatJoinRequestHandler,
    CommandHandler,
    ContextTypes,
)

# ==================== CONFIGURATION ====================

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_ID = os.getenv("ADMIN_ID", "").strip()
PORT = int(os.getenv("PORT", "8080"))
USERS_FILE = "approved_users.json"

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is missing! Add it in Render > Environment > Environment Variables."
    )

# ==================== LOGGING ====================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ==================== WEB SERVER ====================

web_app = Flask(__name__)


@web_app.route("/")
def home():
    return "Auto Acceptor Bot is running!", 200


def run_web_server():
    web_app.run(host="0.0.0.0", port=PORT, use_reloader=False)


# ==================== LOCAL JSON STORAGE ====================

def load_users():
    if not os.path.exists(USERS_FILE):
        return []

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        logger.exception("Could not read %s", USERS_FILE)
        return []


def save_user(user):
    users = load_users()

    if any(
        isinstance(item, dict) and item.get("user_id") == user.id
        for item in users
    ):
        return

    users.append(
        {
            "user_id": user.id,
            "username": user.username,
            "first_name": user.first_name,
        }
    )

    try:
        with open(USERS_FILE, "w", encoding="utf-8") as file:
            json.dump(users, file, indent=2, ensure_ascii=False)
    except OSError:
        logger.exception("Could not save approved user")


# ==================== ADMIN CHECK ====================

def is_admin(update: Update) -> bool:
    user = update.effective_user
    return (
        user is not None
        and ADMIN_ID.isdigit()
        and user.id == int(ADMIN_ID)
    )


# ==================== BOT COMMANDS ====================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_message:
        await update.effective_message.reply_text(
            "🤖 Auto Acceptor Bot is online!\n\n"
            "Commands:\n"
            "/start - Check bot status\n"
            "/ping - Check bot response\n"
            "/stats - Show approval statistics (admin only)\n\n"
            "New join requests are accepted automatically."
        )


async def ping(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if update.effective_message:
        await update.effective_message.reply_text("🏓 Pong! Bot is running.")


async def stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.effective_message:
        return

    if not is_admin(update):
        await update.effective_message.reply_text(
            "⛔ This command is for the bot admin only."
        )
        return

    await update.effective_message.reply_text(
        "📊 Approval Statistics\n\n"
        f"Recorded approved users: {len(load_users())}\n"
        "Storage: local JSON file"
    )


# ==================== AUTO-ACCEPT JOIN REQUESTS ====================

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
            "Approved join request: user_id=%s chat_id=%s",
            user.id,
            request.chat.id,
        )
    except Exception:
        logger.exception(
            "Failed to approve join request: user_id=%s chat_id=%s",
            user.id,
            request.chat.id,
        )


# ==================== MAIN ====================

def main():
    # Render Web Service health-check endpoint.
    threading.Thread(target=run_web_server, daemon=True).start()

    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("ping", ping))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(ChatJoinRequestHandler(auto_accept))

    logger.info("Auto Acceptor Bot is starting...")
    application.run_polling(
        allowed_updates=["message", "chat_join_request"],
        drop_pending_updates=False,
    )


if __name__ == "__main__":
    main()
