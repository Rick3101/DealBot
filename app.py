import os
import asyncio
from flask import Flask, request
from telegram import Update
from telegram.ext import Application

# ✅ Token do bot e domínio
TOKEN = "7593794682:AAEqzdMTtkzGcJLdI_SGFjRSF50q4ntlIjo"
RAILWAY_URL = "web-production-32b2.up.railway.app"  # Ex: 'meubot.up.railway.app'
if not TOKEN or not RAILWAY_URL:
    raise ValueError("BOT_TOKEN ou RAILWAY_URL não definidos.")

WEBHOOK_PATH = f"/{TOKEN}"
WEBHOOK_URL = f"https://{RAILWAY_URL}{WEBHOOK_PATH}"

# ✅ Cria o bot
app_bot = Application.builder().token(TOKEN).build()

# ✅ Inicia Flask
app = Flask(__name__)

# ✅ Inicializa app_bot (async) + seta webhook
async def setup_bot():
    await app_bot.initialize()
    await app_bot.bot.set_webhook(url=WEBHOOK_URL)
    await app_bot.start()  # obrigatória para uso de process_update

asyncio.run(setup_bot())

# 📬 Rota síncrona que chama a lógica async
@app.route(WEBHOOK_PATH, methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app_bot.bot)
    asyncio.run(app_bot.process_update(update))
    return "OK", 200

# 🚀 Executa Flask
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))