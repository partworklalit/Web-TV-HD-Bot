import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from pymongo import MongoClient

# ✅ Env vars
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
MONGO_URI = os.getenv("MONGO_URI")

# ✅ MongoDB setup
client = MongoClient(MONGO_URI)
db = client["telegram_bot"]
users_col = db["users"]
data_col = db["data"]

# ---------------- USERS SYSTEM ----------------
def add_user(user_id):
    if users_col.find_one({"user_id": user_id}) is None:
        users_col.insert_one({"user_id": user_id})

def get_all_users():
    return [u["user_id"] for u in users_col.find()]

# ---------------- DATA SYSTEM ----------------
def set_code(code, message):
    data_col.update_one({"code": code}, {"$set": {"message": message}}, upsert=True)

def get_message(code):
    record = data_col.find_one({"code": code})
    return record["message"] if record else None

def delete_code(code):
    data_col.delete_one({"code": code})

# ---------------- COMMANDS ----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    add_user(user_id)
    await update.message.reply_text(f"Hello! Send a code like 001, 002 etc.\nYour Telegram ID is: {user_id}")

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 You are not allowed.")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /add <code> <message>")
        return
    code = context.args[0]
    message = " ".join(context.args[1:])
    set_code(code, message)
    await update.message.reply_text(f"✅ Added message for code {code}")

async def delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 You are not allowed.")
        return
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /delete <code>")
        return
    code = context.args[0]
    delete_code(code)
    await update.message.reply_text(f"🗑️ Deleted message for code {code}")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id != ADMIN_ID:
        await update.message.reply_text("🚫 You are not allowed.")
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast <message>")
        return
    message = " ".join(context.args)
    count = 0
    for uid in get_all_users():
        try:
            await context.bot.send_message(chat_id=uid, text=message)
            count += 1
        except:
            pass
    await update.message.reply_text(f"📢 Broadcast sent to {count} users.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    code = update.message.text.strip()
    message = get_message(code)
    if message:
        await update.message.reply_text(message)
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
