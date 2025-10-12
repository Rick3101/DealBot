from typing import Optional, List, Dict, Any, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from services.base_service import BaseService, ServiceError, ValidationError, NotFoundError
from models.sale import Payment, CreatePaymentRequest
from models.cash_balance import CashBalance, CashTransaction, CreateCashTransactionRequest, RevenueReport
from utils.input_sanitizer import InputSanitizer


class FinancialService(BaseService):
    """
    Unified financial operations and calculations.
    Consolidates debt calculations, payment processing, and financial reporting.
    """

    def __init__(self):
        super().__init__()

    def calculate_debt_summary(self, buyer_name: Optional[str] = None) -> Dict:
        """
        Unified debt calculation logic.

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

    def process_payment(self, payment_request: CreatePaymentRequest) -> Payment:
        """
        Unified payment processing with cash balance integration.

        Args:
            payment_request: Payment creation request

        Returns:
            Created payment object

        Raises:
            ValidationError: If payment is invalid
            NotFoundError: If sale doesn't exist
        """
        # Validate payment request
        errors = payment_request.validate()
        if errors:
            raise ValidationError(f"Payment validation failed: {', '.join(errors)}")

        # Check if sale exists
        sale_query = "SELECT id, comprador FROM Vendas WHERE id = %s"
        sale_row = self._execute_query(sale_query, (payment_request.venda_id,), fetch_one=True)

        if not sale_row:
            raise NotFoundError(f"Sale with ID {payment_request.venda_id} not found")

        buyer_name = sale_row[1]

        try:
            # Create payment and update cash balance in transaction
            operations = []

            # Insert payment
            payment_query = """
                INSERT INTO Pagamentos (venda_id, valor_pago, data_pagamento, metodo_pagamento, observacoes)
                VALUES (%s, %s, CURRENT_TIMESTAMP, %s, %s)
                RETURNING id, venda_id, valor_pago, data_pagamento, metodo_pagamento, observacoes
            """
            operations.append((
                payment_query,
                (
                    payment_request.venda_id,
                    payment_request.valor_pago,
                    payment_request.metodo_pagamento or 'cash',
                    payment_request.observacoes
                )
            ))

            # Update cash balance
            balance_query = """
                INSERT INTO CashBalance (saldo_atual, data_atualizacao)
                VALUES (
                    (SELECT COALESCE(saldo_atual, 0) + %s FROM CashBalance ORDER BY data_atualizacao DESC LIMIT 1),
                    CURRENT_TIMESTAMP
                )
            """
            operations.append((balance_query, (payment_request.valor_pago,)))

            # Log cash transaction
            transaction_query = """
                INSERT INTO CashTransactions (tipo, valor, descricao, venda_id, data_transacao)
                VALUES ('payment', %s, %s, %s, CURRENT_TIMESTAMP)
            """
            transaction_description = f"Payment from {buyer_name} for sale #{payment_request.venda_id}"
            operations.append((
                transaction_query,
                (payment_request.valor_pago, transaction_description, payment_request.venda_id)
            ))

            # Execute all operations in transaction
            if not self._execute_transaction(operations):
                raise ServiceError("Failed to process payment - transaction failed")

            # Fetch the created payment
            payment_fetch_query = """
                SELECT id, venda_id, valor_pago, data_pagamento, metodo_pagamento, observacoes
                FROM Pagamentos
                WHERE venda_id = %s
                ORDER BY data_pagamento DESC
                LIMIT 1
            """
            payment_row = self._execute_query(payment_fetch_query, (payment_request.venda_id,), fetch_one=True)

            if not payment_row:
                raise ServiceError("Payment created but could not be retrieved")

            payment = Payment.from_db_row(payment_row)

            self._log_operation(
                "payment_processed",
                venda_id=payment_request.venda_id,
                valor_pago=payment_request.valor_pago,
                payment_id=payment.id,
                buyer_name=buyer_name
            )

            return payment

        except Exception as e:
            self.logger.error(f"Error processing payment for sale {payment_request.venda_id}: {e}")
            if isinstance(e, (ValidationError, NotFoundError)):
                raise
            raise ServiceError(f"Failed to process payment: {str(e)}")

    def calculate_expedition_financials(self, expedition_id: int) -> Dict:
        """
        Expedition-specific financial calculations.

        Args:
            expedition_id: Expedition ID

        Returns:
            Dictionary with expedition financial summary
        """
        try:
            # Get expedition details
            expedition_query = """
                SELECT id, name, description, deadline, created_at, status
                FROM Expeditions
                WHERE id = %s
            """
            expedition_row = self._execute_query(expedition_query, (expedition_id,), fetch_one=True)

            if not expedition_row:
                raise NotFoundError(f"Expedition with ID {expedition_id} not found")

            # Calculate expedition item costs and revenues
            financial_query = """
                SELECT
                    COUNT(DISTINCT ei.id) as total_items,
                    COALESCE(SUM(ei.target_price * ei.quantity), 0) as total_target_value,
                    COALESCE(SUM(ic.sale_price * ic.quantity_consumed), 0) as total_revenue,
                    COALESCE(SUM(ic.cost_price * ic.quantity_consumed), 0) as total_cost,
                    COALESCE(SUM(ic.quantity_consumed), 0) as total_items_sold,
                    COALESCE(SUM(ei.quantity), 0) as total_items_planned
                FROM Expedition_Items ei
                LEFT JOIN Item_Consumptions ic ON ei.id = ic.expedition_item_id
                WHERE ei.expedition_id = %s
            """
            financial_row = self._execute_query(financial_query, (expedition_id,), fetch_one=True)

            if financial_row:
                total_items = int(financial_row[0])
                total_target_value = float(financial_row[1])
                total_revenue = float(financial_row[2])
                total_cost = float(financial_row[3])
                total_items_sold = int(financial_row[4])
                total_items_planned = int(financial_row[5])

                profit_loss = total_revenue - total_cost
                profit_margin = (profit_loss / total_revenue * 100) if total_revenue > 0 else 0
                completion_rate = (total_items_sold / total_items_planned * 100) if total_items_planned > 0 else 0

                return {
                    "expedition_id": expedition_id,
                    "expedition_name": expedition_row[1],
                    "status": expedition_row[5],
                    "financial_summary": {
                        "total_items": total_items,
                        "total_target_value": total_target_value,
                        "total_revenue": total_revenue,
                        "total_cost": total_cost,
                        "profit_loss": profit_loss,
                        "profit_margin": round(profit_margin, 2),
                        "completion_rate": round(completion_rate, 2),
                        "items_sold": total_items_sold,
                        "items_planned": total_items_planned
                    }
                }
            else:
                return {
                    "expedition_id": expedition_id,
                    "expedition_name": expedition_row[1],
                    "status": expedition_row[5],
                    "financial_summary": {
                        "total_items": 0,
                        "total_target_value": 0.0,
                        "total_revenue": 0.0,
                        "total_cost": 0.0,
                        "profit_loss": 0.0,
                        "profit_margin": 0.0,
                        "completion_rate": 0.0,
                        "items_sold": 0,
                        "items_planned": 0
                    }
                }

        except Exception as e:
            self.logger.error(f"Error calculating expedition financials for expedition {expedition_id}: {e}")
            if isinstance(e, NotFoundError):
                raise
            raise ServiceError(f"Failed to calculate expedition financials: {str(e)}")

    def generate_financial_report(self, filters: Dict) -> Dict:
        """
        Generate comprehensive financial reports.

        Args:
            filters: Dictionary with report filters (date_from, date_to, buyer_name, etc.)

        Returns:
            Dictionary with financial report data
        """
        try:
            date_from = filters.get('date_from')
            date_to = filters.get('date_to')
            buyer_name = filters.get('buyer_name')

            # Build base query with filters
            where_clauses = []
            params = []

            if date_from:
                where_clauses.append("v.data_venda >= %s")
                params.append(date_from)

            if date_to:
                where_clauses.append("v.data_venda <= %s")
                params.append(date_to)

            if buyer_name:
                where_clauses.append("v.comprador = %s")
                params.append(buyer_name)

            where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"

            # Sales summary
            sales_query = f"""
                SELECT
                    COUNT(DISTINCT v.id) as total_sales,
                    COUNT(DISTINCT v.comprador) as unique_buyers,
                    COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) as total_sales_value,
                    COALESCE(AVG(iv.quantidade * iv.valor_unitario), 0) as avg_sale_value
                FROM Vendas v
                LEFT JOIN ItensVenda iv ON v.id = iv.venda_id
                WHERE {where_clause}
            """

            sales_row = self._execute_query(sales_query, tuple(params), fetch_one=True)

            # Payments summary
            payments_query = f"""
                SELECT
                    COUNT(p.id) as total_payments,
                    COALESCE(SUM(p.valor_pago), 0) as total_payments_value,
                    COALESCE(AVG(p.valor_pago), 0) as avg_payment_value
                FROM Pagamentos p
                JOIN Vendas v ON p.venda_id = v.id
                WHERE {where_clause}
            """

            payments_row = self._execute_query(payments_query, tuple(params), fetch_one=True)

            # Top buyers by debt
            top_buyers_query = f"""
                SELECT
                    v.comprador,
                    COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) as total_owed,
                    COALESCE(SUM(p.valor_pago), 0) as total_paid,
                    COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) - COALESCE(SUM(p.valor_pago), 0) as balance_due
                FROM Vendas v
                LEFT JOIN ItensVenda iv ON v.id = iv.venda_id
                LEFT JOIN Pagamentos p ON v.id = p.venda_id
                WHERE {where_clause}
                GROUP BY v.comprador
                HAVING COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) - COALESCE(SUM(p.valor_pago), 0) > 0
                ORDER BY balance_due DESC
                LIMIT 10
            """

            top_buyers_rows = self._execute_query(top_buyers_query, tuple(params), fetch_all=True)

            # Compile report
            report = {
                "report_generated": datetime.now().isoformat(),
                "filters": filters,
                "sales_summary": {
                    "total_sales": int(sales_row[0]) if sales_row else 0,
                    "unique_buyers": int(sales_row[1]) if sales_row else 0,
                    "total_sales_value": float(sales_row[2]) if sales_row else 0.0,
                    "avg_sale_value": float(sales_row[3]) if sales_row else 0.0
                },
                "payments_summary": {
                    "total_payments": int(payments_row[0]) if payments_row else 0,
                    "total_payments_value": float(payments_row[1]) if payments_row else 0.0,
                    "avg_payment_value": float(payments_row[2]) if payments_row else 0.0
                },
                "outstanding_debt": {
                    "total_outstanding": float(sales_row[2]) - float(payments_row[1]) if sales_row and payments_row else 0.0,
                    "payment_rate": (float(payments_row[1]) / float(sales_row[2]) * 100) if sales_row and payments_row and float(sales_row[2]) > 0 else 0.0
                },
                "top_debtors": []
            }

            # Add top buyers
            if top_buyers_rows:
                for row in top_buyers_rows:
                    report["top_debtors"].append({
                        "buyer_name": row[0],
                        "total_owed": float(row[1]),
                        "total_paid": float(row[2]),
                        "balance_due": float(row[3])
                    })

            self._log_operation("financial_report_generated", filters=filters, total_sales=report["sales_summary"]["total_sales"])

            return report

        except Exception as e:
            self.logger.error(f"Error generating financial report: {e}")
            raise ServiceError(f"Failed to generate financial report: {str(e)}")

    def get_cash_balance_history(self, days: int = 30) -> List[Dict]:
        """
        Get cash balance history for the specified number of days.

        Args:
            days: Number of days to look back

        Returns:
            List of cash balance entries
        """
        try:
            query = """
                SELECT id, saldo_atual, data_atualizacao
                FROM CashBalance
                WHERE data_atualizacao >= %s
                ORDER BY data_atualizacao DESC
            """
            cutoff_date = datetime.now() - timedelta(days=days)
            rows = self._execute_query(query, (cutoff_date,), fetch_all=True)

            balance_history = []
            if rows:
                for row in rows:
                    balance_history.append({
                        "id": int(row[0]),
                        "balance": float(row[1]),
                        "timestamp": row[2].isoformat() if hasattr(row[2], 'isoformat') else str(row[2])
                    })

            return balance_history

        except Exception as e:
            self.logger.error(f"Error getting cash balance history: {e}")
            raise ServiceError(f"Failed to get cash balance history: {str(e)}")

    def get_current_cash_balance(self) -> Dict:
        """
        Get current cash balance.

        Returns:
            Dictionary with current balance information
        """
        try:
            query = """
                SELECT id, saldo_atual, data_atualizacao
                FROM CashBalance
                ORDER BY data_atualizacao DESC
                LIMIT 1
            """
            row = self._execute_query(query, fetch_one=True)

            if row:
                return {
                    "id": int(row[0]),
                    "current_balance": float(row[1]),
                    "last_updated": row[2].isoformat() if hasattr(row[2], 'isoformat') else str(row[2])
                }
            else:
                # Initialize with zero balance
                return {
                    "id": 0,
                    "current_balance": 0.0,
                    "last_updated": datetime.now().isoformat(),
                    "message": "No balance records found - initialized to zero"
                }

        except Exception as e:
            self.logger.error(f"Error getting current cash balance: {e}")
            raise ServiceError(f"Failed to get current cash balance: {str(e)}")

    def calculate_profit_loss_statement(self, date_from: Optional[datetime] = None,
                                      date_to: Optional[datetime] = None) -> Dict:
        """
        Generate profit and loss statement.

        Args:
            date_from: Start date (default: 30 days ago)
            date_to: End date (default: now)

        Returns:
            Dictionary with P&L statement
        """
        try:
            if not date_from:
                date_from = datetime.now() - timedelta(days=30)
            if not date_to:
                date_to = datetime.now()

            # Revenue from sales
            revenue_query = """
                SELECT COALESCE(SUM(p.valor_pago), 0) as total_revenue
                FROM Pagamentos p
                WHERE p.data_pagamento >= %s AND p.data_pagamento <= %s
            """
            revenue_row = self._execute_query(revenue_query, (date_from, date_to), fetch_one=True)
            total_revenue = float(revenue_row[0]) if revenue_row else 0.0

            # Cost of goods sold (from item consumptions)
            cogs_query = """
                SELECT COALESCE(SUM(ic.cost_price * ic.quantity_consumed), 0) as total_cogs
                FROM Item_Consumptions ic
                WHERE ic.consumption_date >= %s AND ic.consumption_date <= %s
            """
            cogs_row = self._execute_query(cogs_query, (date_from, date_to), fetch_one=True)
            total_cogs = float(cogs_row[0]) if cogs_row else 0.0

            # Calculate metrics
            gross_profit = total_revenue - total_cogs
            gross_margin = (gross_profit / total_revenue * 100) if total_revenue > 0 else 0

            return {
                "period": {
                    "from": date_from.isoformat(),
                    "to": date_to.isoformat()
                },
                "revenue": {
                    "total_revenue": total_revenue
                },
                "costs": {
                    "cost_of_goods_sold": total_cogs
                },
                "profit": {
                    "gross_profit": gross_profit,
                    "gross_margin_percent": round(gross_margin, 2)
                },
                "generated_at": datetime.now().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Error calculating P&L statement: {e}")
            raise ServiceError(f"Failed to calculate P&L statement: {str(e)}")