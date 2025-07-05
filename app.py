import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler

# === CONFIG ===
TOKEN = os.getenv("BOT_TOKEN") or "7593794682:AAEqzdMTtkzGcJLdI_SGFjRSF50q4ntlIjo"
RAILWAY_URL = os.getenv("RAILWAY_URL") or "web-production-32b2.up.railway.app"
WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"https://{RAILWAY_URL}{WEBHOOK_PATH}"

# === TELEGRAM BOT ===
app_bot = Application.builder().token(TOKEN).build()

# Comando mínimo para teste
async def start(update: Update, context):
    await update.message.reply_text("✅ Bot online!")

app_bot.add_handler(CommandHandler("start", start))

# === FLASK ===
app = Flask(__name__)

# Inicializa o bot + webhook
async def setup_bot():
    await app_bot.initialize()
    await app_bot.bot.set_webhook(url=WEBHOOK_URL)
    await app_bot.start()

asyncio.run(setup_bot())

@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app_bot.bot)
    asyncio.run(app_bot.process_update(update))
    return "OK", 200

# Health check opcional
@app.route("/")
def health():
    return "👋 Bot online", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
