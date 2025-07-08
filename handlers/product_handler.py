import logging
logger = logging.getLogger(__name__)
import asyncio
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from utils.message_cleaner import (
    send_and_delete,
    send_menu_with_delete,
    delete_protected_message
)
from utils.permissions import require_permission
import services.produto_service_pg as produto_service
from handlers.global_handlers import cancel, cancel_callback


# 🔢 Estados
PRODUCT_MENU, PRODUCT_ADD_NAME, PRODUCT_ADD_EMOJI, PRODUCT_ADD_MEDIA_CONFIRM, PRODUCT_ADD_MEDIA = range(5)


# 🔘 Menu principal do /product
def product_menu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("➕ Inserir Produto", callback_data="add_product"),
            InlineKeyboardButton("✏️ Editar Produto", callback_data="edit_product"),
        ],
        [
            InlineKeyboardButton("🚫 Cancelar", callback_data="cancelar")
        ],
    ])


# 🚀 Início do /product
@require_permission("owner")
async def start_product(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em start_product()")

    await send_menu_with_delete(
        "📦 O que deseja fazer?",
        update,
        context,
        product_menu_keyboard(),
        delay=10,
        protected=False  # 🔥 Não precisa proteger menus iniciais
    )
    return PRODUCT_MENU


# ▶️ Seleção do menu
async def product_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em product_menu_selection()")

    query = update.callback_query
    await query.answer()

    await delete_protected_message(update, context)

    if query.data == "add_product":
        await send_and_delete("📝 Envie o nome do produto:", update, context)
        return PRODUCT_ADD_NAME

    if query.data == "edit_product":
        return await start_edit_product(update, context)



# ➕ Recebe nome do produto
async def product_add_name(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em product_add_name()")

    nome = update.message.text.strip()

    if produto_service.verificar_produto_existe(nome):
        await send_and_delete(
            "❌ Já existe um produto com esse nome. Por favor, envie outro nome:",
            update,
            context
        )
        return PRODUCT_ADD_NAME  # 🔥 Fica no mesmo estado esperando nome válido

    context.user_data["product_name"] = nome
    await send_and_delete("😊 Agora envie o emoji para este produto:", update, context)
    return PRODUCT_ADD_EMOJI


# ➕ Recebe emoji do produto
async def product_add_emoji(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em product_add_emoji()")

    context.user_data["product_emoji"] = update.message.text

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📷 Sim", callback_data="add_media_yes"),
            InlineKeyboardButton("❌ Não", callback_data="add_media_no")
        ]
    ])

    await send_menu_with_delete(
        "Deseja adicionar uma mídia ao produto?",
        update,
        context,
        keyboard,
        delay=10,           # 🔥 Deleta depois
        protected=False     # 🔥 Não precisa proteger
    )
    return PRODUCT_ADD_MEDIA_CONFIRM


# ✔️ Verifica se quer adicionar mídia
async def product_media_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em product_media_confirm()")

    query = update.callback_query
    await query.answer()

    await delete_protected_message(update, context)

    if query.data == "add_media_yes":
        await send_and_delete("📥 Envie a mídia (foto, vídeo ou documento):", update, context)
        return PRODUCT_ADD_MEDIA

    if query.data == "add_media_no":
        produto_service.adicionar_produto(
            nome=context.user_data["product_name"],
            emoji=context.user_data["product_emoji"],
            media_file_id=None
        )
        await send_and_delete("✅ Produto adicionado com sucesso sem mídia.", update, context)
        return ConversationHandler.END


# ✔️ Recebe a mídia
async def product_receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em product_receive_media()")

    file_id = None
    message: Message = update.message

    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id
    elif message.video:
        file_id = message.video.file_id

    if not file_id:
        await send_and_delete("❌ Mídia inválida. Envie uma foto, vídeo ou documento.", update, context)
        return PRODUCT_ADD_MEDIA

    # 🔥 Salvar no banco
    produto_service.adicionar_produto(
        nome=context.user_data["product_name"],
        emoji=context.user_data["product_emoji"],
        media_file_id=file_id
    )

    # 🔥 Marcar a mídia como protegida (nunca apagar)
    context.chat_data.setdefault("protected_messages", set()).add(message.message_id)

    await send_and_delete("✅ Produto adicionado com sucesso com mídia.", update, context)

    return ConversationHandler.END

def get_product_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("product", start_product)],
        states={
            # 🔹 Menu principal
            PRODUCT_MENU: [
                CallbackQueryHandler(product_menu_selection)
            ],

            # 🔹 Inserir Produto
            PRODUCT_ADD_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, product_add_name)
            ],
            PRODUCT_ADD_EMOJI: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, product_add_emoji)
            ],
            PRODUCT_ADD_MEDIA_CONFIRM: [
                CallbackQueryHandler(product_media_confirm),
                CallbackQueryHandler(cancel_callback, pattern="^cancelar$")
            ],
            PRODUCT_ADD_MEDIA: [
                MessageHandler(filters.ALL & ~filters.COMMAND, product_receive_media)
            ],

            # 🔹 Editar Produto
            PRODUCT_EDIT_SELECT: [
                CallbackQueryHandler(edit_select_product, pattern="^editproduct:"),
                CallbackQueryHandler(cancel_callback, pattern="^cancelar$")          
            ],
            PRODUCT_EDIT_PROPERTY: [
                CallbackQueryHandler(edit_property_selection),
                CallbackQueryHandler(cancel_callback, pattern="^cancelar$")
            ],
            PRODUCT_EDIT_NEW_VALUE: [
                MessageHandler(filters.ALL & ~filters.COMMAND, edit_receive_new_value)
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel_callback, pattern="^cancelar$")
        ],
        allow_reentry=True
    )

