import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application

# ✅ Token do bot e domínio
TOKEN = "7593794682:AAEqzdMTtkzGcJLdI_SGFjRSF50q4ntlIjo"
RAILWAY_URL = os.getenv("RAILWAY_URL")  # Ex: 'meubot.up.railway.app'
if not TOKEN or not RAILWAY_URL:
    raise ValueError("❌ BOT_TOKEN ou RAILWAY_URL não definidos.")

WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"https://{RAILWAY_URL}{WEBHOOK_PATH}"

# ✅ Cria bot
app_bot = Application.builder().token(TOKEN).build()

# ✅ Flask app
app = Flask(__name__)

# 🔗 Define webhook uma única vez
@app.before_first_request
def set_webhook_sync():
    asyncio.run(app_bot.bot.set_webhook(url=WEBHOOK_URL))

# 📬 Recebe mensagens via webhook
@app.post(WEBHOOK_PATH)
async def receive_update():
    update = Update.de_json(request.json, app_bot.bot)
    await app_bot.process_update(update)
    return "OK"

# 🚀 Inicia servidor no Railway
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
