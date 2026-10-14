import os
import logging
import json
import threading
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes

# --- 1. LIGHTWEIGHT WEBSERVER FOR RENDER ---
web_app = Flask(__name__)

@web_app.route('/')
def home():
    return "Telegram Auto-Accept Bot is running!", 200

def run_web_server():
    # Render assigns a dynamic port via environment variables
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host="0.0.0.0", port=port)

# --- 2. TELEGRAM BOT SETUP ---
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

TOKEN = "8939699354:AAGRy7r9nXMBzObdXTJzCtLcCtyfs-_KkB0"  # Replace with your actual Bot Token from @BotFather
FILE_NAME = "approved_users.json"

def save_user_locally(user_id, username, first_name):
    """Saves approved users to a local JSON file."""
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
    """Automatically approves chat join requests and saves user data locally."""
    join_request = update.chat_join_request
    user = join_request.from_user
    
    try:
        # Approve the join request
        await context.bot.approve_chat_join_request(
            chat_id=join_request.chat.id,
            user_id=user.id
        )
        print(f"Approved join request for: {user.first_name} (ID: {user.id})")
        
        # Save user details locally
        save_user_locally(user.id, user.username, user.first_name)
        
    except Exception as e:
        print(f"Failed to process request for {user.id}: {e}")

def main() -> None:
    # Start the web server in a separate background thread so Render detects an open port
    threading.Thread(target=run_web_server, daemon=True).start()

    # Build the Telegram application
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(ChatJoinRequestHandler(auto_accept))

    print("Bot web service is active and listening for join requests...")
    application.run_polling()

if __name__ == "__main__":
    main()
