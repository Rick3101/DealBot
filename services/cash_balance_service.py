"""
Service for managing cash balance and revenue tracking.
Handles balance updates, transaction logging, and revenue reports.
"""

from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from services.base_service import BaseService, ServiceError, ValidationError
from core.interfaces import ICashBalanceService
from models.cash_balance import (
    CashBalance, CashTransaction, CreateCashTransactionRequest,
    RevenueReport, CashBalanceHistory
)


class CashBalanceService(BaseService, ICashBalanceService):
    """Service for cash balance and revenue management."""

    def get_current_balance(self) -> CashBalance:
        """Get the current cash balance."""
        try:
            query = """
                SELECT id, saldo_atual, data_atualizacao
                FROM CashBalance
                ORDER BY data_atualizacao DESC
                LIMIT 1
            """
            row = self._execute_query(query, fetch_one=True)

            if not row:
                # Initialize with zero balance if none exists
                return self._initialize_balance()

            return CashBalance.from_db_row(row)

        except Exception as e:
            self.logger.error(f"Failed to get current balance: {e}")
            raise ServiceError(f"Failed to get current balance: {str(e)}")

    def _initialize_balance(self) -> CashBalance:
        """Initialize cash balance with zero."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO CashBalance (saldo_atual, data_atualizacao)
                        VALUES (%s, CURRENT_TIMESTAMP)
                        RETURNING id, saldo_atual, data_atualizacao
                    """, (Decimal('0.00'),))

                    row = cursor.fetchone()
                    conn.commit()

                    return CashBalance.from_db_row(row)

        except Exception as e:
            self.logger.error(f"Failed to initialize balance: {e}")
            raise ServiceError(f"Failed to initialize balance: {str(e)}")

    def add_revenue_from_payment(self, pagamento_id: int, valor: Decimal, venda_id: Optional[int] = None) -> CashTransaction:
        """
        Add revenue from a payment to cash balance.
        This is called automatically when payments are received.
        """
        try:
            request = CreateCashTransactionRequest(
                tipo='receita',
                valor=valor,
                descricao=f'Pagamento recebido - ID: {pagamento_id}',
                venda_id=venda_id,
                pagamento_id=pagamento_id
            )

            return self._create_transaction(request)

        except Exception as e:
            self.logger.error(f"Failed to add revenue from payment {pagamento_id}: {e}")
            raise ServiceError(f"Failed to add revenue: {str(e)}")

    def add_expense(self, valor: Decimal, descricao: str, usuario_chat_id: Optional[int] = None) -> CashTransaction:
        """Add an expense (reduces cash balance)."""
        try:
            request = CreateCashTransactionRequest(
                tipo='despesa',
                valor=valor,
                descricao=descricao,
                usuario_chat_id=usuario_chat_id
            )

            return self._create_transaction(request)

        except Exception as e:
            self.logger.error(f"Failed to add expense: {e}")
            raise ServiceError(f"Failed to add expense: {str(e)}")

    def adjust_balance(self, valor: Decimal, descricao: str, usuario_chat_id: Optional[int] = None) -> CashTransaction:
        """
        Make a manual balance adjustment.
        Positive value increases balance, negative decreases.
        """
        try:
            request = CreateCashTransactionRequest(
                tipo='ajuste',
                valor=abs(valor),  # Store absolute value, type determines direction
                descricao=descricao,
                usuario_chat_id=usuario_chat_id
            )

            # For adjustments, we need to handle negative values
            return self._create_transaction(request, adjustment_amount=valor)

        except Exception as e:
            self.logger.error(f"Failed to adjust balance: {e}")
            raise ServiceError(f"Failed to adjust balance: {str(e)}")

    def _create_transaction(self, request: CreateCashTransactionRequest, adjustment_amount: Optional[Decimal] = None) -> CashTransaction:
        """Create a cash transaction and update balance."""
        # Validate request
        errors = request.validate()
        if errors:
            raise ValidationError(f"Transaction validation failed: {', '.join(errors)}")

        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get current balance
                    cursor.execute("""
                        SELECT saldo_atual FROM CashBalance
                        ORDER BY data_atualizacao DESC
                        LIMIT 1
                    """)
                    balance_row = cursor.fetchone()

                    if not balance_row:
                        saldo_anterior = Decimal('0.00')
                    else:
                        saldo_anterior = balance_row[0]

                    # Calculate new balance based on transaction type
                    if request.tipo == 'receita':
                        saldo_novo = saldo_anterior + request.valor
                    elif request.tipo == 'despesa':
                        saldo_novo = saldo_anterior - request.valor
                    elif request.tipo == 'ajuste':
                        # Use adjustment_amount if provided, otherwise treat as positive
                        amount = adjustment_amount if adjustment_amount is not None else request.valor
                        saldo_novo = saldo_anterior + amount
                    else:
                        raise ValidationError(f"Invalid transaction type: {request.tipo}")

                    # Create transaction record
                    cursor.execute("""
                        INSERT INTO CashTransactions (
                            tipo, valor, descricao, venda_id, pagamento_id,
                            usuario_chat_id, saldo_anterior, saldo_novo
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        RETURNING id, tipo, valor, descricao, venda_id, pagamento_id,
                                  usuario_chat_id, saldo_anterior, saldo_novo, data_transacao
                    """, (
                        request.tipo,
                        request.valor,
                        request.descricao,
                        request.venda_id,
                        request.pagamento_id,
                        request.usuario_chat_id,
                        saldo_anterior,
                        saldo_novo
                    ))

                    transaction_row = cursor.fetchone()

                    # Update cash balance
                    cursor.execute("""
                        UPDATE CashBalance
                        SET saldo_atual = %s, data_atualizacao = CURRENT_TIMESTAMP
                        WHERE id = (SELECT id FROM CashBalance ORDER BY data_atualizacao DESC LIMIT 1)
                    """, (saldo_novo,))

                    # If no balance record exists, create one
                    if cursor.rowcount == 0:
                        cursor.execute("""
                            INSERT INTO CashBalance (saldo_atual)
                            VALUES (%s)
                        """, (saldo_novo,))

                    conn.commit()

                    self.logger.info(f"Created {request.tipo} transaction: {request.valor}, new balance: {saldo_novo}")

                    return CashTransaction.from_db_row(transaction_row)

        except Exception as e:
            self.logger.error(f"Failed to create transaction: {e}")
            raise ServiceError(f"Failed to create transaction: {str(e)}")

    def get_transactions_history(self, limit: int = 50, offset: int = 0) -> List[CashTransaction]:
        """Get transaction history."""
        try:
            # Try different table name formats to handle case sensitivity
            for table_name in ['CashTransactions', 'cashtransactions', '"CashTransactions"']:
                try:
                    query = f"""
                        SELECT id, tipo, valor, descricao, venda_id, pagamento_id,
                               usuario_chat_id, saldo_anterior, saldo_novo, data_transacao
                        FROM {table_name}
                        ORDER BY data_transacao DESC
                        LIMIT %s OFFSET %s
                    """
                    rows = self._execute_query(query, (limit, offset))
                    self.logger.info(f"Successfully queried {table_name} table")
                    return [CashTransaction.from_db_row(row) for row in rows]

                except Exception as table_error:
                    self.logger.warning(f"Table {table_name} query failed: {table_error}")
                    continue

            # If no table format worked, return empty list
            self.logger.warning("No CashTransactions table found, returning empty list")
            return []

        except Exception as e:
            self.logger.error(f"Failed to get transactions history: {e}")
            raise ServiceError(f"Failed to get transactions history: {str(e)}")

    def get_revenue_report(self, days: int = 30) -> RevenueReport:
        """Generate revenue report for the specified number of days."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    # Get sales data
                    cursor.execute("""
                        SELECT
                            COALESCE(COUNT(DISTINCT v.id), 0) as vendas_count,
                            COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) as total_vendas,
                            COALESCE(SUM(iv.quantidade * e.custo), 0) as total_custos
                        FROM vendas v
                        LEFT JOIN itensvenda iv ON v.id = iv.venda_id
                        LEFT JOIN estoque e ON iv.produto_id = e.produto_id
                        WHERE v.data_venda >= %s AND v.data_venda <= %s
                    """, (start_date, end_date))

                    sales_row = cursor.fetchone()
                    vendas_count = sales_row[0] or 0
                    total_vendas = sales_row[1] or Decimal('0.00')
                    total_custos = sales_row[2] or Decimal('0.00')

                    # Get payments data
                    cursor.execute("""
                        SELECT COALESCE(SUM(valor_pago), 0) as total_pagamentos
                        FROM pagamentos
                        WHERE data_pagamento >= %s AND data_pagamento <= %s
                    """, (start_date, end_date))

                    payments_row = cursor.fetchone()
                    total_pagamentos = payments_row[0] or Decimal('0.00')

                    # Get cash transactions data
                    cursor.execute("""
                        SELECT
                            COUNT(*) as transacoes_count,
                            COALESCE(SUM(CASE WHEN tipo = 'despesa' THEN valor ELSE 0 END), 0) as total_despesas
                        FROM CashTransactions
                        WHERE data_transacao >= %s AND data_transacao <= %s
                    """, (start_date, end_date))

                    transactions_row = cursor.fetchone()
                    transacoes_count = transactions_row[0] or 0
                    total_despesas = transactions_row[1] or Decimal('0.00')

                    # Get current balance
                    current_balance = self.get_current_balance()

                    conn.commit()

            # Calculate metrics
            lucro_bruto = total_vendas - total_custos
            lucro_liquido = lucro_bruto - total_despesas

            return RevenueReport(
                periodo_inicio=start_date,
                periodo_fim=end_date,
                total_vendas=total_vendas,
                total_pagamentos=total_pagamentos,
                total_custos=total_custos,
                lucro_bruto=lucro_bruto,
                lucro_liquido=lucro_liquido,
                saldo_atual=current_balance.saldo_atual,
                total_despesas=total_despesas,
                transacoes_count=transacoes_count,
                vendas_count=vendas_count
            )

        except Exception as e:
            self.logger.error(f"Failed to generate revenue report: {e}")
            raise ServiceError(f"Failed to generate revenue report: {str(e)}")

    def get_balance_history(self, days: int = 30) -> CashBalanceHistory:
        """Get balance history for a period."""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)

            # Get transactions in period
            query = """
                SELECT id, tipo, valor, descricao, venda_id, pagamento_id,
                       usuario_chat_id, saldo_anterior, saldo_novo, data_transacao
                FROM CashTransactions
                WHERE data_transacao >= %s AND data_transacao <= %s
                ORDER BY data_transacao ASC
            """
            rows = self._execute_query(query, (start_date, end_date))
            transactions = [CashTransaction.from_db_row(row) for row in rows]

            # Calculate summary
            if transactions:
                balance_start = transactions[0].saldo_anterior
                balance_end = transactions[-1].saldo_novo
            else:
                current_balance = self.get_current_balance()
                balance_start = balance_end = current_balance.saldo_atual

            total_receitas = sum(t.valor for t in transactions if t.tipo == 'receita')
            total_despesas = sum(t.valor for t in transactions if t.tipo == 'despesa')
            total_ajustes = sum(
                t.saldo_novo - t.saldo_anterior - (t.valor if t.tipo == 'receita' else -t.valor)
                for t in transactions if t.tipo == 'ajuste'
            )

            return CashBalanceHistory(
                transactions=transactions,
                balance_start=balance_start,
                balance_end=balance_end,
                total_receitas=total_receitas,
                total_despesas=total_despesas,
                total_ajustes=total_ajustes
            )

        except Exception as e:
            self.logger.error(f"Failed to get balance history: {e}")
            raise ServiceError(f"Failed to get balance history: {str(e)}")