import logging
logger = logging.getLogger(__name__)
import asyncio
from telegram import Update
from telegram.ext import ContextTypes
from utils.message_cleaner import send_and_delete
from utils.permissions import require_permission
from utils.lock_conversation import lock_conversation
from services import produto_service_pg as produto_service

@lock_conversation
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    
    logger.info("→ Entrando em start()")
    frase = produto_service.obter_frase_start()

    await send_and_delete(
        "✅ "+frase,
        update,
        context,
        delay=10,
        protected=True
    )

async def protect(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    
    logger.info("→ Entrando em protect()")

    await send_and_delete(
    "🔒 Esta mensagem é protegida e não será deletada.",
    update,
    context,
    delay=10,
    protected=True
    )