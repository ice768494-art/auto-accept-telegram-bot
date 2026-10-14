import logging
import json
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ChatJoinRequestHandler, ContextTypes

# Enable logging to see activity in the console
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# Replace with your actual Bot Token from @BotFather
TOKEN = "YOUR_BOT_TOKEN_HERE"
FILE_NAME = "approved_users.json"

def save_user_locally(user_id, username, first_name):
    """Saves approved users to a local JSON file."""
    data = []
    
    # Load existing records if the file already exists
    if os.path.exists(FILE_NAME):
        with open(FILE_NAME, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
                
    # Check if user is already saved
    user_entry = {"user_id": user_id, "username": username, "first_name": first_name}
    if not any(u["user_id"] == user_id for u in data):
        data.append(user_entry)
        with open(FILE_NAME, "w") as f:
            json.dump(data, f, indent=4)
        print(f"Saved user {first_name} ({user_id}) to {FILE_NAME}")

async def auto_accept(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Automatically approves chat join requests and saves user data locally."""
    join_request = update.chat_join_request
    user = join_request.from_user
    
    try:
        # 1. Approve the join request
        await context.bot.approve_chat_join_request(
            chat_id=join_request.chat.id,
            user_id=user.id
        )
        print(f"Approved join request for: {user.first_name} (ID: {user.id})")
        
        # 2. Save user details to local JSON file
        save_user_locally(user.id, user.username, user.first_name)
        
    except Exception as e:
        print(f"Failed to process request for {user.id}: {e}")

def main() -> None:
    # Build the application
    application = ApplicationBuilder().token(TOKEN).build()

    # Register the handler for chat join requests
    application.add_handler(ChatJoinRequestHandler(auto_accept))

    print("Bot is running and listening for join requests...")
    # Start polling
    application.run_polling()

if __name__ == "__main__":
    main()
