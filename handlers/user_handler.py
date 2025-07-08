import logging
logger = logging.getLogger(__name__)
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)
from utils.message_cleaner import send_and_delete , send_menu_with_delete , delete_protected_message
from utils.permissions import require_permission
import services.produto_service_pg as produto_service
from handlers.global_handlers import cancel_callback , cancel

# 🔢 Estados da conversa
MENU, ADD_USERNAME, ADD_PASSWORD, REMOVE_USER, EDIT_SELECT_USER, EDIT_ACTION, EDIT_NEW_VALUE = range(7)



# 🔘 Teclado com botões
def main_menu_keyboard():
    keyboard = [
        [
            InlineKeyboardButton("➕ Adicionar", callback_data="add_user"),
            InlineKeyboardButton("➖ Remover", callback_data="remove_user"),
        ],
        [
            InlineKeyboardButton("✏️ Editar", callback_data="edit_user"),
        ],
        [   
        InlineKeyboardButton("🚫 Cancelar", callback_data="cancelar"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# 🚀 Início do comando /user
@require_permission("owner")
async def start_user(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em start_user()")

    await send_menu_with_delete(
        "👤 O que deseja fazer?",
        update,
        context,
        main_menu_keyboard(),
        delay=10
    )
    return MENU

@require_permission("owner")
# ▶️ Seleção do menu
async def menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em menu_selection()")

    query = update.callback_query
    await query.answer()

    # 🔥 Deleta a mensagem do menu anterior
    await delete_protected_message(update, context)

    if query.data == "add_user":
        await send_and_delete("🆕 Envie o nome de usuário que deseja adicionar:", update, context)
        return ADD_USERNAME

    if query.data == "remove_user":
        usuarios = produto_service.listar_usuarios()

        if not usuarios:
            await send_and_delete("🚫 Nenhum usuário encontrado.", update, context)
            return ConversationHandler.END

        await send_menu_with_delete(
            "👥 Escolha o usuário que deseja remover:",
            update,
            context,
            gerar_keyboard_usuarios(usuarios, "remover")
        )
        return REMOVE_USER

    if query.data == "edit_user":
        usuarios = produto_service.listar_usuarios()

        if not usuarios:
            await send_and_delete("🚫 Nenhum usuário encontrado.", update, context)
            return ConversationHandler.END

        await send_menu_with_delete(
            "👥 Escolha o usuário que deseja editar:",
            update,
            context,
            gerar_keyboard_usuarios(usuarios, "editar")
        )
        return EDIT_SELECT_USER


@require_permission("owner")
# ➕ Adicionar usuário
async def add_username(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em add_username()")

    username = update.message.text.strip()

    if produto_service.verificar_username_existe(username):
        await send_and_delete(
            "❌ Este nome de usuário já existe. Por favor, envie outro nome:",
            update,
            context
        )
        return ADD_USERNAME  # 🔥 Continua no mesmo estado

    context.user_data["novo_username"] = username
    await send_and_delete("🔑 Agora envie a senha para este usuário:", update, context)
    return ADD_PASSWORD


@require_permission("owner")
async def add_password(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em add_password()")

    username = context.user_data["novo_username"]
    password = update.message.text

    if produto_service.verificar_username_existe(username):
        await send_and_delete("❌ Esse nome de usuário já existe.", update, context)
    else:
        produto_service.adicionar_usuario(username, password)
        await send_and_delete("✅ Usuário adicionado com sucesso!", update, context)

    return ConversationHandler.END

@require_permission("owner")
# ➖ Remover usuário
async def remove_user(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em remove_user()")

    await delete_protected_message(update, context)
    query = update.callback_query
    await query.answer()
    username = query.data.split(":")[1]

    if produto_service.verificar_username_existe(username):
        produto_service.remover_usuario(username)
        await query.message.edit_text(f"✅ Usuário '{username}' removido com sucesso.")
    else:
        await query.message.edit_text("❌ Usuário não encontrado.")

    return ConversationHandler.END


@require_permission("owner")
# ✏️ Editar usuário
async def edit_select_user(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em edit_select_user()")

    await delete_protected_message(update, context)

    query = update.callback_query
    await query.answer()

    username = query.data.split(":")[1]
    context.user_data["edit_user"] = username

    keyboard = [
        [
            InlineKeyboardButton("✏️ Alterar Nome", callback_data="edit_nome"),
            InlineKeyboardButton("🔑 Alterar Senha", callback_data="edit_senha")
        ]
    ]
    await send_menu_with_delete(
        f"O que deseja editar em '{username}'?",
        update,
        context,
        keyboard=InlineKeyboardMarkup(keyboard),
        delay=10,          # ou o delay que quiser
        protected=True     # se quiser proteger até o próximo clique
    )
    return EDIT_ACTION


@require_permission("owner")
async def edit_action(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em edit_action()")

    
    await delete_protected_message(update, context)

    query = update.callback_query
    await query.answer()

    acao = query.data

    if acao == "edit_nome":
        context.user_data["edit_action"] = "nome"
        await send_and_delete("✏️ Envie o novo nome de usuário:", update, context)

        return EDIT_NEW_VALUE

    if acao == "edit_senha":
        context.user_data["edit_action"] = "senha"
        await send_and_delete("🔑 Envie a nova senha:", update, context)
        return EDIT_NEW_VALUE


@require_permission("owner")
async def edit_new_value(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em edit_new_value()")

    await delete_protected_message(update, context) 
   
    username = context.user_data["edit_user"]
    acao = context.user_data["edit_action"]
    novo_valor = update.message.text

    if not produto_service.verificar_username_existe(username):
        await send_and_delete("❌ Usuário não encontrado.", update, context)
        return ConversationHandler.END

    if acao == "nome":
        produto_service.atualizar_username(username, novo_valor)
        await send_and_delete("✅ Nome de usuário atualizado!", update, context)

    if acao == "senha":
        produto_service.atualizar_senha(username, novo_valor)
        await send_and_delete("✅ Senha atualizada!", update, context)

    return ConversationHandler.END

def get_user_conversation_handler():
    return ConversationHandler(
        entry_points=[CommandHandler("user", start_user)],
        states={
            MENU: [CallbackQueryHandler(menu_selection)],
            ADD_USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_username)],
            ADD_PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_password)],
            REMOVE_USER: [CallbackQueryHandler(remove_user)],
            EDIT_SELECT_USER: [CallbackQueryHandler(edit_select_user)],
            EDIT_ACTION: [CallbackQueryHandler(edit_action)],
            EDIT_NEW_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_new_value)],
        },
        fallbacks=[
            CommandHandler("cancel", cancel), 
            CallbackQueryHandler(cancel_callback, pattern="^cancelar$")
        ],
        allow_reentry=True
    )


NEW_PASSWORD, CONFIRM_PASSWORD = range(2)


async def start_password(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em start_password()")

    await send_and_delete("🔑 Envie a nova senha:", update, context)
    return NEW_PASSWORD


async def received_new_password(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em received_new_password()")

    context.user_data["new_password"] = update.message.text
    await send_and_delete("🔐 Confirme a nova senha:", update, context)
    return CONFIRM_PASSWORD


async def confirm_password(update: Update, context: ContextTypes.DEFAULT_TYPE):    
    logger.info("→ Entrando em confirm_password()")

    new_password = context.user_data.get("new_password")
    confirm_password = update.message.text
    chat_id = update.effective_chat.id

    username = produto_service.obter_username_por_chat_id(chat_id)

    if username is None:
        await send_and_delete("❌ Você não está logado. Use /login primeiro.", update, context)
        return ConversationHandler.END

    if new_password != confirm_password:
        await send_and_delete("❌ As senhas não coincidem. Tente novamente.", update, context)
        return ConversationHandler.END

    produto_service.atualizar_senha(username, new_password)
    await send_and_delete("✅ Sua senha foi atualizada com sucesso.", update, context)

    return ConversationHandler.END

def gerar_keyboard_usuarios(usuarios, callback_prefix):
    """
    Gera uma InlineKeyboardMarkup com botões dos usuários.
    """
    keyboard = []
    for user in usuarios:
        keyboard.append([InlineKeyboardButton(user, callback_data=f"{callback_prefix}:{user}")])

    keyboard.append([InlineKeyboardButton("🚫 Cancelar", callback_data="cancelar")])
    return InlineKeyboardMarkup(keyboard)