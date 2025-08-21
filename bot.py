import os
import json
from telegram import Update, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    InlineQueryHandler,
    filters,
    ContextTypes
)

# File to store responses
RESPONSES_FILE = "responses.json"

# Admin Telegram ID (replace with your ID after running /start once)
ADMIN_ID = 7273895542

# Load responses from file
def load_responses():
    try:
        with open(RESPONSES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

# Save responses to file
def save_responses(responses):
    with open(RESPONSES_FILE, "w", encoding="utf-8") as f:
        json.dump(responses, f, ensure_ascii=False, indent=2)

# Global dictionary
responses = load_responses()

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    await update.message.reply_text(
        f"Hello! Send a code like 001, 002 etc.\n"
        f"Your Telegram ID is: {user_id}"
    )

# Add new code-response (Admin only)
async def add_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 You are not allowed to use this command.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /add <code> <message>")
        return

    code = context.args[0]
    message = " ".join(context.args[1:])

    responses[code] = message
    save_responses(responses)

    await update.message.reply_text(f"✅ Added response for code {code}")

# Delete a code-response (Admin only)
async def delete_response(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 You are not allowed to use this command.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Usage: /delete <code>")
        return

    code = context.args[0]
    if code in responses:
        del responses[code]
        save_responses(responses)
        await update.message.reply_text(f"🗑️ Deleted response for code {code}")
    else:
        await update.message.reply_text("❌ Code not found.")

# List all codes
async def list_codes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if responses:
        codes_list = "\n".join([f"- {c}" for c in responses.keys()])
        await update.message.reply_text(f"📋 Available codes:\n{codes_list}")
    else:
        await update.message.reply_text("📭 No codes available yet.")

# Handle normal messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = update.message.text.strip()
    if user_text in responses:
        await update.message.reply_text(responses[user_text])
    else:
        await update.message.reply_text("❌ Code not recognized.")

# Inline query (search by code)
async def inline_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.inline_query.query.strip()

    results = []
    if query in responses:
        results.append(
            InlineQueryResultArticle(
                id=query,
                title=f"Code {query}",
                description=responses[query][:50] + ("..." if len(responses[query]) > 50 else ""),
                input_message_content=InputTextMessageContent(responses[query])
            )
        )

    await update.inline_query.answer(results, cache_time=0)

def main():
    TOKEN = os.getenv("BOT_TOKEN")  # Token from Render Environment Variables
    if not TOKEN:
        print("❌ BOT_TOKEN not found! Set it in environment variables.")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add_response))
    app.add_handler(CommandHandler("delete", delete_response))
    app.add_handler(CommandHandler("list", list_codes))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(InlineQueryHandler(inline_query))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
