from typing import Optional, List, Dict, Tuple, TYPE_CHECKING
from datetime import datetime
from decimal import Decimal
from services.base_service import BaseService, ServiceError, ValidationError, NotFoundError
from services.financial_service import FinancialService
from services.product_repository import StockRepository
from services.expedition_integration_service import ExpeditionIntegrationService
from models.sale import Sale, SaleItem, Payment, SaleWithPayments, CreateSaleRequest, CreatePaymentRequest
from utils.input_sanitizer import InputSanitizer
from core.interfaces import ISalesService

if TYPE_CHECKING:
    from core.interfaces import IProductService


class SalesService(BaseService, ISalesService):
    """
    Service layer for sales management.
    Handles sale creation, payment processing, and debt tracking.
    Uses FinancialService for financial operations.
    """

    def __init__(self, product_service: Optional['IProductService'] = None):
        super().__init__()
        self._financial_service = FinancialService()
        self._stock_repository = StockRepository()
        self._expedition_integration = ExpeditionIntegrationService()
        self._product_service = product_service  # Lazy-loaded if needed

    @property
    def product_service(self) -> 'IProductService':
        """Lazy-load ProductService to avoid circular dependency."""
        if self._product_service is None:
            from core.modern_service_container import get_service_container
            container = get_service_container()
            self._product_service = container.get_service('IProductService')
        return self._product_service
    
    def create_sale(self, request: CreateSaleRequest) -> Sale:
        """
        Create a new sale with items.
        
        Args:
            request: Sale creation request
            
        Returns:
            Created sale object with items
            
        Raises:
            ValidationError: If request is invalid or insufficient stock
        """
        # Validate request
        errors = request.validate()
        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")
        
        # Sanitize buyer name
        try:
            comprador = InputSanitizer.sanitize_buyer_name(request.comprador)
        except ValueError as e:
            raise ValidationError(f"Invalid buyer name: {str(e)}")
        
        # Check stock availability for all items
        for item in request.items:
            # Use StockRepository to get available stock
            available_stock = self._stock_repository.get_available_quantity(item.produto_id)

            if available_stock < item.quantidade:
                # Get product name for error message
                product_query = "SELECT nome FROM Produtos WHERE id = %s"
                product_row = self._execute_query(product_query, (item.produto_id,), fetch_one=True)
                product_name = product_row[0] if product_row else f"Product {item.produto_id}"
                raise ValidationError(
                    f"Insufficient stock for {product_name}. "
                    f"Available: {available_stock}, Requested: {item.quantidade}"
                )
        
        # Create sale and items in transaction
        operations = []
        
        # Insert sale
        sale_query = """
            INSERT INTO Vendas (comprador, data_venda, expedition_id)
            VALUES (%s, CURRENT_TIMESTAMP, %s)
            RETURNING id, comprador, data_venda, expedition_id
        """
        
        try:
            # Create sale
            sale_row = self._execute_query(sale_query, (comprador, request.expedition_id), fetch_one=True)
            if not sale_row:
                raise ServiceError("Failed to create sale - no row returned")
            
            sale = Sale.from_db_row(sale_row)
            sale.items = []
            
            # Create sale items and consume stock
            for item_request in request.items:
                # Get product name for the sale item
                product_query = "SELECT nome FROM Produtos WHERE id = %s"
                product_row = self._execute_query(product_query, (item_request.produto_id,), fetch_one=True)
                if not product_row:
                    raise ValidationError(f"Product with ID {item_request.produto_id} not found")
                produto_nome = product_row[0]
                
                # Insert sale item
                item_query = """
                    INSERT INTO ItensVenda (venda_id, produto_id, quantidade, valor_unitario, produto_nome) 
                    VALUES (%s, %s, %s, %s, %s) 
                    RETURNING id, venda_id, produto_id, quantidade, valor_unitario, produto_nome
                """
                
                item_row = self._execute_query(
                    item_query, 
                    (sale.id, item_request.produto_id, item_request.quantidade, item_request.valor_unitario, produto_nome),
                    fetch_one=True
                )
                
                if not item_row:
                    raise ServiceError("Failed to create sale item")
                
                sale_item = SaleItem.from_db_row(item_row)
                sale.items.append(sale_item)

                # Consume stock using FIFO method from StockRepository
                self._stock_repository.consume_fifo(item_request.produto_id, item_request.quantidade)
            
            self._log_operation(
                "sale_created", 
                sale_id=sale.id, 
                comprador=comprador,
                total_value=sale.get_total_value(),
                items_count=len(sale.items)
            )
            
            return sale

        except Exception as e:
            self.logger.error(f"Error creating sale for {comprador}: {e}")
            raise ServiceError(f"Failed to create sale: {str(e)}")

    def create_expedition_sale(self, request: CreateSaleRequest) -> Sale:
        """
        Create a sale for expedition consumption without FIFO stock processing.

        This is a simplified version that only creates sale records for debt tracking,
        without any stock validation or consumption.

        Args:
            request: Sale creation request

        Returns:
            Created sale object with items

        Raises:
            ValidationError: If request is invalid
        """
        # Validate request
        errors = request.validate()
        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")

        # Sanitize buyer name
        try:
            comprador = InputSanitizer.sanitize_buyer_name(request.comprador)
        except ValueError as e:
            raise ValidationError(f"Invalid buyer name: {str(e)}")

        try:
            # Insert sale
            sale_query = """
                INSERT INTO Vendas (comprador, data_venda, expedition_id)
                VALUES (%s, CURRENT_TIMESTAMP, %s)
                RETURNING id, comprador, data_venda, expedition_id
            """

            sale_row = self._execute_query(sale_query, (comprador, request.expedition_id), fetch_one=True)
            if not sale_row:
                raise ServiceError("Failed to create sale - no row returned")

            sale = Sale.from_db_row(sale_row)
            sale.items = []

            # Create sale items
            for item_request in request.items:
                # Get product name for the sale item
                product_query = "SELECT nome FROM Produtos WHERE id = %s"
                product_row = self._execute_query(product_query, (item_request.produto_id,), fetch_one=True)
                if not product_row:
                    raise ValidationError(f"Product with ID {item_request.produto_id} not found")
                produto_nome = product_row[0]

                # Insert sale item
                item_query = """
                    INSERT INTO ItensVenda (venda_id, produto_id, quantidade, valor_unitario, produto_nome)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id, venda_id, produto_id, quantidade, valor_unitario, produto_nome
                """

                item_row = self._execute_query(
                    item_query,
                    (sale.id, item_request.produto_id, item_request.quantidade, item_request.valor_unitario, produto_nome),
                    fetch_one=True
                )

                if not item_row:
                    raise ServiceError("Failed to create sale item")

                sale_item = SaleItem.from_db_row(item_row)
                sale.items.append(sale_item)

            self._log_operation(
                "expedition_sale_created",
                sale_id=sale.id,
                comprador=comprador,
                expedition_id=request.expedition_id,
                total_value=sale.get_total_value(),
                items_count=len(sale.items)
            )

            return sale

        except Exception as e:
            self.logger.error(f"Error creating expedition sale for {comprador}: {e}")
            raise ServiceError(f"Failed to create expedition sale: {str(e)}")

    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        """
        Get sale by ID with items.
        
        Args:
            sale_id: Sale ID
            
        Returns:
            Sale object with items if found, None otherwise
        """
        # Get sale
        sale_query = "SELECT id, comprador, data_venda, expedition_id FROM Vendas WHERE id = %s"
        sale_row = self._execute_query(sale_query, (sale_id,), fetch_one=True)
        
        if not sale_row:
            return None
        
        sale = Sale.from_db_row(sale_row)
        
        # Get sale items
        items_query = """
            SELECT id, venda_id, produto_id, quantidade, valor_unitario, produto_nome 
            FROM ItensVenda 
            WHERE venda_id = %s 
            ORDER BY id
        """
        
        item_rows = self._execute_query(items_query, (sale_id,), fetch_all=True)
        
        sale.items = []
        if item_rows:
            for item_row in item_rows:
                sale_item = SaleItem.from_db_row(item_row)
                if sale_item:
                    sale.items.append(sale_item)
        
        return sale
    
    def get_sales_by_buyer(self, buyer_name: Optional[str] = None) -> List[Sale]:
        """
        Get sales by buyer name.
        
        Args:
            buyer_name: Buyer name to filter by (None for all sales)
            
        Returns:
            List of sales
        """
        if buyer_name:
            try:
                buyer_name = InputSanitizer.sanitize_buyer_name(buyer_name)
                query = "SELECT id, comprador, data_venda, expedition_id FROM Vendas WHERE comprador = %s ORDER BY data_venda DESC"
                params = (buyer_name,)
            except ValueError:
                return []  # Invalid buyer name, return empty list
        else:
            query = "SELECT id, comprador, data_venda, expedition_id FROM Vendas ORDER BY data_venda DESC"
            params = ()
        
        rows = self._execute_query(query, params, fetch_all=True)
        
        sales = []
        if rows:
            for row in rows:
                sale = Sale.from_db_row(row)
                if sale:
                    # Load items for each sale
                    full_sale = self.get_sale_by_id(sale.id)
                    if full_sale:
                        sales.append(full_sale)
        
        return sales
    
    def get_sale_items(self, sale_id: int) -> List['SaleItem']:
        """
        Get sale items for a specific sale.
        
        Args:
            sale_id: Sale ID to get items for
            
        Returns:
            List of sale items
        """
        from models.sale import SaleItem
        
        query = """
            SELECT id, venda_id, produto_id, quantidade, valor_unitario, produto_nome 
            FROM ItensVenda 
            WHERE venda_id = %s 
            ORDER BY id
        """
        
        rows = self._execute_query(query, (sale_id,), fetch_all=True)
        
        items = []
        if rows:
            for row in rows:
                item = SaleItem.from_db_row(row)
                if item:
                    items.append(item)
        
        return items
    
    def get_all_sales(self) -> List[Sale]:
        """
        Get all sales with items.
        
        Returns:
            List of all sales
        """
        return self.get_sales_by_buyer(None)
    
    def get_unpaid_sales(self, buyer_name: Optional[str] = None) -> List[SaleWithPayments]:
        """
        Get sales with outstanding balances.

        Args:
            buyer_name: Buyer name to filter by (None for all buyers)

        Returns:
            List of sales with payment information
        """
        # Build query
        if buyer_name:
            try:
                buyer_name = InputSanitizer.sanitize_buyer_name(buyer_name)
                base_query = """
                    SELECT v.id, v.comprador, v.data_venda, v.expedition_id,
                           COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) as total_sale,
                           COALESCE(SUM(p.valor_pago), 0) as total_paid
                    FROM Vendas v
                    LEFT JOIN ItensVenda iv ON v.id = iv.venda_id
                    LEFT JOIN Pagamentos p ON v.id = p.venda_id
                    WHERE v.comprador = %s
                    GROUP BY v.id, v.comprador, v.data_venda, v.expedition_id
                    HAVING COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) - COALESCE(SUM(p.valor_pago), 0) > 0.001
                    ORDER BY v.data_venda DESC
                """
                params = (buyer_name,)
            except ValueError:
                return []  # Invalid buyer name
        else:
            base_query = """
                SELECT v.id, v.comprador, v.data_venda, v.expedition_id,
                       COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) as total_sale,
                       COALESCE(SUM(p.valor_pago), 0) as total_paid
                FROM Vendas v
                LEFT JOIN ItensVenda iv ON v.id = iv.venda_id
                LEFT JOIN Pagamentos p ON v.id = p.venda_id
                GROUP BY v.id, v.comprador, v.data_venda, v.expedition_id
                HAVING COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) - COALESCE(SUM(p.valor_pago), 0) > 0.001
                ORDER BY v.data_venda DESC
            """
            params = ()

        rows = self._execute_query(base_query, params, fetch_all=True)

        unpaid_sales = []
        if rows:
            for row in rows:
                sale_data = row[:4]  # Sale data (id, comprador, data_venda, expedition_id)
                total_paid = float(row[5])

                # Get full sale with items
                sale = self.get_sale_by_id(row[0])
                if sale:
                    # Get payments
                    payments = self.get_payments_for_sale(sale.id)

                    sale_with_payments = SaleWithPayments(
                        sale=sale,
                        payments=payments,
                        total_paid=total_paid
                    )

                    # Double check that the balance is indeed unpaid (avoid floating point issues)
                    if sale_with_payments.balance_due > 0.001:
                        unpaid_sales.append(sale_with_payments)

        return unpaid_sales
    
    def get_payments_for_sale(self, sale_id: int) -> List[Payment]:
        """
        Get all payments for a sale.
        
        Args:
            sale_id: Sale ID
            
        Returns:
            List of payments
        """
        query = """
            SELECT id, venda_id, valor_pago, data_pagamento 
            FROM Pagamentos 
            WHERE venda_id = %s 
            ORDER BY data_pagamento DESC
        """
        
        rows = self._execute_query(query, (sale_id,), fetch_all=True)
        
        payments = []
        if rows:
            for row in rows:
                payment = Payment.from_db_row(row)
                if payment:
                    payments.append(payment)
        
        return payments
    
    def create_payment(self, request: CreatePaymentRequest) -> Payment:
        """
        Create a payment for a sale.
        Uses FinancialService for unified payment processing with cash balance integration.

        Args:
            request: Payment creation request

        Returns:
            Created payment object

        Raises:
            ValidationError: If request is invalid
            NotFoundError: If sale doesn't exist
        """
        try:
            # Use FinancialService for unified payment processing
            # This handles validation, sale existence check, payment creation, and cash balance updates
            return self._financial_service.process_payment(request)
        except Exception as e:
            self.logger.error(f"Error creating payment for sale {request.venda_id}: {e}")
            if isinstance(e, (ValidationError, NotFoundError)):
                raise
            raise ServiceError(f"Failed to create payment: {str(e)}")
    
    def get_buyer_debt_summary(self, buyer_name: Optional[str] = None) -> dict:
        """
        Get debt summary for a buyer or all buyers.
        Uses FinancialService for unified debt calculations.

        Args:
            buyer_name: Buyer name (None for all buyers)

        Returns:
            Dictionary with debt summary information
        """
        try:
            return self._financial_service.calculate_debt_summary(buyer_name)
        except Exception as e:
            self.logger.error(f"Error getting debt summary for {buyer_name}: {e}")
            return {"error": f"Failed to calculate debt summary: {str(e)}"}
    
    def add_payment(self, request: CreatePaymentRequest) -> Payment:
        """
        Add a payment to a sale (alias for create_payment to satisfy interface).
        
        Args:
            request: Payment creation request
            
        Returns:
            Created payment object
        """
        return self.create_payment(request)
    
    def get_sale_with_payments(self, sale_id: int) -> Optional[SaleWithPayments]:
        """
        Get sale with all payment information.
        
        Args:
            sale_id: Sale ID
            
        Returns:
            Sale with payments or None if not found
        """
        # Get the base sale
        sale = self.get_sale_by_id(sale_id)
        if not sale:
            return None
        
        # Get all payments for this sale
        payments = self.get_payments_for_sale(sale_id)
        
        # Calculate totals
        total_paid = sum(payment.valor_pago for payment in payments)
        
        # Calculate total amount from sale items
        total_amount = sum(item.quantidade * item.valor_unitario for item in sale.items)
        
        # Create SaleWithPayments object
        return SaleWithPayments(
            sale=sale,
            payments=payments,
            total_paid=total_paid
        )
    

    def get_sales_by_expedition(self, expedition_id: int) -> List[Sale]:
        """
        Get all sales linked to a specific expedition.

        Args:
            expedition_id: Expedition ID to filter by

        Returns:
            List of sales for the expedition
        """
        query = "SELECT id, comprador, data_venda, expedition_id FROM Vendas WHERE expedition_id = %s ORDER BY data_venda DESC"

        rows = self._execute_query(query, (expedition_id,), fetch_all=True)

        sales = []
        if rows:
            for row in rows:
                sale = Sale.from_db_row(row)
                if sale:
                    # Load items for each sale
                    full_sale = self.get_sale_by_id(sale.id)
                    if full_sale:
                        sales.append(full_sale)

        return sales

    def create_expedition_linked_sale(self, request: CreateSaleRequest) -> Sale:
        """
        Create a sale linked to an expedition and automatically track item consumption.
        This method ensures that expedition items are properly consumed when sales are created.

        Args:
            request: Sale creation request with expedition_id

        Returns:
            Created sale object

        Raises:
            ValidationError: If expedition validation fails
        """
        if not request.expedition_id:
            return self.create_sale(request)

        # Validate expedition exists and is active
        from core.modern_service_container import get_expedition_service
        expedition_service = get_expedition_service()

        expedition = expedition_service.get_expedition_by_id(request.expedition_id)
        if not expedition:
            raise ValidationError(f"Expedition {request.expedition_id} not found")

        if not expedition.is_active():
            raise ValidationError("Cannot create sales for inactive expeditions")

        # Create the sale normally
        sale = self.create_sale(request)

        # Auto-track expedition item consumption for each sale item
        expedition_items = expedition_service.get_expedition_items(request.expedition_id)

        for sale_item in sale.items:
            # Find matching expedition item
            matching_expedition_item = None
            for exp_item in expedition_items:
                if exp_item.produto_id == sale_item.produto_id:
                    matching_expedition_item = exp_item
                    break

            if matching_expedition_item:
                try:
                    # Create consumption record for the expedition item
                    from models.expedition import ItemConsumptionRequest
                    consumption_request = ItemConsumptionRequest(
                        expedition_item_id=matching_expedition_item.id,
                        consumer_name=sale.comprador,
                        pirate_name=f"Pirate {sale.comprador[:3]}",  # Simple pirate name for now
                        quantity_consumed=sale_item.quantidade,
                        unit_price=sale_item.valor_unitario
                    )

                    expedition_service.consume_item(consumption_request)
                    self._log_operation(
                        "expedition_item_consumed",
                        sale_id=sale.id,
                        expedition_id=request.expedition_id,
                        produto_id=sale_item.produto_id,
                        quantity=sale_item.quantidade
                    )

                except Exception as e:
                    self.logger.warning(f"Failed to track expedition consumption for sale {sale.id}: {e}")
                    # Don't fail the sale creation, just log the issue

        # Check if expedition is now complete
        try:
            expedition_service.check_expedition_completion(request.expedition_id)
        except Exception as e:
            self.logger.warning(f"Failed to check expedition completion: {e}")

        return sale

    # === EXPEDITION INTEGRATION - Delegated to ExpeditionIntegrationService ===

    def map_pirate_to_buyer(self, expedition_id: int, pirate_name: str, buyer_username: str,
                           owner_key: str) -> bool:
        """Delegate to ExpeditionIntegrationService."""
        return self._expedition_integration.map_pirate_to_buyer(
            expedition_id, pirate_name, buyer_username, owner_key
        )

    def get_buyer_for_pirate(self, expedition_id: int, pirate_name: str) -> Optional[str]:
        """Delegate to ExpeditionIntegrationService."""
        return self._expedition_integration.get_buyer_for_pirate(expedition_id, pirate_name)

    def get_pirate_for_buyer(self, expedition_id: int, buyer_username: str) -> Optional[str]:
        """Delegate to ExpeditionIntegrationService."""
        return self._expedition_integration.get_pirate_for_buyer(expedition_id, buyer_username)

    def sync_expedition_debt_to_main_system(self, expedition_id: int) -> Dict[str, any]:
        """Delegate to ExpeditionIntegrationService."""
        return self._expedition_integration.sync_expedition_debt_to_main_system(expedition_id)

    def create_integrated_sale_record(self, expedition_id: int, pirate_name: str,
                                    product_name: str, quantity: int, total_price: Decimal,
                                    product_emoji: str = "") -> bool:
        """
        Create a sale record in the main system for an expedition consumption.

        Args:
            expedition_id: Expedition identifier
            pirate_name: Anonymized pirate name
            product_name: Product name
            quantity: Quantity consumed
            total_price: Total price
            product_emoji: Product emoji

        Returns:
            True if sale record was created successfully
        """
        self._log_operation("CreateIntegratedSale",
                          expedition_id=expedition_id,
                          pirate_name=pirate_name,
                          product_name=product_name)

        try:
            # Get real buyer username
            buyer_username = self.get_buyer_for_pirate(expedition_id, pirate_name)

            if not buyer_username:
                self.logger.warning(f"No buyer mapping found for pirate {pirate_name} in expedition {expedition_id}")
                return False

            # Create sale record in main system
            sale_query = """
                INSERT INTO vendas (nome_comprador, produto, quantidade, preco_total, data_venda, emoji_produto)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """

            sale_values = (
                buyer_username,
                product_name,
                quantity,
                float(total_price),
                datetime.now(),
                product_emoji
            )

            result = self._execute_query(sale_query, sale_values, fetch_one=True)

            if result:
                sale_id = result[0]
                self.logger.info(f"Created integrated sale record {sale_id} for expedition {expedition_id}")
                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Failed to create integrated sale record: {e}", exc_info=True)
            return False

    def record_expedition_payment(self, expedition_id: int, pirate_name: str,
                                 payment_amount: Decimal, payment_method: str = "expedition",
                                 payment_notes: Optional[str] = None) -> bool:
        """
        Record a payment in the expedition payments system.

        Args:
            expedition_id: Expedition identifier
            pirate_name: Anonymized pirate name
            payment_amount: Payment amount
            payment_method: Payment method
            payment_notes: Optional payment notes

        Returns:
            True if payment was recorded successfully
        """
        self._log_operation("RecordExpeditionPayment",
                          expedition_id=expedition_id,
                          pirate_name=pirate_name,
                          payment_amount=payment_amount)

        try:
            # Insert payment record
            payment_query = """
                INSERT INTO expedition_payments
                (expedition_id, pirate_name, payment_amount, payment_method, payment_notes, payment_date, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """

            now = datetime.now()
            payment_values = (
                expedition_id,
                pirate_name,
                float(payment_amount),
                payment_method,
                payment_notes,
                now,
                now
            )

            result = self._execute_query(payment_query, payment_values, fetch_one=True)

            if result:
                payment_id = result[0]
                self.logger.info(f"Recorded expedition payment {payment_id}")

                # Also record in main payment system if buyer mapping exists
                buyer_username = self.get_buyer_for_pirate(expedition_id, pirate_name)
                if buyer_username:
                    self._record_main_system_payment(buyer_username, payment_amount, f"Expedition {expedition_id} payment")

                return True
            else:
                return False

        except Exception as e:
            self.logger.error(f"Failed to record expedition payment: {e}", exc_info=True)
            return False

    def get_expedition_financial_summary(self, expedition_id: int) -> Dict[str, any]:
        """
        Get financial summary for an expedition including debt and payment totals.

        Args:
            expedition_id: Expedition identifier

        Returns:
            Dictionary with financial summary
        """
        try:
            # Get assignment totals
            assignment_query = """
                SELECT
                    COUNT(*) as total_assignments,
                    SUM(CASE WHEN assignment_status = 'completed' THEN actual_amount ELSE assignment_amount END) as total_debt,
                    SUM(CASE WHEN assignment_status = 'completed' THEN actual_amount ELSE 0 END) as consumed_debt,
                    SUM(CASE WHEN assignment_status IN ('assigned', 'partially_consumed') THEN assignment_amount ELSE 0 END) as pending_debt
                FROM expedition_assignments
                WHERE expedition_id = %s
            """

            assignment_result = self._execute_query(assignment_query, (expedition_id,), fetch_one=True)

            # Get payment totals
            payment_query = """
                SELECT
                    COUNT(*) as total_payments,
                    SUM(payment_amount) as total_paid
                FROM expedition_payments
                WHERE expedition_id = %s
            """

            payment_result = self._execute_query(payment_query, (expedition_id,), fetch_one=True)

            # Calculate summary
            total_debt = Decimal(str(assignment_result[1] or 0)) if assignment_result else Decimal('0')
            total_paid = Decimal(str(payment_result[1] or 0)) if payment_result else Decimal('0')
            outstanding_balance = total_debt - total_paid

            return {
                'total_assignments': assignment_result[0] if assignment_result else 0,
                'total_debt': total_debt,
                'consumed_debt': Decimal(str(assignment_result[2] or 0)) if assignment_result else Decimal('0'),
                'pending_debt': Decimal(str(assignment_result[3] or 0)) if assignment_result else Decimal('0'),
                'total_payments': payment_result[0] if payment_result else 0,
                'total_paid': total_paid,
                'outstanding_balance': outstanding_balance,
                'payment_completion_rate': (total_paid / total_debt * 100) if total_debt > 0 else 0
            }

        except Exception as e:
            self.logger.error(f"Failed to get financial summary: {e}", exc_info=True)
            raise ServiceError(f"Financial summary failed: {str(e)}")

