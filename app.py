import os
from flask import Flask, request
from telegram.ext import Application
import telegram

# ✅ Lê o token do ambiente
TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN não encontrado nas variáveis de ambiente.")

# ✅ Cria o bot
app_bot = Application.builder().token(TOKEN).build()

# ✅ Inicializa banco (opcional)
# from services import produto_service
# produto_service.init_db()

# ✅ Webhook path = token
WEBHOOK_PATH = f"/{TOKEN}"

# ✅ Dominio do Railway
RAILWAY_DOMAIN = os.getenv("RAILWAY_URL")  # Exemplo: myapp.up.railway.app
WEBHOOK_URL = f"https://{RAILWAY_DOMAIN}{WEBHOOK_PATH}"

# ✅ Cria app Flask
flask_app = Flask(__name__)

# ✅ Endpoint para Telegram enviar atualizações
@flask_app.post(WEBHOOK_PATH)
async def webhook():
    update = telegram.Update.de_json(request.json, app_bot.bot)
    await app_bot.process_update(update)
    return "OK"

# ✅ Define webhook ao iniciar
@flask_app.before_serving
async def start_webhook():
    await app_bot.bot.set_webhook(url=WEBHOOK_URL)

# ✅ Inicia servidor Flask no Railway
if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
