from typing import Optional, List
from services.base_service import BaseService, ServiceError, ValidationError, NotFoundError
# ProductService will be injected when needed to avoid circular dependencies
from models.sale import Sale, SaleItem, Payment, SaleWithPayments, CreateSaleRequest, CreatePaymentRequest
from utils.input_sanitizer import InputSanitizer
from core.interfaces import ISalesService


class SalesService(BaseService, ISalesService):
    """
    Service layer for sales management.
    Handles sale creation, payment processing, and debt tracking.
    """
    
    def __init__(self):
        super().__init__()
    
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
            # Get available stock directly from database
            stock_query = """
                SELECT COALESCE(SUM(quantidade), 0) as available_stock
                FROM estoque 
                WHERE produto_id = %s AND quantidade > 0
            """
            stock_row = self._execute_query(stock_query, (item.produto_id,), fetch_one=True)
            available_stock = stock_row[0] if stock_row else 0
            
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
            INSERT INTO Vendas (comprador, data_venda) 
            VALUES (%s, CURRENT_TIMESTAMP) 
            RETURNING id, comprador, data_venda
        """
        
        try:
            # Create sale
            sale_row = self._execute_query(sale_query, (comprador,), fetch_one=True)
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
                
                # Note: Stock consumption is handled by the business service layer
            
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
    
    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        """
        Get sale by ID with items.
        
        Args:
            sale_id: Sale ID
            
        Returns:
            Sale object with items if found, None otherwise
        """
        # Get sale
        sale_query = "SELECT id, comprador, data_venda FROM Vendas WHERE id = %s"
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
                query = "SELECT id, comprador, data_venda FROM Vendas WHERE comprador = %s ORDER BY data_venda DESC"
                params = (buyer_name,)
            except ValueError:
                return []  # Invalid buyer name, return empty list
        else:
            query = "SELECT id, comprador, data_venda FROM Vendas ORDER BY data_venda DESC"
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
                    SELECT v.id, v.comprador, v.data_venda,
                           COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) as total_sale,
                           COALESCE(SUM(p.valor_pago), 0) as total_paid
                    FROM Vendas v
                    LEFT JOIN ItensVenda iv ON v.id = iv.venda_id
                    LEFT JOIN Pagamentos p ON v.id = p.venda_id
                    WHERE v.comprador = %s
                    GROUP BY v.id, v.comprador, v.data_venda
                    HAVING COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) - COALESCE(SUM(p.valor_pago), 0) > 0.001
                    ORDER BY v.data_venda DESC
                """
                params = (buyer_name,)
            except ValueError:
                return []  # Invalid buyer name
        else:
            base_query = """
                SELECT v.id, v.comprador, v.data_venda,
                       COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) as total_sale,
                       COALESCE(SUM(p.valor_pago), 0) as total_paid
                FROM Vendas v
                LEFT JOIN ItensVenda iv ON v.id = iv.venda_id
                LEFT JOIN Pagamentos p ON v.id = p.venda_id
                GROUP BY v.id, v.comprador, v.data_venda
                HAVING COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) - COALESCE(SUM(p.valor_pago), 0) > 0.001
                ORDER BY v.data_venda DESC
            """
            params = ()

        rows = self._execute_query(base_query, params, fetch_all=True)

        unpaid_sales = []
        if rows:
            for row in rows:
                sale_data = row[:3]  # Sale data
                total_paid = float(row[4])

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
        
        Args:
            request: Payment creation request
            
        Returns:
            Created payment object
            
        Raises:
            ValidationError: If request is invalid
            NotFoundError: If sale doesn't exist
        """
        # Validate request
        errors = request.validate()
        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")
        
        # Check if sale exists
        sale = self.get_sale_by_id(request.venda_id)
        if not sale:
            raise NotFoundError(f"Sale with ID {request.venda_id} not found")
        
        # Create payment
        query = """
            INSERT INTO Pagamentos (venda_id, valor_pago)
            VALUES (%s, %s)
            RETURNING id, venda_id, valor_pago, data_pagamento
        """

        try:
            row = self._execute_query(
                query,
                (request.venda_id, request.valor_pago),
                fetch_one=True
            )

            if not row:
                raise ServiceError("Failed to create payment - no row returned")

            payment = Payment.from_db_row(row)

            # Add revenue to cash balance - CRITICAL for /saldo update
            try:
                from core.modern_service_container import get_cash_balance_service
                from decimal import Decimal

                cash_service = get_cash_balance_service()

                # Convert float to Decimal for cash balance service
                valor_decimal = Decimal(str(payment.valor_pago))

                cash_transaction = cash_service.add_revenue_from_payment(
                    pagamento_id=payment.id,
                    valor=valor_decimal,
                    venda_id=payment.venda_id
                )
                self.logger.info(f"SUCCESS: Payment R${payment.valor_pago} added to cash balance. New balance: R${cash_transaction.saldo_novo}")

            except Exception as cash_error:
                self.logger.error(f"CRITICAL: Failed to update cash balance for payment {payment.id}: {cash_error}", exc_info=True)
                # Still don't fail the payment creation, but log the error clearly

            self._log_operation(
                "payment_created",
                venda_id=request.venda_id,
                valor_pago=request.valor_pago,
                payment_id=payment.id
            )
            
            return payment
            
        except Exception as e:
            self.logger.error(f"Error creating payment for sale {request.venda_id}: {e}")
            raise ServiceError(f"Failed to create payment: {str(e)}")
    
    def get_buyer_debt_summary(self, buyer_name: Optional[str] = None) -> dict:
        """
        Get debt summary for a buyer or all buyers.
        
        Args:
            buyer_name: Buyer name (None for all buyers)
            
        Returns:
            Dictionary with debt summary information
        """
        if buyer_name:
            try:
                buyer_name = InputSanitizer.sanitize_buyer_name(buyer_name)
                query = """
                    SELECT 
                        v.comprador,
                        COUNT(DISTINCT v.id) as total_sales,
                        COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) as total_owed,
                        COALESCE(SUM(p.valor_pago), 0) as total_paid,
                        COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) - COALESCE(SUM(p.valor_pago), 0) as balance_due
                    FROM Vendas v
                    LEFT JOIN ItensVenda iv ON v.id = iv.venda_id
                    LEFT JOIN Pagamentos p ON v.id = p.venda_id
                    WHERE v.comprador = %s
                    GROUP BY v.comprador
                """
                params = (buyer_name,)
            except ValueError:
                return {"error": "Invalid buyer name"}
        else:
            query = """
                SELECT 
                    v.comprador,
                    COUNT(DISTINCT v.id) as total_sales,
                    COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) as total_owed,
                    COALESCE(SUM(p.valor_pago), 0) as total_paid,
                    COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) - COALESCE(SUM(p.valor_pago), 0) as balance_due
                FROM Vendas v
                LEFT JOIN ItensVenda iv ON v.id = iv.venda_id
                LEFT JOIN Pagamentos p ON v.id = p.venda_id
                GROUP BY v.comprador
                HAVING COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) - COALESCE(SUM(p.valor_pago), 0) > 0
                ORDER BY balance_due DESC
            """
            params = ()
        
        rows = self._execute_query(query, params, fetch_all=True)
        
        if buyer_name and rows:
            # Single buyer summary
            row = rows[0]
            return {
                "comprador": row[0],
                "total_sales": int(row[1]),
                "total_owed": float(row[2]),
                "total_paid": float(row[3]),
                "balance_due": float(row[4])
            }
        elif not buyer_name and rows:
            # All buyers summary
            summaries = []
            for row in rows:
                summaries.append({
                    "comprador": row[0],
                    "total_sales": int(row[1]),
                    "total_owed": float(row[2]),
                    "total_paid": float(row[3]),
                    "balance_due": float(row[4])
                })
            return {"buyers": summaries}
        else:
            return {"buyers": []} if not buyer_name else {"balance_due": 0.0}
    
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
    
    def _consume_stock_fifo(self, produto_id: int, quantidade: int):
        """
        Consume stock using FIFO (First In, First Out) method.
        
        Args:
            produto_id: Product ID
            quantidade: Quantity to consume
        """
        remaining_to_consume = quantidade
        
        # Get stock items ordered by date (FIFO)
        query = """
            SELECT id, quantidade 
            FROM estoque 
            WHERE produto_id = %s AND quantidade > 0 
            ORDER BY data ASC
        """
        
        stock_items = self._execute_query(query, (produto_id,), fetch_all=True)
        
        if not stock_items:
            raise ValidationError(f"No stock available for product {produto_id}")
        
        # Consume from oldest stock first
        for stock_id, stock_remaining in stock_items:
            if remaining_to_consume <= 0:
                break
                
            if stock_remaining >= remaining_to_consume:
                # This stock item can fulfill the remaining requirement
                new_remaining = stock_remaining - remaining_to_consume
                update_query = """
                    UPDATE Estoque 
                    SET quantidade = %s 
                    WHERE id = %s
                """
                self._execute_query(update_query, (new_remaining, stock_id))
                remaining_to_consume = 0
            else:
                # Consume all of this stock item
                update_query = """
                    UPDATE Estoque 
                    SET quantidade = 0 
                    WHERE id = %s
                """
                self._execute_query(update_query, (stock_id,))
                remaining_to_consume -= stock_remaining
        
        if remaining_to_consume > 0:
            raise ValidationError(f"Insufficient stock to consume {quantidade} units of product {produto_id}")