import logging
logger = logging.getLogger(__name__)
from telegram import Update, Message
from telegram.ext import ContextTypes
import services.produto_service_pg as produto_service
import asyncio
import telegram
from utils.permissions import require_permission

@require_permission("admin")
async def lista_produtos(update: Update, context: ContextTypes.DEFAULT_TYPE):    

    
    logger.info("→ Entrando em lista_produtos()")

    chat_id = update.effective_chat.id

    # 🧼 Deleta o comando /lista_produtos enviado pelo usuário
    msg = update.message or (update.callback_query.message if update.callback_query else None)
    if msg:
        try:
            await msg.delete()
        except:
            pass

    # 🔒 Cria lock se não existir
    if "lista_lock" not in context.chat_data:
        context.chat_data["lista_lock"] = asyncio.Lock()

    lock: asyncio.Lock = context.chat_data["lista_lock"]

    # ⚠️ Impede execução paralela
    if lock.locked():
        await context.bot.send_message(
            chat_id=chat_id,
            text="⏳ A lista de produtos ainda está sendo exibida. Aguarde um momento..."
        )
        return

    async with lock:
        produtos = produto_service.listar_produtos_com_estoque()
        precos = dict(produto_service.obter_precos_medios())

        if not produtos:
            await context.bot.send_message(chat_id=chat_id, text="🚫 Nenhum produto com estoque.")
            return

        mensagens: list[Message] = []

        for pid, nome, emoji, _ in produtos:
            preco = precos.get(nome, "0.00")
            texto = f"*{emoji} {nome} - R$ {preco}*"

            msg_txt = await context.bot.send_message(chat_id=chat_id, text=texto, parse_mode="Markdown")
            mensagens.append(msg_txt)

            media_id = produto_service.get_media_file_id(pid)
            if media_id:
                try:
                    if media_id.startswith("AgAC"):
                        msg_media = await context.bot.send_photo(chat_id=chat_id, photo=media_id)
                    elif media_id.startswith("BAAC"):
                        msg_media = await context.bot.send_document(chat_id=chat_id, document=media_id)
                    elif media_id.startswith("BAAD"):
                        msg_media = await context.bot.send_video(chat_id=chat_id, video=media_id)
                    else:
                        msg_media = await context.bot.send_message(chat_id=chat_id, text="❓ Mídia desconhecida.")
                except telegram.error.BadRequest as e:
                    msg_media = await context.bot.send_message(chat_id=chat_id, text=f"❌ Erro ao carregar mídia: {e}")

                mensagens.append(msg_media)

        # ⏱️ Espera e deleta tudo
        await asyncio.sleep(15)
        for m in mensagens:
            try:
                await m.delete()
            except:
                pass
