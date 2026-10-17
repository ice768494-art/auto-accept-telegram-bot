import os
import logging
import json
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes


web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Bot is active!", 200

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- TELEGRAM BOT LOGIC ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


TOKEN = os.environ.get("BOT_TOKEN")

if not TOKEN:
    raise ValueError("No BOT_TOKEN found in environment variables!")

FILE_NAME = "approved_users.json"

def save_user_locally(user_id, username, first_name):
    data = []
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
                
    user_entry = {"user_id": user_id, "username": username, "first_name": first_name}
    if not any(u["user_id"] == user_id for u in data):
        data.append(user_entry)
        with open(FILE_NAME, "w") as f:
            json.dump(data, f, indent=4)

async def auto_accept(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    join_request = update.chat_join_request
    user = join_request.from_user
    
    try:
        await context.bot.approve_chat_join_request(
            chat_id=join_request.chat.id,
            user_id=user.id
        )
        print(f"Approved: {user.first_name} ({user.id})")
        save_user_locally(user.id, user.username, user.first_name)
    except Exception as e:
        print(f"Error approving user {user.id}: {e}")

def main() -> None:
    threading.Thread(target=run_web_server, daemon=True).start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(ChatJoinRequestHandler(auto_accept))
    print("Bot starting...")
    application.run_polling()

if __name__ == "__main__":
    main()
