import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from utils.message_cleaner import send_and_delete
from utils.permissions import require_permission
import services.produto_service_pg as produto_service

logger = logging.getLogger(__name__)

async def debitos_handler_raw(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"🔥 RAW HANDLER: debitos_handler chamado!")
    return await debitos_handler_with_permission(update, context)

@require_permission("admin")
async def debitos_handler_with_permission(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Comando /debitos [username] - Mostra débitos do usuário.
    - Admin: Mostra apenas seus próprios débitos
    - Owner: Pode especificar username para ver débitos de qualquer usuário
    Uso: /debitos ou /debitos username_do_comprador
    """
    logger.info("→ Entrando em debitos_handler()")
    logger.info(f"🚀 DEBITOS: Handler chamado por chat_id: {update.effective_chat.id}")
    
    try:
        chat_id = update.effective_chat.id
        
        # Deleta o comando enviado pelo usuário
        try:
            await update.message.delete()
        except:
            pass
        
        # Obtém o nível do usuário atual
        nivel = produto_service.obter_nivel(chat_id)
        username_atual = produto_service.obter_username_por_chat_id(chat_id)
        logger.info(f"👤 DEBITOS: Usuário {username_atual} com nível {nivel}")
        
        if not username_atual:
            await send_and_delete(
                "❌ Usuário não encontrado. Faça login primeiro com /login",
                update,
                context,
                delay=10
            )
            return
        
        # Determina qual comprador usar para consulta
        logger.info(f"📝 DEBITOS: Args recebidos: {context.args}")
        if context.args and len(context.args) > 0:
            # Nome do comprador foi especificado como parâmetro
            target_comprador = " ".join(context.args).strip()
            logger.info(f"🎯 DEBITOS: Procurando débitos para: '{target_comprador}'")
            
            # Apenas owners podem consultar outros usuários
            if nivel != "owner":
                await send_and_delete(
                    "❌ Apenas owners podem consultar débitos de outros compradores.\nUse apenas `/debitos` para ver seus próprios débitos.",
                    update,
                    context,
                    delay=10,
                    parse_mode=ParseMode.MARKDOWN
                )
                return
                
            comprador_nome = target_comprador
            is_self_query = False
        else:
            # Sem parâmetros, usa o próprio username como comprador
            comprador_nome = username_atual
            is_self_query = True
        
        # Busca os débitos do comprador
        try:
            logger.info(f"Buscando débitos para comprador: {comprador_nome}")
            debitos = produto_service.obter_debitos_por_usuario(comprador_nome)
            logger.info(f"Encontrados {len(debitos)} débitos para {comprador_nome}")
        except Exception as e:
            logger.error(f"Erro ao buscar débitos para {comprador_nome}: {e}")
            await send_and_delete(
                f"❌ Erro ao buscar débitos. Tente novamente.",
                update,
                context,
                delay=10
            )
            return
        
        if not debitos:
            # Mensagem personalizada dependendo se está consultando próprios débitos ou de outro comprador
            if is_self_query:
                mensagem = f"✅ Você não possui débitos."
            else:
                mensagem = f"✅ Nenhum débito encontrado para *{comprador_nome}*."
                
                # Para owners, mostra lista de compradores com débitos se não encontrou nenhum
                if nivel == "owner":
                    try:
                        compradores_com_debitos = produto_service.listar_compradores_com_debitos()
                        if compradores_com_debitos:
                            mensagem += f"\n\n📋 *Compradores com débitos:*\n"
                            for comp in compradores_com_debitos[:10]:  # Limita a 10 para não ficar muito longo
                                mensagem += f"• `{comp}`\n"
                            if len(compradores_com_debitos) > 10:
                                mensagem += f"... e mais {len(compradores_com_debitos) - 10} compradores"
                    except Exception as e:
                        logger.error(f"Erro ao listar compradores com débitos: {e}")
                        mensagem += f"\n\n❌ Erro ao carregar lista de compradores."
                
            await send_and_delete(
                mensagem,
                update,
                context,
                delay=15,
                parse_mode=ParseMode.MARKDOWN
            )
            return
        
        # Monta a mensagem com os débitos
        if is_self_query:
            texto = f"*💸 Seus débitos:*\n\n"
        else:
            texto = f"*💸 Débitos de {comprador_nome}:*\n\n"
        total_devido = 0
        
        for venda_id, produto_nome, quantidade, valor_total, valor_pago, valor_devido, data_venda in debitos:
            data_formatada = data_venda.strftime('%d/%m/%Y')
            texto += f"🧾 *Venda #{venda_id}* - {data_formatada}\n"
            texto += f"📦 {produto_nome} (x{quantidade})\n"
            texto += f"💰 Total: R$ {valor_total:.2f}\n"
            texto += f"✅ Pago: R$ {valor_pago:.2f}\n"
            texto += f"🔴 Devido: R$ {valor_devido:.2f}\n\n"
            total_devido += valor_devido
        
        texto += f"*📊 Total devido: R$ {total_devido:.2f}*"
    
        await send_and_delete(
            texto,
            update,
            context,
            delay=20,
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Erro geral em debitos_handler: {e}")
        try:
            await send_and_delete(
                "❌ Erro interno. Tente novamente em alguns instantes.",
                update,
                context,
                delay=10
            )
        except:
            pass  # Se não conseguir nem enviar mensagem de erro, só loga