from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import asyncio

# 🔐 Token do Bot
TOKEN = os.environ.get("BOT_TOKEN")

# ✅ Criação segura do bot
app_bot = Application.builder().token(TOKEN).build()

# 🔹 Handler de teste
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot está online via Render!")

app_bot.add_handler(CommandHandler("start", start))

# 🌐 Flask App
flask_app = Flask(__name__)

# 📩 Rota Webhook
@flask_app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), app_bot.bot)
    asyncio.create_task(app_bot.process_update(update))
    return "ok"

# 🌐 Webhook automático no boot
@flask_app.before_first_request
def setup_webhook():
    webhook_url = f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{TOKEN}"
    asyncio.create_task(app_bot.bot.set_webhook(webhook_url))

# ▶️ Executar local (Render ignora isso, mas útil localmente)
if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
