from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from services.base_service import BaseService, ServiceError, ValidationError, NotFoundError
from core.config import get_secret_menu_emojis
from models.handler_models import (
    LoginRequest, LoginResponse, 
    PurchaseRequest, PurchaseResponse,
    InventoryAddRequest, InventoryResponse,
    ReportRequest, ReportResponse,
    PaymentRequest, PaymentResponse,
    UserManagementRequest, UserManagementResponse,
    SmartContractRequest, SmartContractResponse
)
from models.product import Product, ProductWithStock
from models.sale import Sale, CreateSaleRequest
from models.user import User, UserLevel, CreateUserRequest, UpdateUserRequest
from core.modern_service_container import get_user_service, get_product_service, get_sales_service
from core.interfaces import IContext
from utils.input_sanitizer import InputSanitizer
import tempfile
import csv
import os
from datetime import datetime


class HandlerBusinessService(BaseService):
    """
    Service layer containing business logic extracted from handlers.
    Coordinates between multiple services to provide high-level operations.
    """
    
    def __init__(self, context: IContext = None):
        super().__init__()
        self.context = context
        self.user_service = get_user_service(context)
        self.product_service = get_product_service(context)
        self.sales_service = get_sales_service(context)
    
    def process_login(self, request: LoginRequest) -> LoginResponse:
        """
        Process user login with complete validation and response.
        
        Args:
            request: Login request with username, password, chat_id
            
        Returns:
            LoginResponse with success status and user details
        """
        try:
            user = self.user_service.authenticate_user(
                request.username, 
                request.password, 
                request.chat_id
            )
            
            if user:
                return LoginResponse(
                    success=True,
                    user_id=user.id,
                    username=user.username,
                    level=user.level.value,
                    message="✅ Login realizado com sucesso!"
                )
            else:
                return LoginResponse(
                    success=False,
                    message="❌ Usuário ou senha inválidos."
                )
                
        except RuntimeError as e:
            self.logger.error(f"Database initialization error: {e}")
            return LoginResponse(
                success=False,
                message="❌ Erro de conexão com banco de dados. Sistema não inicializado."
            )
        except Exception as e:
            self.logger.error(f"Login process error: {e}", exc_info=True)
            return LoginResponse(
                success=False,
                message=f"❌ Erro interno durante login: {str(e)}"
            )
    
    def get_products_for_purchase(self, user_level: str, include_secret: bool = False) -> List[ProductWithStock]:
        """
        Get products available for purchase based on user level.
        
        Args:
            user_level: User's permission level
            include_secret: Whether to include secret products (🧪💀 emojis)
            
        Returns:
            List of products with stock information
        """
        try:
            products_with_stock = self.product_service.get_products_with_stock()
            
            # Filter secret products unless specifically requested
            if not include_secret:
                secret_emojis = set(get_secret_menu_emojis())
                filtered_products = []
                for pws in products_with_stock:
                    if pws.product.emoji not in secret_emojis:
                        filtered_products.append(pws)
                return filtered_products
            
            return products_with_stock
            
        except Exception as e:
            self.logger.error(f"Error getting products for purchase: {e}")
            raise ServiceError(f"Failed to get products: {str(e)}")
    
    def process_purchase(self, request: PurchaseRequest) -> PurchaseResponse:
        """
        Process complete purchase with inventory validation and updates.
        
        Args:
            request: Purchase request with buyer, items, total
            
        Returns:
            PurchaseResponse with success status and details
        """
        try:
            warnings = []
            
            # Validate inventory for all items
            for item in request.items:
                available_quantity = self.product_service.get_available_quantity(item.product_id)
                if available_quantity < item.quantity:
                    product = self.product_service.get_product_by_id(item.product_id)
                    warnings.append(f"Estoque insuficiente para {product.nome}: {available_quantity} disponível")
            
            if warnings:
                return PurchaseResponse(
                    success=False,
                    total_amount=request.total_amount,
                    message="❌ Estoque insuficiente para alguns itens.",
                    warnings=warnings
                )
            
            # Create sale items
            sale_items = []
            for item in request.items:
                from models.sale import CreateSaleItemRequest
                sale_items.append(CreateSaleItemRequest(
                    produto_id=item.product_id,
                    quantidade=item.quantity,
                    valor_unitario=item.custom_price or self._get_product_default_price(item.product_id)
                ))
            
            # Create the sale
            sale_request = CreateSaleRequest(
                comprador=request.buyer_name,
                items=sale_items
            )
            
            sale = self.sales_service.create_sale(sale_request)
            
            # Update inventory (FIFO)
            for item in request.items:
                self.product_service.consume_stock(item.product_id, item.quantity)
            
            return PurchaseResponse(
                success=True,
                sale_id=sale.id,
                total_amount=sale.get_total_value(),
                message=f"✅ Compra realizada com sucesso! ID: {sale.id}"
            )
            
        except Exception as e:
            self.logger.error(f"Purchase process error: {e}", exc_info=True)
            return PurchaseResponse(
                success=False,
                total_amount=request.total_amount,
                message=f"❌ Erro ao processar compra: {str(e)}"
            )
    
    def add_inventory(self, request: InventoryAddRequest) -> InventoryResponse:
        """
        Add inventory for a product with validation.
        
        Args:
            request: Inventory addition request
            
        Returns:
            InventoryResponse with success status and details
        """
        try:
            product = self.product_service.get_product_by_id(request.product_id)
            if not product:
                raise NotFoundError("Produto não encontrado")
            
            # Add inventory
            from models.product import AddStockRequest
            add_stock_request = AddStockRequest(
                produto_id=request.product_id,
                quantidade=request.quantity,
                valor=request.unit_price,
                custo=request.unit_cost
            )
            self.product_service.add_stock(add_stock_request)
            
            # Get updated total quantity
            new_total_quantity = self.product_service.get_available_quantity(request.product_id)
            
            return InventoryResponse(
                success=True,
                product_name=product.nome,
                added_quantity=request.quantity,
                new_total=new_total_quantity,
                message=f"✅ {request.quantity} unidades adicionadas ao estoque de {product.nome}"
            )
            
        except Exception as e:
            self.logger.error(f"Add inventory error: {e}")
            raise ServiceError(f"Erro ao adicionar estoque: {str(e)}")
    
    def generate_report(self, request: ReportRequest) -> ReportResponse:
        """
        Generate sales or debt reports with CSV export.
        
        Args:
            request: Report generation request
            
        Returns:
            ReportResponse with report data and optional CSV file
        """
        try:
            report_data = []
            summary = {}
            
            if request.report_type == "sales":
                # Get sales with filtering support
                sales = self._get_filtered_sales(request)
                
                # Build report data from sales with product details
                report_data = []
                if sales:
                    for sale in sales:
                        # Get sale items for this sale
                        items = self.sales_service.get_sale_items(sale.id)
                        for item in items:
                            # Get product name
                            product = self.product_service.get_product_by_id(item.produto_id)
                            product_name = product.nome if product else "Unknown Product"
                            
                            # Apply product name filter if specified
                            if request.product_name_filter and request.product_name_filter.lower() not in product_name.lower():
                                continue
                            
                            report_data.append({
                                'id': sale.id,
                                'comprador': sale.comprador,
                                'produto_nome': product_name,
                                'quantidade': item.quantidade,
                                'valor_total': item.get_total_value(),
                                'data_venda': sale.data.strftime('%Y-%m-%d') if hasattr(sale.data, 'strftime') else str(sale.data)
                            })
                
                summary = {
                    'total_sales': len(sales),
                    'total_revenue': sum(sale.get_total_value() for sale in sales),
                    'total_paid': 0.0,  # Will need to calculate payments separately
                    'total_debt': sum(sale.get_total_value() for sale in sales)  # Simplified for now
                }
                
            elif request.report_type == "debts":
                # Use existing method and treat all sales as debts for now
                # TODO: Implement proper debt tracking with payments
                if request.buyer_name:
                    sales = self.sales_service.get_sales_by_buyer(request.buyer_name)
                else:
                    sales = self.sales_service.get_sales_by_buyer()
                
                # Build report data from sales (treating all sales as debts for now)
                report_data = []
                if sales:
                    for sale in sales:
                        # Get sale items for this sale
                        items = self.sales_service.get_sale_items(sale.id)
                        for item in items:
                            # Get product name
                            product = self.product_service.get_product_by_id(item.produto_id)
                            product_name = product.nome if product else "Unknown Product"
                            
                            report_data.append({
                                'id': sale.id,
                                'produto_nome': product_name,
                                'quantidade': item.quantidade,
                                'valor_total': item.get_total_value(),  # Use the method instead of preco_total
                                'data_venda': sale.data.strftime('%Y-%m-%d') if hasattr(sale.data, 'strftime') else str(sale.data)
                            })
                
                summary = {
                    'total_debtors': len(set(sale.comprador for sale in sales)) if sales else 0,
                    'total_unpaid_sales': len(sales) if sales else 0,
                    'total_debt_amount': sum(sale.get_total_value() for sale in sales) if sales else 0.0
                }
            
            # Generate CSV file
            csv_file_path = None
            if report_data:
                csv_file_path = self._generate_csv_report(request.report_type, report_data)
            
            return ReportResponse(
                success=True,
                report_data=report_data,
                csv_file_path=csv_file_path,
                summary=summary,
                message=f"✅ Relatório de {request.report_type} gerado com sucesso!"
            )
            
        except Exception as e:
            self.logger.error(f"Report generation error: {e}")
            return ReportResponse(
                success=False,
                report_data=[],  # Required field
                message="❌ Erro ao gerar relatório."
            )
    
    def process_payment(self, request: PaymentRequest) -> PaymentResponse:
        """
        Process payment for a sale with debt calculation.
        
        Args:
            request: Payment request
            
        Returns:
            PaymentResponse with updated debt information
        """
        try:
            sale = self.sales_service.get_sale_by_id(request.sale_id)
            if not sale:
                raise NotFoundError("Venda não encontrada")
            
            # Add payment
            from models.sale import CreatePaymentRequest
            payment_request = CreatePaymentRequest(
                venda_id=request.sale_id,
                valor_pago=request.amount
            )
            self.sales_service.create_payment(payment_request)
            
            # Get updated sale with payments
            updated_sale = self.sales_service.get_sale_with_payments(request.sale_id)
            
            return PaymentResponse(
                success=True,
                remaining_debt=updated_sale.balance_due,
                total_paid=updated_sale.total_paid,
                is_fully_paid=updated_sale.is_fully_paid,
                message=f"✅ Pagamento de R$ {request.amount:.2f} registrado!"
            )
            
        except Exception as e:
            self.logger.error(f"Payment process error: {e}")
            raise ServiceError(f"Erro ao processar pagamento: {str(e)}")
    
    def manage_user(self, request: UserManagementRequest) -> UserManagementResponse:
        """
        Handle user management operations (add, edit, remove).
        
        Args:
            request: User management request
            
        Returns:
            UserManagementResponse with operation result
        """
        try:
            if request.action == "add":
                user_request = CreateUserRequest(
                    username=request.username,
                    password=request.password,
                    level=UserLevel.from_string(request.level)
                )
                user = self.user_service.create_user(user_request)
                
                return UserManagementResponse(
                    success=True,
                    user_id=user.id,
                    username=user.username,
                    level=user.level.value,
                    message=f"✅ Usuário {user.username} criado com sucesso!"
                )
                
            elif request.action == "edit":
                update_request = UpdateUserRequest(user_id=request.target_user_id)
                if request.username:
                    update_request.username = request.username
                if request.password:
                    update_request.password = request.password
                if request.level:
                    update_request.level = UserLevel.from_string(request.level)
                
                user = self.user_service.update_user(update_request)
                
                return UserManagementResponse(
                    success=True,
                    user_id=user.id,
                    username=user.username,
                    level=user.level.value,
                    message=f"✅ Usuário {user.username} atualizado com sucesso!"
                )
                
            elif request.action == "remove":
                self.user_service.delete_user(request.target_user_id)
                
                return UserManagementResponse(
                    success=True,
                    username=request.username,
                    message=f"✅ Usuário {request.username} removido com sucesso!"
                )
                
        except Exception as e:
            self.logger.error(f"User management error: {e}")
            return UserManagementResponse(
                success=False,
                username=request.username,
                message=f"❌ Erro ao {request.action} usuário: {str(e)}"
            )
    
    def _get_product_default_price(self, product_id: int) -> float:
        """Get default selling price for a product."""
        try:
            stock_entries = self.product_service.get_product_stock(product_id)
            if stock_entries:
                # Use FIFO - first entry's price
                return stock_entries[0].unit_price
            return 0.0
        except:
            return 0.0
    
    def _generate_csv_report(self, report_type: str, data: List[Dict]) -> str:
        """Generate CSV file for report data."""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8')
            
            if data:
                writer = csv.DictWriter(temp_file, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
            
            temp_file.close()
            return temp_file.name
            
        except Exception as e:
            self.logger.error(f"CSV generation error: {e}")
            return None
    
    def create_smartcontract(self, request: SmartContractRequest, chat_id: int) -> SmartContractResponse:
        """
        Create a new smart contract.
        
        Args:
            request: Smart contract creation request
            chat_id: Creator's chat ID
            
        Returns:
            SmartContractResponse with creation result
        """
        try:
            from core.modern_service_container import get_smartcontract_service
            smartcontract_service = get_smartcontract_service(self.context)
            
            contract_id = smartcontract_service.create_smart_contract(chat_id, request.contract_code)
            
            return SmartContractResponse(
                success=True,
                contract_id=request.contract_code,
                message=f"✅ Contrato `{request.contract_code}` criado com sucesso!"
            )
            
        except Exception as e:
            from services.base_service import DuplicateError
            if isinstance(e, DuplicateError):
                self.logger.warning(f"Duplicate smart contract: {e}")
                return SmartContractResponse(
                    success=False,
                    message=str(e)
                )
            else:
                self.logger.error(f"Smart contract creation error: {e}")
                return SmartContractResponse(
                    success=False,
                    message="❌ Erro interno ao criar contrato. Tente novamente."
                )
    
    def get_contract_by_code(self, chat_id: int, contract_code: str) -> Optional[Any]:
        """
        Get smart contract by code.

        Args:
            chat_id: User's chat ID
            contract_code: Contract code to search

        Returns:
            Contract data object with id, chat_id, code, and created_at attributes or None if not found
        """
        try:
            from core.modern_service_container import get_smartcontract_service
            smartcontract_service = get_smartcontract_service(self.context)
            
            result = smartcontract_service.get_smart_contract_by_code(chat_id, contract_code)
            
            if result:
                # Convert to object with id and code attributes for compatibility
                class ContractResult:
                    def __init__(self, data):
                        self.id = data[0]
                        self.chat_id = data[1] 
                        self.code = data[2]
                        self.created_at = data[3]
                return ContractResult(result)
            return None
            
        except Exception as e:
            self.logger.error(f"Get contract error: {e}")
            return None
    
    def handle_smartcontract_operation(self, request: SmartContractRequest, contract_id: int = None) -> SmartContractResponse:
        """
        Handle smart contract operations like adding transactions.
        
        Args:
            request: Smart contract operation request
            contract_id: Contract ID for operations
            
        Returns:
            SmartContractResponse with operation result
        """
        try:
            from core.modern_service_container import get_smartcontract_service
            smartcontract_service = get_smartcontract_service(self.context)
            
            if request.action == "add_transaction":
                transaction_id = smartcontract_service.add_transaction(contract_id, request.description, request.participant_chat_id)
                
                return SmartContractResponse(
                    success=True,
                    transaction_id=transaction_id,
                    message="✅ Transação adicionada com sucesso!"
                )
            
            return SmartContractResponse(
                success=False,
                message="❌ Operação não suportada."
            )
            
        except Exception as e:
            self.logger.error(f"Smart contract operation error: {e}")
            return SmartContractResponse(
                success=False,
                message=f"❌ Erro na operação: {str(e)}"
            )
    
    def get_contract_transactions(self, contract_id: int) -> List[Tuple[int, int, str, str, datetime]]:
        """
        Get all transactions for a contract.

        Args:
            contract_id: Contract ID

        Returns:
            List of tuples: (id, contract_id, description, participant_name, created_at)
        """
        try:
            from core.modern_service_container import get_smartcontract_service
            smartcontract_service = get_smartcontract_service(self.context)
            
            transactions = smartcontract_service.list_contract_transactions(contract_id)
            
            # Convert to objects with id and description attributes for compatibility
            class TransactionResult:
                def __init__(self, data):
                    self.id = data[0]
                    self.description = data[1]
            
            return [TransactionResult(t) for t in transactions]
            
        except Exception as e:
            self.logger.error(f"Get contract transactions error: {e}")
            return []
    
    def get_unpaid_sales(self, buyer_name: str = None):
        """
        Get unpaid sales, optionally filtered by buyer name.
        
        Args:
            buyer_name: Optional buyer name filter
            
        Returns:
            List of unpaid sales with payment information
        """
        try:
            return self.sales_service.get_unpaid_sales(buyer_name)
            
        except Exception as e:
            self.logger.error(f"Get unpaid sales error: {e}")
            return []
    
    def get_sale_with_payments(self, sale_id: int):
        """
        Get sale with payment information.
        
        Args:
            sale_id: Sale ID
            
        Returns:
            Sale with payment details or None
        """
        try:
            return self.sales_service.get_sale_with_payments(sale_id)
            
        except Exception as e:
            self.logger.error(f"Get sale with payments error: {e}")
            return None
    
    def user_exists(self, chat_id: int) -> bool:
        """
        Check if user exists.
        
        Args:
            chat_id: User's chat ID
            
        Returns:
            True if user exists, False otherwise
        """
        try:
            user = self.user_service.get_user_by_chat_id(chat_id)
            return user is not None
            
        except Exception as e:
            self.logger.error(f"User exists check error: {e}")
            return False
    
    def delete_user_data(self, chat_id: int) -> bool:
        """
        Delete all user data.
        
        Args:
            chat_id: User's chat ID
            
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            # This would need to be implemented in the user service
            # For now, return True as a placeholder
            return True
            
        except Exception as e:
            self.logger.error(f"Delete user data error: {e}")
            return False
    
    def _get_filtered_sales(self, request: ReportRequest) -> List[Sale]:
        """
        Get sales with filtering applied.
        
        Args:
            request: Report request with filter parameters
            
        Returns:
            List of filtered sales
        """
        # Start with buyer name filter (use new field with fallback to legacy)
        buyer_name = request.comprador_filter or request.buyer_name
        
        # Get base sales
        if buyer_name:
            sales = self.sales_service.get_sales_by_buyer(buyer_name)
        else:
            sales = self.sales_service.get_all_sales()
        
        # Apply date filtering if specified
        if request.start_date or request.end_date:
            filtered_sales = []
            for sale in sales:
                sale_date = sale.data.date() if hasattr(sale.data, 'date') else sale.data
                
                # Convert sale_date to datetime.date if it's a datetime object
                if hasattr(sale_date, 'strftime'):
                    try:
                        from datetime import datetime
                        sale_date = datetime.strptime(sale_date.strftime('%Y-%m-%d'), '%Y-%m-%d').date()
                    except:
                        continue
                
                include_sale = True
                
                if request.start_date:
                    start_date = request.start_date.date() if hasattr(request.start_date, 'date') else request.start_date
                    if sale_date < start_date:
                        include_sale = False
                
                if request.end_date and include_sale:
                    end_date = request.end_date.date() if hasattr(request.end_date, 'date') else request.end_date
                    if sale_date > end_date:
                        include_sale = False
                
                if include_sale:
                    filtered_sales.append(sale)
            
            sales = filtered_sales
        
        return sales