(
    PRODUCT_EDIT_SELECT,
    PRODUCT_EDIT_PROPERTY,
    PRODUCT_EDIT_NEW_VALUE
) = range(5, 8)


# 🔘 Gera teclado com lista de produtos
def gerar_keyboard_produtos(callback_prefix):
    produtos = produto_service.listar_todos_produtos()
    keyboard = []
    for pid, nome, emoji in produtos:
        display_text = f"{emoji} {nome}" if emoji else nome
        keyboard.append([InlineKeyboardButton(display_text, callback_data=f"{callback_prefix}:{pid}")])
    keyboard.append([InlineKeyboardButton("🚫 Cancelar", callback_data="cancelar")])
    return InlineKeyboardMarkup(keyboard)



# ▶️ Handler ao clicar em "Editar Produto"
async def start_edit_product(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em start_edit_product()")

    query = getattr(update, "callback_query", None)

    if query:
        await query.answer()
        await delete_protected_message(update, context)

    produtos = produto_service.listar_todos_produtos()

    if not produtos:
        await send_and_delete("🚫 Nenhum produto cadastrado.", update, context)
        return ConversationHandler.END

    await send_menu_with_delete(
        "👀 Escolha o produto que deseja editar:",
        update,
        context,
        gerar_keyboard_produtos("editproduct")
    )
    return PRODUCT_EDIT_SELECT



# ▶️ Seleciona qual produto editar
async def edit_select_product(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em edit_select_product()")

    query = update.callback_query
    await query.answer()

    await delete_protected_message(update, context)

    produto_id = query.data.split(":")[1]
    context.user_data["edit_product_id"] = produto_id

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Nome", callback_data="edit_nome"),
            InlineKeyboardButton("😊 Emoji", callback_data="edit_emoji"),
        ],
        [
            InlineKeyboardButton("📷 Mídia", callback_data="edit_media"),
        ],
        [
            InlineKeyboardButton("🚫 Cancelar", callback_data="cancelar")
        ]
    ])

    await send_menu_with_delete(
        "🔧 Qual propriedade deseja editar?",
        update,
        context,
        keyboard
    )
    return PRODUCT_EDIT_PROPERTY


# ▶️ Seleciona a propriedade (nome, emoji, mídia)
async def edit_property_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em edit_property_selection()")

    query = update.callback_query
    await query.answer()

    await delete_protected_message(update, context)

    acao = query.data
    context.user_data["edit_property"] = acao

    if acao == "edit_media":
        await send_and_delete("📥 Envie a nova mídia (foto, vídeo ou documento):", update, context)
    else:
        await send_and_delete("✍️ Quer alterar para o que?", update, context)

    return PRODUCT_EDIT_NEW_VALUE


# ✔️ Recebe novo valor e atualiza
async def edit_receive_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em edit_receive_new_value()")

    produto_id = context.user_data["edit_product_id"]
    propriedade = context.user_data["edit_property"]

    if propriedade == "edit_nome":
        novo_nome = update.message.text
        produto_service.atualizar_nome_produto(produto_id, novo_nome)
        await send_and_delete("✅ Nome atualizado com sucesso!", update, context)

    elif propriedade == "edit_emoji":
        novo_emoji = update.message.text
        produto_service.atualizar_emoji_produto(produto_id, novo_emoji)
        await send_and_delete("✅ Emoji atualizado com sucesso!", update, context)

    elif propriedade == "edit_media":
        message = update.message
        file_id = None

        # 🔒 Protege IMEDIATAMENTE antes de qualquer delay
        protected = context.chat_data.setdefault("protected_messages", set())
        protected.add(message.message_id)

        if message.photo:
            file_id = message.photo[-1].file_id
        elif message.document:
            file_id = message.document.file_id
        elif message.video:
            file_id = message.video.file_id

        if not file_id:
            await send_and_delete("❌ Mídia inválida. Envie uma foto, vídeo ou documento.", update, context)
            return PRODUCT_EDIT_NEW_VALUE

        produto_service.atualizar_midia_produto(produto_id, file_id)

        # 🔒 Protege a nova mídia
        protected = context.chat_data.setdefault("protected_messages", set())
        protected.add(message.message_id)

        # Evita que o update da mídia seja reutilizado e deletado
        await send_and_delete("✅ Mídia atualizada com sucesso!", update, context)

    await send_and_delete(
        "🔁 Voltando ao menu de edição...",
        update,
        context,
        delay=5,
        protected=False
    )
    await asyncio.sleep(0.5)

    # Chama menu com um update "limpo"
    return await start_edit_product(update, context)
