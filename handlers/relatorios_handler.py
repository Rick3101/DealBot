import logging
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler, CommandHandler,
    MessageHandler, CallbackQueryHandler, filters
)
from handlers.base_handler import MenuHandlerBase, HandlerRequest, HandlerResponse, InteractionType, ContentType
from handlers.error_handler import with_error_boundary, with_error_boundary_standalone
from models.handler_models import ReportRequest, ReportResponse
from services.handler_business_service import HandlerBusinessService
from utils.permissions import require_permission
from utils.message_cleaner import enviar_documento_temporario
from utils.files import exportar_para_csv
from handlers.global_handlers import ModernGlobalHandlers

logger = logging.getLogger(__name__)

# States
(RELATORIO_MENU, RELATORIO_DIVIDA_NOME, VENDAS_FILTER_SELECTION, 
 VENDAS_FILTER_NAME_INPUT, VENDAS_FILTER_DATE_INPUT, VENDAS_FILTER_PRODUCT_SELECTION) = range(6)


class ModernRelatoriosHandler(MenuHandlerBase):
    def __init__(self):
        super().__init__("relatorios")
        
    def create_main_menu_keyboard(self) -> InlineKeyboardMarkup:
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🧾 Vendas", callback_data="rel_vendas"),
                InlineKeyboardButton("💸 Dívidas", callback_data="rel_dividas")
            ],
            [InlineKeyboardButton("🚫 Cancelar", callback_data="rel_cancel")]
        ])
    
    def create_filter_selection_keyboard(self, selected_filters: set = None) -> InlineKeyboardMarkup:
        """Create keyboard for filter selection with checkbox-style indicators."""
        if selected_filters is None:
            selected_filters = set()
        
        # Create checkboxes for each filter option
        name_checkbox = "✅" if "name" in selected_filters else "☐"
        date_checkbox = "✅" if "date" in selected_filters else "☐"
        product_checkbox = "✅" if "product" in selected_filters else "☐"
        
        return InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{name_checkbox} Filtrar por Nome", callback_data="filter_toggle_name")],
            [InlineKeyboardButton(f"{date_checkbox} Filtrar por Data", callback_data="filter_toggle_date")],
            [InlineKeyboardButton(f"{product_checkbox} Filtrar por Produto", callback_data="filter_toggle_product")],
            [
                InlineKeyboardButton("📋 Aplicar Filtros", callback_data="filter_apply"),
                InlineKeyboardButton("🔍 Ver Tudo", callback_data="filter_none")
            ],
            [InlineKeyboardButton("🚫 Cancelar", callback_data="rel_cancel")]
        ])
    
    def create_product_selection_keyboard(self, products: list) -> InlineKeyboardMarkup:
        """Create keyboard for product selection."""
        buttons = []
        
        # Add product buttons (2 per row)
        for i in range(0, len(products), 2):
            row = []
            for j in range(2):
                if i + j < len(products):
                    product = products[i + j]
                    button_text = f"{product.emoji} {product.nome[:15]}"
                    if len(product.nome) > 15:
                        button_text += "..."
                    row.append(InlineKeyboardButton(
                        button_text, 
                        callback_data=f"filter_product_{product.id}"
                    ))
            buttons.append(row)
        
        # Add control buttons
        buttons.append([InlineKeyboardButton("🚫 Cancelar", callback_data="rel_cancel")])
        
        return InlineKeyboardMarkup(buttons)
    
    def get_menu_text(self) -> str:
        return "📊 Relatório de:"
    
    def get_menu_state(self) -> int:
        return RELATORIO_MENU
    
    def get_retry_state(self) -> Optional[int]:
        return RELATORIO_DIVIDA_NOME
        
    async def handle(self, request: HandlerRequest) -> HandlerResponse:
        return await self.show_main_menu(request)
    
    async def handle_menu_selection(self, request: HandlerRequest, selection: str) -> HandlerResponse:
        if selection == "rel_vendas":
            return await self._handle_sales_filter_selection(request)
        elif selection == "rel_dividas":
            return await self._handle_start_debt_report(request)
        elif selection == "rel_cancel":
            return self.create_smart_response(
                message="🚫 Operação cancelada.",
                keyboard=None,
                interaction_type=InteractionType.CONFIRMATION,
                content_type=ContentType.INFO,
                end_conversation=True
            )
        else:
            return self.create_smart_response(
                message="❌ Opção inválida.",
                keyboard=self.create_main_menu_keyboard(),
                interaction_type=InteractionType.ERROR_DISPLAY,
                content_type=ContentType.VALIDATION_ERROR,
                next_state=RELATORIO_MENU
            )
    
    async def _handle_sales_filter_selection(self, request: HandlerRequest) -> HandlerResponse:
        """Show filter selection screen for sales report."""
        # Initialize filter selection in user data
        if "selected_filters" not in request.user_data:
            request.user_data["selected_filters"] = set()
        
        selected_filters = request.user_data["selected_filters"]
        
        return self.create_smart_response(
            message="🎯 **Filtrar Vendas**\n\nSelecione os filtros que deseja aplicar:",
            keyboard=self.create_filter_selection_keyboard(selected_filters),
            interaction_type=InteractionType.MENU_NAVIGATION,
            content_type=ContentType.SELECTION,
            next_state=VENDAS_FILTER_SELECTION
        )
    
    async def _handle_filter_toggle(self, request: HandlerRequest, filter_type: str) -> HandlerResponse:
        """Handle toggling of filter options."""
        selected_filters = request.user_data.get("selected_filters", set())
        
        if filter_type in selected_filters:
            selected_filters.remove(filter_type)
        else:
            selected_filters.add(filter_type)
        
        request.user_data["selected_filters"] = selected_filters
        
        return self.create_smart_response(
            message="🎯 **Filtrar Vendas**\n\nSelecione os filtros que deseja aplicar:",
            keyboard=self.create_filter_selection_keyboard(selected_filters),
            interaction_type=InteractionType.MENU_NAVIGATION,
            content_type=ContentType.SELECTION,
            next_state=VENDAS_FILTER_SELECTION
        )
    
    async def _handle_filter_apply(self, request: HandlerRequest) -> HandlerResponse:
        """Handle application of selected filters."""
        # Delete the filter selection message immediately using batch cleanup
        if hasattr(request.update, 'callback_query') and request.update.callback_query:
            await self.batch_cleanup_messages([request.update.callback_query], strategy="instant")
        
        selected_filters = request.user_data.get("selected_filters", set())
        
        if not selected_filters:
            # No filters selected, show all sales
            return await self._handle_sales_report_with_filters(request, {})
        
        # Initialize filter values storage
        request.user_data["filter_values"] = {}
        request.user_data["filter_queue"] = list(selected_filters)
        
        # Start collecting filter values
        return await self._handle_next_filter_input(request)
    
    async def _handle_next_filter_input(self, request: HandlerRequest) -> HandlerResponse:
        """Handle the next filter input in the queue."""
        filter_queue = request.user_data.get("filter_queue", [])
        
        if not filter_queue:
            # All filters processed, generate report
            filter_values = request.user_data.get("filter_values", {})
            return await self._handle_sales_report_with_filters(request, filter_values)
        
        # Get next filter to process
        next_filter = filter_queue[0]
        
        if next_filter == "name":
            return self.create_smart_response(
                message="✍️ Digite o nome do comprador para filtrar:",
                keyboard=None,
                interaction_type=InteractionType.FORM_INPUT,
                content_type=ContentType.INFO,
                next_state=VENDAS_FILTER_NAME_INPUT
            )
        elif next_filter == "date":
            return self.create_smart_response(
                message="📅 Digite o período de data (formato: YYYY-MM-DD a YYYY-MM-DD) ou apenas uma data:",
                keyboard=None,
                interaction_type=InteractionType.FORM_INPUT,
                content_type=ContentType.INFO,
                next_state=VENDAS_FILTER_DATE_INPUT
            )
        elif next_filter == "product":
            return await self._handle_product_filter_selection(request)
    
    async def _handle_name_filter_input(self, request: HandlerRequest) -> HandlerResponse:
        """Handle name filter input."""
        nome = request.update.message.text.strip()
        
        if not nome:
            return self.create_smart_response(
                message="❌ Nome não pode estar vazio. Digite novamente:",
                keyboard=None,
                interaction_type=InteractionType.FORM_INPUT,
                content_type=ContentType.VALIDATION_ERROR,
                next_state=VENDAS_FILTER_NAME_INPUT
            )
        
        # Store filter value
        request.user_data["filter_values"]["name"] = nome
        
        # Remove processed filter from queue
        filter_queue = request.user_data.get("filter_queue", [])
        if "name" in filter_queue:
            filter_queue.remove("name")
        
        # Process next filter
        return await self._handle_next_filter_input(request)
    
    async def _handle_date_filter_input(self, request: HandlerRequest) -> HandlerResponse:
        """Handle date filter input."""
        date_text = request.update.message.text.strip()
        
        if not date_text:
            return HandlerResponse(
                message="❌ Data não pode estar vazia. Digite novamente:",
                next_state=VENDAS_FILTER_DATE_INPUT
            )
        
        # Store filter value (we'll parse it in the business service)
        request.user_data["filter_values"]["date"] = date_text
        
        # Remove processed filter from queue
        filter_queue = request.user_data.get("filter_queue", [])
        if "date" in filter_queue:
            filter_queue.remove("date")
        
        # Process next filter
        return await self._handle_next_filter_input(request)
    
    async def _handle_product_filter_selection(self, request: HandlerRequest) -> HandlerResponse:
        """Show product selection for filtering."""
        business_service = HandlerBusinessService(request.context)
        
        try:
            # Get all products
            from core.modern_service_container import get_product_service
            product_service = get_product_service(request.context)
            products = product_service.get_all_products()
            
            if not products:
                return HandlerResponse(
                    message="❌ Nenhum produto encontrado.",
                    keyboard=self.create_filter_selection_keyboard(request.user_data.get("selected_filters", set())),
                    next_state=VENDAS_FILTER_SELECTION
                )
            
            return HandlerResponse(
                message="🛒 Selecione o produto para filtrar:",
                keyboard=self.create_product_selection_keyboard(products),
                next_state=VENDAS_FILTER_PRODUCT_SELECTION
            )
        
        except Exception as e:
            return HandlerResponse(
                message="❌ Erro ao carregar produtos.",
                keyboard=self.create_filter_selection_keyboard(request.user_data.get("selected_filters", set())),
                next_state=VENDAS_FILTER_SELECTION
            )
    
    async def _handle_product_filter_callback(self, request: HandlerRequest, product_id: str) -> HandlerResponse:
        """Handle product selection for filtering."""
        try:
            # Get product name
            from core.modern_service_container import get_product_service
            product_service = get_product_service(request.context)
            product = product_service.get_product_by_id(int(product_id))
            
            if not product:
                return HandlerResponse(
                    message="❌ Produto não encontrado.",
                    keyboard=self.create_filter_selection_keyboard(request.user_data.get("selected_filters", set())),
                    next_state=VENDAS_FILTER_SELECTION
                )
            
            # Store filter value
            request.user_data["filter_values"]["product"] = product.nome
            
            # Remove processed filter from queue
            filter_queue = request.user_data.get("filter_queue", [])
            if "product" in filter_queue:
                filter_queue.remove("product")
            
            # Process next filter
            return await self._handle_next_filter_input(request)
        
        except Exception as e:
            return HandlerResponse(
                message="❌ Erro ao processar seleção de produto.",
                keyboard=self.create_filter_selection_keyboard(request.user_data.get("selected_filters", set())),
                next_state=VENDAS_FILTER_SELECTION
            )
    
    async def _handle_sales_report_with_filters(self, request: HandlerRequest, filters: dict) -> HandlerResponse:
        """Generate sales report with applied filters."""
        business_service = HandlerBusinessService(request.context)
        
        # Create report request with filters
        report_request = ReportRequest(
            report_type="sales",
            comprador_filter=filters.get("name"),
            product_name_filter=filters.get("product")
        )
        
        # Parse date filter if provided
        if "date" in filters:
            date_text = filters["date"]
            try:
                # Try to parse date range or single date
                from datetime import datetime
                if " a " in date_text:
                    # Date range format: "2023-01-01 a 2023-12-31"
                    start_str, end_str = date_text.split(" a ")
                    report_request.start_date = datetime.strptime(start_str.strip(), "%Y-%m-%d")
                    report_request.end_date = datetime.strptime(end_str.strip(), "%Y-%m-%d")
                else:
                    # Single date
                    single_date = datetime.strptime(date_text.strip(), "%Y-%m-%d")
                    report_request.start_date = single_date
                    report_request.end_date = single_date
            except ValueError:
                return HandlerResponse(
                    message="❌ Formato de data inválido. Use YYYY-MM-DD ou YYYY-MM-DD a YYYY-MM-DD",
                    end_conversation=True
                )
        
        report_response = business_service.generate_report(report_request)
        
        if not report_response.success or not report_response.report_data:
            # Create filter summary for empty results
            filter_summary = self._create_filter_summary(filters)
            message = f"📭 Nenhuma venda encontrada{filter_summary}."
            
            return HandlerResponse(
                message=message,
                end_conversation=True,
                delay=10
            )
        
        # Build sales table with filter information
        filter_summary = self._create_filter_summary(filters)
        texto = f"*🧾 Vendas{filter_summary}:*\n\n"
        texto += "```plaintext\n"
        texto += f"{'ID':<5} {'Produto':<20} {'Qtd':<5} {'Valor':<8}\n"
        texto += "-" * 42 + "\n"
        
        for sale_data in report_response.report_data:
            venda_id = sale_data.get('id', 0)
            nome = sale_data.get('produto_nome', 'N/A')[:20]
            qtd = sale_data.get('quantidade', 0)
            total = sale_data.get('valor_total', 0)
            texto += f"{venda_id:<5} {nome:<20} {qtd:<5} R${int(total):<8}\n"
        
        texto += "```"
        
        # Export button
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Exportar CSV", callback_data="rel_export_sales")],
            [InlineKeyboardButton("🚫 Fechar", callback_data="fechar_relatorio")]
        ])
        
        return HandlerResponse(
            message=texto,
            keyboard=keyboard,
            next_state=RELATORIO_MENU,  # Stay in conversation to handle "fechar" button
            delay=15
        )
    
    def _create_filter_summary(self, filters: dict) -> str:
        """Create a summary string of applied filters."""
        if not filters:
            return ""
        
        filter_parts = []
        if "name" in filters:
            filter_parts.append(f"Nome: {filters['name']}")
        if "product" in filters:
            filter_parts.append(f"Produto: {filters['product']}")
        if "date" in filters:
            filter_parts.append(f"Data: {filters['date']}")
        
        if filter_parts:
            return f" ({', '.join(filter_parts)})"
        return ""
    
    async def _handle_sales_report(self, request: HandlerRequest) -> HandlerResponse:
        business_service = HandlerBusinessService(request.context)
        
        # Create report request
        report_request = ReportRequest(report_type="sales")
        report_response = business_service.generate_report(report_request)
        
        if not report_response.success or not report_response.report_data:
            return HandlerResponse(
                message="📭 Nenhuma venda registrada.",
                end_conversation=True,
                delay=10
            )
        
        # Build sales table in markdown
        texto = "*🧾 Vendas:*\n\n"
        texto += "```plaintext\n"
        texto += f"{'ID':<5} {'Produto':<20} {'Qtd':<5} {'Valor':<8}\n"
        texto += "-" * 42 + "\n"
        
        for sale_data in report_response.report_data:
            venda_id = sale_data.get('id', 0)
            nome = sale_data.get('produto_nome', 'N/A')[:20]
            qtd = sale_data.get('quantidade', 0)
            total = sale_data.get('valor_total', 0)
            texto += f"{venda_id:<5} {nome:<20} {qtd:<5} R${int(total):<8}\n"
        
        texto += "```"
        
        # Export button
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Exportar CSV", callback_data="rel_export_sales")],
            [InlineKeyboardButton("🚫 Fechar", callback_data="fechar_relatorio")]
        ])
        
        return HandlerResponse(
            message=texto,
            keyboard=keyboard,
            next_state=RELATORIO_MENU,  # Stay in conversation to handle "fechar" button
            delay=15
        )
    
    async def _handle_start_debt_report(self, request: HandlerRequest) -> HandlerResponse:
        return HandlerResponse(
            message="✍️ Digite o nome do comprador (ou envie vazio para todos):",
            next_state=RELATORIO_DIVIDA_NOME
        )
    
    async def _handle_debt_report_name(self, request: HandlerRequest) -> HandlerResponse:
        business_service = HandlerBusinessService(request.context)
        nome = request.update.message.text.strip()
        buyer_name = nome if nome else None
        
        # Create debt report request
        report_request = ReportRequest(
            report_type="debts",
            buyer_name=buyer_name
        )
        report_response = business_service.generate_report(report_request)
        
        if not report_response.success or not report_response.report_data:
            msg = f"📭 Nenhuma venda encontrada para *{nome}*." if nome else "📭 Nenhuma venda pendente."
            return HandlerResponse(
                message=msg,
                end_conversation=True
            )
        
        # Build debt table
        display_name = nome or "Todos"
        texto = f"*🧾 Compras de:* `{display_name}`\n\n"
        texto += "```plaintext\n"
        texto += f"{'ID':<5} {'Produto':<20} {'Qtd':<5} {'Valor':<8} {'PG'}\n"
        texto += "-" * 50 + "\n"
        
        for debt_data in report_response.report_data:
            venda_id = debt_data.get('id', 0)
            produto_nome = debt_data.get('produto_nome', 'N/A')[:20]
            qtd = debt_data.get('quantidade', 0)
            total = debt_data.get('valor_total', 0)
            texto += f"{venda_id:<5} {produto_nome:<20} {qtd:<5} R${int(total):<8}\n"
        
        texto += "```"
        
        # Store buyer name for CSV export
        request.user_data["detalhes_comprador"] = nome
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Exportar CSV", callback_data="rel_export_debts")],
            [InlineKeyboardButton("🚫 Fechar", callback_data="fechar_relatorio")]
        ])
        
        return HandlerResponse(
            message=texto,
            keyboard=keyboard,
            end_conversation=True
        )
    
    async def _handle_export_sales_csv(self, request: HandlerRequest) -> HandlerResponse:
        business_service = HandlerBusinessService(request.context)
        
        # Get sales data
        report_request = ReportRequest(report_type="sales")
        report_response = business_service.generate_report(report_request)
        
        if not report_response.success or not report_response.report_data:
            return HandlerResponse(
                message="📭 Nenhuma venda registrada.",
                end_conversation=True
            )
        
        # Create CSV data
        colunas = ["ID", "Comprador", "Produto", "Quantidade", "Valor Total", "Data"]
        dados = []
        
        for sale_data in report_response.report_data:
            dados.append([
                sale_data.get('id', ''),
                sale_data.get('comprador', ''),
                sale_data.get('produto_nome', ''),
                sale_data.get('quantidade', ''),
                f"{sale_data.get('valor_total', 0):.2f}",
                sale_data.get('data_venda', '')
            ])
        
        csv_bytes = exportar_para_csv(colunas, dados)
        
        # Send temporary document
        await enviar_documento_temporario(
            context=request.context,
            chat_id=request.chat_id,
            document_bytes=csv_bytes,
            filename="vendas.csv",
            caption="📄 Arquivo exportado com sucesso! Este arquivo será deletado em 2 minutos.",
            timeout=120
        )
        
        return HandlerResponse(
            message="✅ CSV enviado com sucesso!",
            end_conversation=True
        )
    
    async def _handle_export_debts_csv(self, request: HandlerRequest) -> HandlerResponse:
        business_service = HandlerBusinessService(request.context)
        nome = request.user_data.get("detalhes_comprador")
        
        if not nome:
            return HandlerResponse(
                message="❌ Nome do comprador não encontrado.",
                end_conversation=True
            )
        
        # Get debt data
        report_request = ReportRequest(
            report_type="debts", 
            buyer_name=nome
        )
        report_response = business_service.generate_report(report_request)
        
        if not report_response.success or not report_response.report_data:
            return HandlerResponse(
                message="📭 Nenhuma venda registrada.",
                end_conversation=True
            )
        
        # Create CSV data
        colunas = ["ID", "Produto", "Quantidade", "Valor Lote"]
        dados = []
        
        for debt_data in report_response.report_data:
            dados.append([
                debt_data.get('id', ''),
                debt_data.get('produto_nome', ''),
                debt_data.get('quantidade', ''),
                f"{debt_data.get('valor_total', 0):.2f}"
            ])
        
        csv_bytes = exportar_para_csv(colunas, dados)
        
        # Send temporary document
        await enviar_documento_temporario(
            context=request.context,
            chat_id=request.chat_id,
            document_bytes=csv_bytes,
            filename=f"compras_{nome}.csv",
            caption=f"📄 Compras de {nome} exportadas com sucesso! Este arquivo será deletado em 2 minutos.",
            timeout=120
        )
        
        return HandlerResponse(
            message="✅ CSV enviado com sucesso!",
            end_conversation=True
        )
    
    def get_conversation_handler(self) -> ConversationHandler:
        return ConversationHandler(
            entry_points=[CommandHandler("relatorios", self._start_relatorios)],
            states={
                RELATORIO_MENU: [
                    CallbackQueryHandler(self._menu_callback, pattern="^rel_(vendas|dividas|export_sales|export_debts)$"),
                    CallbackQueryHandler(self._close_report_callback, pattern="^fechar_relatorio$"),
                    CallbackQueryHandler(ModernGlobalHandlers.cancel_callback, pattern="^rel_cancel$")
                ],
                RELATORIO_DIVIDA_NOME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._debt_name_callback),
                    CallbackQueryHandler(self._close_report_callback, pattern="^fechar_relatorio$")
                ],
                VENDAS_FILTER_SELECTION: [
                    CallbackQueryHandler(self._filter_selection_callback, pattern="^filter_"),
                    CallbackQueryHandler(self._close_report_callback, pattern="^fechar_relatorio$")
                ],
                VENDAS_FILTER_NAME_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._filter_name_input_callback),
                    CallbackQueryHandler(self._close_report_callback, pattern="^fechar_relatorio$")
                ],
                VENDAS_FILTER_DATE_INPUT: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self._filter_date_input_callback),
                    CallbackQueryHandler(self._close_report_callback, pattern="^fechar_relatorio$")
                ],
                VENDAS_FILTER_PRODUCT_SELECTION: [
                    CallbackQueryHandler(self._filter_product_callback, pattern="^filter_product_"),
                    CallbackQueryHandler(self._close_report_callback, pattern="^fechar_relatorio$")
                ],
            },
            fallbacks=[
                CommandHandler("cancel", ModernGlobalHandlers.cancel),
                CallbackQueryHandler(ModernGlobalHandlers.cancel_callback, pattern="^rel_cancel$")
            ],
            allow_reentry=True
        )
    
    @require_permission("admin")
    @with_error_boundary
    async def _start_relatorios(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = self.create_request(update, context)
        response = await self.handle(request)
        return await self.send_response(response, request)
    
    @with_error_boundary
    async def _menu_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = self.create_request(update, context)
        selection = update.callback_query.data
        
        if selection == "rel_export_sales":
            response = await self._handle_export_sales_csv(request)
        elif selection == "rel_export_debts":
            response = await self._handle_export_debts_csv(request)
        else:
            response = await self.handle_menu_selection(request, selection)
        
        return await self.send_response(response, request)
    
    @with_error_boundary
    async def _debt_name_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = self.create_request(update, context)
        response = await self._handle_debt_report_name(request)
        return await self.send_response(response, request)
    
    @with_error_boundary
    async def _filter_selection_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = self.create_request(update, context)
        selection = update.callback_query.data
        
        if selection.startswith("filter_toggle_"):
            filter_type = selection.replace("filter_toggle_", "")
            response = await self._handle_filter_toggle(request, filter_type)
        elif selection == "filter_apply":
            response = await self._handle_filter_apply(request)
        elif selection == "filter_none":
            # Delete the filter selection message immediately
            if hasattr(request.update, 'callback_query') and request.update.callback_query:
                try:
                    await request.update.callback_query.message.delete()
                    await request.update.callback_query.answer()
                except Exception as e:
                    self.logger.warning(f"Could not delete filter selection message: {e}")
            response = await self._handle_sales_report_with_filters(request, {})
        else:
            response = HandlerResponse(
                message="❌ Opção inválida.",
                keyboard=self.create_filter_selection_keyboard(request.user_data.get("selected_filters", set())),
                next_state=VENDAS_FILTER_SELECTION
            )
        
        return await self.send_response(response, request)
    
    @with_error_boundary
    async def _filter_name_input_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = self.create_request(update, context)
        response = await self._handle_name_filter_input(request)
        return await self.send_response(response, request)
    
    @with_error_boundary
    async def _filter_date_input_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = self.create_request(update, context)
        response = await self._handle_date_filter_input(request)
        return await self.send_response(response, request)
    
    @with_error_boundary
    async def _filter_product_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        request = self.create_request(update, context)
        callback_data = update.callback_query.data
        
        if callback_data.startswith("filter_product_"):
            product_id = callback_data.replace("filter_product_", "")
            response = await self._handle_product_filter_callback(request, product_id)
        else:
            response = HandlerResponse(
                message="❌ Seleção de produto inválida.",
                keyboard=self.create_filter_selection_keyboard(request.user_data.get("selected_filters", set())),
                next_state=VENDAS_FILTER_SELECTION
            )
        
        return await self.send_response(response, request)
    
    @with_error_boundary
    async def _close_report_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        """Handle the fechar_relatorio callback."""
        query = update.callback_query
        await query.answer()
        
        try:
            await query.message.delete()
        except Exception as e:
            logger.warning(f"Could not delete message: {e}")
        
        # End conversation cleanly without confirmation message (UX Flow Guide Pattern 2.1)
        from telegram.ext import ConversationHandler
        return ConversationHandler.END


# Factory function for the relatorios conversation handler
def get_relatorios_conversation_handler() -> ConversationHandler:
    handler = ModernRelatoriosHandler()
    return handler.get_conversation_handler()


# Standalone handlers for legacy compatibility
@require_permission("admin")
@with_error_boundary
async def detalhes_vendas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Legacy command handler for detailed sales view"""
    logger.info("→ Entrando em detalhes_vendas()")

    if not context.args:
        from utils.message_cleaner import send_and_delete
        await send_and_delete("❗ Use: /detalhes <nome_do_comprador> [pagos|pendentes]", update, context)
        return

    args = context.args
    nome = args[0]
    status = args[1].lower() if len(args) > 1 and args[1].lower() in ("pagos", "pendentes") else None

    business_service = HandlerBusinessService(context)
    report_request = ReportRequest(
        report_type="debts" if status == "pendentes" else "sales",
        buyer_name=nome
    )
    
    report_response = business_service.generate_report(report_request)
    
    if not report_response.success or not report_response.report_data:
        msg = f"📭 Nenhuma venda encontrada para *{nome}*"
        if status == "pagos":
            msg += " (pagas)."
        elif status == "pendentes":
            msg += " (pendentes)."
        else:
            msg += "."
        
        from utils.message_cleaner import send_and_delete
        await send_and_delete(msg, update, context)
        return

    texto = f"*🧾 Compras de:* `{nome}`\n"
    texto += "```plaintext\n"
    texto += f"{'ID':<5} {'Produto':<20} {'Qtd':<5} {'Valor':<8} {'PG'}\n"
    texto += "-" * 50 + "\n"

    for sale_data in report_response.report_data:
        venda_id = sale_data.get('id', 0)
        produto_nome = sale_data.get('produto_nome', 'N/A')[:20]
        qtd = sale_data.get('quantidade', 0)
        total = sale_data.get('valor_total', 0)
        texto += f"{venda_id:<5} {produto_nome:<20} {qtd:<5} R${int(total):<8}\n"

    texto += "```"

    # Store buyer name for CSV export
    context.user_data["detalhes_comprador"] = nome

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Exportar CSV", callback_data="exportar_csv_detalhes")],
        [InlineKeyboardButton("🚫 Fechar", callback_data="fechar_relatorio")]
    ])

    from telegram.constants import ParseMode
    await update.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)


# Legacy callback handlers for backward compatibility
@with_error_boundary
async def exportar_csv_detalhes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Legacy callback handler for CSV export"""
    logger.info("→ Entrando em exportar_csv_detalhes()")
    
    query = update.callback_query
    await query.answer()

    nome = context.user_data.get("detalhes_comprador")
    if not nome:
        await query.message.edit_text("❌ Nome do comprador não encontrado.")
        return

    business_service = HandlerBusinessService(context)
    report_request = ReportRequest(report_type="debts", buyer_name=nome)
    report_response = business_service.generate_report(report_request)

    if not report_response.success or not report_response.report_data:
        await query.message.edit_text("📭 Nenhuma venda registrada.")
        return

    colunas = ["ID", "Produto", "Quantidade", "Valor Lote"]
    dados = []
    for sale_data in report_response.report_data:
        dados.append([
            sale_data.get('id', ''),
            sale_data.get('produto_nome', ''),
            sale_data.get('quantidade', ''),
            f"{sale_data.get('valor_total', 0):.2f}"
        ])
    
    csv_bytes = exportar_para_csv(colunas, dados)

    await enviar_documento_temporario(
        context=context,
        chat_id=query.message.chat_id,
        document_bytes=csv_bytes,
        filename=f"compras_{nome}.csv",
        caption=f"📄 Compras de {nome} exportadas com sucesso! Este arquivo será deletado em 2 minutos.",
        timeout=120
    )


# New /dividas command - shows debt report for authenticated user
@require_permission("admin")
@with_error_boundary_standalone("dividas_usuario")
async def dividas_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Command handler for /dividas [username] - shows debt report.
    - Without parameter: shows authenticated user's own debts
    - With parameter (owner only): shows specified user's debts
    """
    logger.info("→ Entrando em dividas_usuario()")
    
    try:
        # Get authenticated user from chat_id
        from core.modern_service_container import get_user_service
        chat_id = update.effective_chat.id
        
        try:
            user_service = get_user_service(context)
            authenticated_user = user_service.get_user_by_chat_id(chat_id)
        except Exception as service_error:
            logger.error(f"Error getting user service: {service_error}")
            from utils.message_cleaner import send_and_delete
            await send_and_delete("❌ Erro interno. Tente novamente.", update, context)
            return
        
        if not authenticated_user:
            from utils.message_cleaner import send_and_delete
            await send_and_delete("❌ Usuário não autenticado. Use /login primeiro.", update, context)
            return
        
        # Check for username parameter (owner only)
        if context.args and len(context.args) > 0:
            if authenticated_user.level.value != "owner":
                # Non-owners can only see their own debts
                from utils.message_cleaner import send_and_delete
                await send_and_delete("❌ Apenas owners podem ver dívidas de outros usuários.", update, context)
                return
            nome = context.args[0]  # Use specified username
            is_viewing_other = True
        else:
            nome = authenticated_user.username  # Use own username
            is_viewing_other = False
        
        logger.info(f"Getting debts for user: {nome} (viewing other: {is_viewing_other})")
        
        business_service = HandlerBusinessService(context)
        report_request = ReportRequest(
            report_type="debts",
            buyer_name=nome
        )
        
        report_response = business_service.generate_report(report_request)
        
        if not report_response.success or not report_response.report_data:
            from utils.message_cleaner import send_and_delete
            if is_viewing_other:
                await send_and_delete(f"📭 Nenhuma compra pendente encontrada para {nome}.", update, context, delay=10)
            else:
                await send_and_delete(f"📭 Nenhuma compra pendente encontrada para você ({nome}).", update, context, delay=10)
            return
        
        # Build debt table with appropriate header
        if is_viewing_other:
            texto = f"*💸 Dívidas de:* `{nome}`\n\n"
        else:
            texto = f"*💸 Suas Dívidas:* `{nome}`\n\n"
        texto += "```plaintext\n"
        texto += f"{'ID':<5} {'Produto':<20} {'Qtd':<5} {'Valor':<8}\n"
        texto += "-" * 42 + "\n"
        
        total_debt = 0
        for debt_data in report_response.report_data:
            venda_id = debt_data.get('id', 0)
            produto_nome = debt_data.get('produto_nome', 'N/A')[:20]
            qtd = debt_data.get('quantidade', 0)
            valor = debt_data.get('valor_total', 0)
            total_debt += valor
            texto += f"{venda_id:<5} {produto_nome:<20} {qtd:<5} R${int(valor):<8}\n"
        
        texto += "-" * 42 + "\n"
        texto += f"{'TOTAL':<32} R${int(total_debt):<8}\n"
        texto += "```"
        
        # Store user info for CSV export
        context.user_data["dividas_usuario"] = nome
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Exportar CSV", callback_data="exportar_csv_dividas_usuario")],
            [InlineKeyboardButton("🚫 Fechar", callback_data="fechar_relatorio")]
        ])
        
        from telegram.constants import ParseMode
        message = await update.message.reply_text(texto, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
        
        # Auto-delete after 30 seconds
        from utils.message_cleaner import delayed_delete
        await delayed_delete(message, context, delay=30)
        
    except Exception as e:
        logger.error(f"Error in dividas_usuario: {e}", exc_info=True)
        from utils.message_cleaner import send_and_delete
        await send_and_delete("❌ Erro ao buscar suas dívidas. Tente novamente.", update, context)


# CSV export callback for /dividas command
@with_error_boundary_standalone("exportar_csv_dividas_usuario")
async def exportar_csv_dividas_usuario(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback handler for CSV export from /dividas command"""
    logger.info("→ Entrando em exportar_csv_dividas_usuario()")
    
    query = update.callback_query
    await query.answer()
    
    nome = context.user_data.get("dividas_usuario")
    if not nome:
        await query.message.edit_text("❌ Informações do usuário não encontradas.")
        return
    
    business_service = HandlerBusinessService(context)
    report_request = ReportRequest(report_type="debts", buyer_name=nome)
    report_response = business_service.generate_report(report_request)
    
    if not report_response.success or not report_response.report_data:
        await query.message.edit_text("📭 Nenhuma dívida registrada.")
        return
    
    # Create CSV data
    colunas = ["ID", "Produto", "Quantidade", "Valor Total", "Data Venda"]
    dados = []
    
    for debt_data in report_response.report_data:
        dados.append([
            debt_data.get('id', ''),
            debt_data.get('produto_nome', ''),
            debt_data.get('quantidade', ''),
            f"{debt_data.get('valor_total', 0):.2f}",
            debt_data.get('data_venda', '')
        ])
    
    csv_bytes = exportar_para_csv(colunas, dados)
    
    # Send temporary document
    await enviar_documento_temporario(
        context=context,
        chat_id=query.message.chat_id,
        document_bytes=csv_bytes,
        filename=f"minhas_dividas_{nome}.csv",
        caption=f"📄 Suas dívidas exportadas com sucesso! Este arquivo será deletado em 2 minutos.",
        timeout=120
    )
    
    # Clean up the original message
    try:
        await query.message.delete()
    except Exception as e:
        logger.warning(f"Could not delete message: {e}")


# Standalone callback handler for "Fechar" button
@with_error_boundary
async def fechar_relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Standalone callback handler for closing reports"""
    logger.info("→ Entrando em fechar_relatorio()")
    
    query = update.callback_query
    await query.answer()
    
    try:
        await query.message.delete()
    except Exception as e:
        logger.warning(f"Could not delete message: {e}")
    
    # No confirmation message needed (UX Flow Guide Pattern 2.1)


# Command handler registrations
detalhes_vendas_handler = CommandHandler("detalhes", detalhes_vendas)
dividas_usuario_handler = CommandHandler("dividas", dividas_usuario)
exportar_csv_detalhes_handler = CallbackQueryHandler(exportar_csv_detalhes, pattern="^exportar_csv_detalhes$")
exportar_csv_dividas_usuario_handler = CallbackQueryHandler(exportar_csv_dividas_usuario, pattern="^exportar_csv_dividas_usuario$")
fechar_relatorio_handler = CallbackQueryHandler(fechar_relatorio, pattern="^fechar_relatorio$")