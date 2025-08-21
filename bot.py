import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# ✅ Admin ID (apna Telegram ID yahan daalo)
ADMIN_ID = 123456789  

# ✅ Bot Token Render ke env vars se aayega
TOKEN = os.getenv("BOT_TOKEN")

# ✅ Files
DATA_FILE = "data.json"
USERS_FILE = "users.json"

# ---------------- USERS SYSTEM ----------------

def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

users = load_users()

# ---------------- DATA SYSTEM ----------------

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ---------------- COMMANDS ----------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in users:
        users.append(user_id)
        save_users(users)

    await update.message.reply_text(
        f"Hello! Send a code like 001, 002 etc.\n"
        f"Your Telegram ID is: {user_id}"
    )

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 You are not allowed.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Usage: /add <code> <message>")
        return

    code = context.args[0]
    message = " ".join(context.args[1:])
    data[code] = message
    save_data(data)
    await update.message.reply_text(f"✅ Added message for code {code}")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 You are not allowed.")
        return

    if len(context.args) < 1:
        await update.message.reply_text("Usage: /delete <code>")
        return

    code = context.args[0]
    if code in data:
        del data[code]
        save_data(data)
        await update.message.reply_text(f"🗑️ Deleted message for code {code}")
    else:
        await update.message.reply_text(f"⚠️ No message found for code {code}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("🚫 You are not allowed.")
        return

    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return

    message = " ".join(context.args)
    count = 0

    for uid in users:
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            count += 1
        except:
            pass  # skip agar user ne block kar diya hai

    await update.message.reply_text(f"📢 Broadcast sent to {count} users.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    if code in data:
        await update.message.reply_text(data[code])
    else:
        await update.message.reply_text("⚠️ Invalid code. Try again!")

# ---------------- MAIN ----------------

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("delete", delete))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
