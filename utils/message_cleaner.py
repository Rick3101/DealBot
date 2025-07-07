import asyncio
from telegram import InputFile , Message

def get_effective_message(update):
    """
    Retorna a mensagem, seja de texto normal ou de callback (botão).
    """
    return update.message or (update.callback_query.message if update.callback_query else None)


async def delayed_delete(message, context, delay=10, protected_messages=None):
    await asyncio.sleep(delay)
    protected_messages = protected_messages or context.chat_data.get("protected_messages", set())
    if message.message_id in protected_messages:
        print(f"[PROTEGIDA] Mensagem {message.message_id} não será deletada.")
        return
    try:
        await message.delete()
        print(f"[DELETADA] Mensagem {message.message_id} foi deletada.")
    except Exception as e:
        print(f"[ERRO] Não foi possível deletar mensagem {message.message_id}: {e}")


def get_event_loop_safe():
    """Garante que sempre haverá um loop de evento válido (para uso em Flask/Webhook)"""
    try:
        return asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


async def send_and_delete(
    text, update, context, delay=10, protected=False, **kwargs
):
    msg_obj = get_effective_message(update)

    if msg_obj:
        msg = await msg_obj.reply_text(text, **kwargs)

        if protected:
            protected_set = context.chat_data.setdefault("protected_messages", set())
            protected_set.update({msg.message_id, msg_obj.message_id})
            protected_copy = protected_set.copy()
        else:
            protected_copy = None

        context.application.create_task(delayed_delete(msg, context, delay, protected_copy))
        context.application.create_task(delayed_delete(msg_obj, context, delay, protected_copy))

        return msg
    return None

async def send_menu_with_delete(
    text, update, context, keyboard, delay=10, protected=True
):
    """
    Envia uma mensagem com InlineKeyboard (botões) e deleta ela e a anterior após o delay.
    """
    msg_obj = get_effective_message(update)

    if msg_obj:
        msg = await msg_obj.reply_text(
            text,
            reply_markup=keyboard
        )

        if protected:
            context.chat_data.setdefault("protected_messages", set()).add(msg.message_id)
            context.chat_data.setdefault("protected_messages", set()).add(msg_obj.message_id)

        asyncio.create_task(delayed_delete(msg, context, delay))
        asyncio.create_task(delayed_delete(msg_obj, context, delay))

        return msg

    return None


async def delete_protected_message(update, context):
    """
    Deleta manualmente uma mensagem protegida após o clique em callback.
    """
    msg = get_effective_message(update)

    if msg:
        protected_messages = context.chat_data.get("protected_messages", set())
        protected_messages.discard(msg.message_id)
        context.chat_data["protected_messages"] = protected_messages

        try:
            await msg.delete()
            print(f"[DELETADA] Mensagem protegida {msg.message_id} foi deletada.")
        except Exception as e:
            print(f"[ERRO] Ao deletar mensagem protegida {msg.message_id}: {e}")

async def enviar_documento_temporario(context, chat_id, document_bytes, filename, caption, timeout=120, protected=False):
    message = await context.bot.send_document(
        chat_id=chat_id,
        document=InputFile(document_bytes, filename=filename),
        caption=caption
    )

    if protected:
        context.chat_data.setdefault("protected_messages", set()).add(message.message_id)
        protected_copy = context.chat_data["protected_messages"].copy()
    else:
        protected_copy = None

    async def deletar():
        await asyncio.sleep(timeout)
        if message.message_id in (protected_copy or set()):
            print(f"[PROTEGIDO] Documento {message.message_id} não será deletado.")
            return
        try:
            await context.bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass

    context.application.create_task(deletar())
