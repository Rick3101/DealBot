from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import os
import asyncio

TOKEN = os.environ.get("BOT_TOKEN")
app_bot = Application.builder().token(TOKEN).build()

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot online!")

app_bot.add_handler(CommandHandler("start", start))

# ✅ Inicia Application manualmente
async def initialize_bot():
    await app_bot.initialize()
    await app_bot.start()
    # Webhook será definido automaticamente após isso

# Flask
flask_app = Flask(__name__)

@flask_app.route(f"/{TOKEN}", methods=["POST"])
async def webhook():
    update = Update.de_json(await request.get_json(force=True), app_bot.bot)
    await app_bot.process_update(update)
    return "ok"

@flask_app.before_first_request
def setup_webhook():
    url = f"https://{os.environ['RENDER_EXTERNAL_HOSTNAME']}/{TOKEN}"
    asyncio.create_task(initialize_bot())
    asyncio.create_task(app_bot.bot.set_webhook(url))

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
