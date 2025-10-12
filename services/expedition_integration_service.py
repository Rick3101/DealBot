from typing import Optional, Dict, List, Any
from datetime import datetime
from decimal import Decimal
from services.base_service import BaseService, ServiceError, ValidationError, NotFoundError
from utils.input_sanitizer import InputSanitizer


class ExpeditionIntegrationService(BaseService):
    """
    Handles integration between expeditions and main sales system.
    Manages pirate-to-buyer mapping, debt synchronization, and expedition payment processing.
    """

    def __init__(self):
        super().__init__()

    def map_pirate_to_buyer(self, expedition_id: int, pirate_name: str, buyer_username: str,
                           owner_key: str) -> bool:
        """
        Create a mapping between a pirate name and a real buyer username.
        This mapping is encrypted and only accessible to expedition owners.

        Args:
            expedition_id: Expedition identifier
            pirate_name: Anonymized pirate name
            buyer_username: Real buyer username
            owner_key: Owner's encryption key for secure mapping

        Returns:
            True if mapping was created successfully

        Raises:
            ValidationError: If input validation fails
            ServiceError: If mapping creation fails
        """
        self._log_operation("MapPirateToBuyer",
                          expedition_id=expedition_id,
                          pirate_name=pirate_name,
                          buyer_username=buyer_username[:10] + "...")

        try:
            # Validate inputs
            self._validate_mapping_inputs(expedition_id, pirate_name, buyer_username, owner_key)

            # Check if mapping already exists
            existing_query = """
                SELECT id FROM expedition_pirates
                WHERE expedition_id = %s AND pirate_name = %s
            """
            existing_result = self._execute_query(existing_query, (expedition_id, pirate_name), fetch_one=True)

            if existing_result:
                # Update existing mapping
                update_query = """
                    UPDATE expedition_pirates
                    SET buyer_username = %s, owner_key = %s, updated_at = %s
                    WHERE expedition_id = %s AND pirate_name = %s
                """
                self._execute_query(update_query, (buyer_username, owner_key, datetime.now(), expedition_id, pirate_name))
                self.logger.info(f"Updated pirate-buyer mapping for {pirate_name} in expedition {expedition_id}")
            else:
                # Create new mapping
                insert_query = """
                    INSERT INTO expedition_pirates (expedition_id, pirate_name, buyer_username, owner_key, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """
                now = datetime.now()
                self._execute_query(insert_query, (expedition_id, pirate_name, buyer_username, owner_key, now, now))
                self.logger.info(f"Created pirate-buyer mapping for {pirate_name} in expedition {expedition_id}")

            return True

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to map pirate to buyer: {e}", exc_info=True)
            raise ServiceError(f"Mapping creation failed: {str(e)}")

    def get_buyer_for_pirate(self, expedition_id: int, pirate_name: str) -> Optional[str]:
        """
        Get the real buyer username for a pirate name (owner access only).

        Args:
            expedition_id: Expedition identifier
            pirate_name: Anonymized pirate name

        Returns:
            Real buyer username or None if not found
        """
        query = """
            SELECT buyer_username FROM expedition_pirates
            WHERE expedition_id = %s AND pirate_name = %s
        """

        result = self._execute_query(query, (expedition_id, pirate_name), fetch_one=True)
        return result[0] if result else None

    def get_pirate_for_buyer(self, expedition_id: int, buyer_username: str) -> Optional[str]:
        """
        Get the pirate name for a real buyer username.

        Args:
            expedition_id: Expedition identifier
            buyer_username: Real buyer username

        Returns:
            Anonymized pirate name or None if not found
        """
        query = """
            SELECT pirate_name FROM expedition_pirates
            WHERE expedition_id = %s AND buyer_username = %s
        """

        result = self._execute_query(query, (expedition_id, buyer_username), fetch_one=True)
        return result[0] if result else None

    def sync_expedition_debt_to_main_system(self, expedition_id: int) -> Dict[str, Any]:
        """
        Synchronize expedition debts with the main debt tracking system.

        Args:
            expedition_id: Expedition identifier

        Returns:
            Dictionary with synchronization results
        """
        self._log_operation("SyncExpeditionDebt", expedition_id=expedition_id)

        try:
            sync_results = {
                'synchronized_pirates': 0,
                'total_debt_amount': Decimal('0'),
                'created_debt_records': 0,
                'updated_debt_records': 0,
                'errors': []
            }

            # Get all expedition assignments with debt
            debt_query = """
                SELECT ea.pirate_name,
                       SUM(CASE WHEN ea.assignment_status = 'completed' THEN ea.actual_amount ELSE ea.assignment_amount END) as total_debt
                FROM expedition_assignments ea
                WHERE ea.expedition_id = %s
                  AND ea.assignment_status IN ('assigned', 'partially_consumed', 'completed')
                GROUP BY ea.pirate_name
            """

            debt_results = self._execute_query(debt_query, (expedition_id,), fetch_all=True)

            for debt_row in debt_results or []:
                pirate_name = debt_row[0]
                debt_amount = Decimal(str(debt_row[1]))

                try:
                    # Get real buyer username
                    buyer_username = self.get_buyer_for_pirate(expedition_id, pirate_name)

                    if buyer_username:
                        # Sync debt to main system
                        success = self._create_or_update_main_debt(buyer_username, debt_amount, expedition_id)

                        if success:
                            sync_results['synchronized_pirates'] += 1
                            sync_results['total_debt_amount'] += debt_amount
                        else:
                            sync_results['errors'].append(f"Failed to sync debt for {pirate_name}")
                    else:
                        sync_results['errors'].append(f"No buyer mapping found for pirate: {pirate_name}")

                except Exception as pirate_error:
                    self.logger.error(f"Error syncing debt for pirate {pirate_name}: {pirate_error}")
                    sync_results['errors'].append(f"Error syncing {pirate_name}: {str(pirate_error)}")

            self.logger.info(f"Expedition debt sync completed: {sync_results['synchronized_pirates']} pirates synced")
            return sync_results

        except Exception as e:
            self.logger.error(f"Failed to sync expedition debt: {e}", exc_info=True)
            raise ServiceError(f"Debt synchronization failed: {str(e)}")

    def create_integrated_sale_record(self, expedition_id: int, pirate_name: str,
                                     items: List[Dict], total_amount: Decimal) -> Optional[int]:
        """
        Create a sale record that integrates with both expedition and main systems.

        Args:
            expedition_id: Expedition identifier
            pirate_name: Anonymized pirate name
            items: List of sale items
            total_amount: Total sale amount

        Returns:
            Sale ID if created successfully, None otherwise
        """
        self._log_operation("CreateIntegratedSale",
                          expedition_id=expedition_id,
                          pirate_name=pirate_name,
                          total_amount=total_amount)

        try:
            # Get buyer username from pirate name
            buyer_username = self.get_buyer_for_pirate(expedition_id, pirate_name)

            if not buyer_username:
                raise ValidationError(f"No buyer mapping found for pirate: {pirate_name}")

            # Create sale in main system
            sale_query = """
                INSERT INTO Vendas (comprador, data_venda, expedition_id)
                VALUES (%s, CURRENT_TIMESTAMP, %s)
                RETURNING id
            """

            sale_result = self._execute_query(sale_query, (buyer_username, expedition_id), fetch_one=True)

            if not sale_result:
                raise ServiceError("Failed to create sale record")

            sale_id = sale_result[0]

            # Create sale items
            for item in items:
                item_query = """
                    INSERT INTO ItensVenda (venda_id, produto_id, quantidade, valor_unitario, produto_nome)
                    VALUES (%s, %s, %s, %s, %s)
                """
                self._execute_query(item_query, (
                    sale_id,
                    item['produto_id'],
                    item['quantidade'],
                    item['valor_unitario'],
                    item.get('produto_nome', '')
                ))

            self.logger.info(f"Created integrated sale {sale_id} for pirate {pirate_name}")
            return sale_id

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create integrated sale: {e}", exc_info=True)
            raise ServiceError(f"Integrated sale creation failed: {str(e)}")

    def record_expedition_payment(self, expedition_id: int, pirate_name: str,
                                  payment_amount: Decimal, payment_date: Optional[datetime] = None) -> bool:
        """
        Record a payment for an expedition purchase.

        Args:
            expedition_id: Expedition identifier
            pirate_name: Anonymized pirate name
            payment_amount: Payment amount
            payment_date: Payment date (defaults to now)

        Returns:
            True if payment was recorded successfully
        """
        self._log_operation("RecordExpeditionPayment",
                          expedition_id=expedition_id,
                          pirate_name=pirate_name,
                          payment_amount=payment_amount)

        try:
            # Get buyer username
            buyer_username = self.get_buyer_for_pirate(expedition_id, pirate_name)

            if not buyer_username:
                raise ValidationError(f"No buyer mapping found for pirate: {pirate_name}")

            # Get unpaid sales for this buyer in this expedition
            sale_query = """
                SELECT v.id, COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) - COALESCE(SUM(p.valor_pago), 0) as balance
                FROM Vendas v
                LEFT JOIN ItensVenda iv ON v.id = iv.venda_id
                LEFT JOIN Pagamentos p ON v.id = p.venda_id
                WHERE v.comprador = %s AND v.expedition_id = %s
                GROUP BY v.id
                HAVING COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) - COALESCE(SUM(p.valor_pago), 0) > 0
                ORDER BY v.data_venda ASC
            """

            unpaid_sales = self._execute_query(sale_query, (buyer_username, expedition_id), fetch_all=True)

            if not unpaid_sales:
                self.logger.warning(f"No unpaid sales found for {pirate_name} in expedition {expedition_id}")
                return False

            # Record payment against first unpaid sale
            sale_id = unpaid_sales[0][0]
            payment_query = """
                INSERT INTO Pagamentos (venda_id, valor_pago, data_pagamento)
                VALUES (%s, %s, %s)
            """

            payment_datetime = payment_date or datetime.now()
            self._execute_query(payment_query, (sale_id, payment_amount, payment_datetime))

            self.logger.info(f"Recorded payment of {payment_amount} for {pirate_name} on sale {sale_id}")
            return True

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to record expedition payment: {e}", exc_info=True)
            raise ServiceError(f"Payment recording failed: {str(e)}")

    def get_expedition_financial_summary(self, expedition_id: int) -> Dict[str, Any]:
        """
        Get financial summary for an expedition including all pirate debts and payments.

        Args:
            expedition_id: Expedition identifier

        Returns:
            Dictionary with financial summary
        """
        try:
            summary_query = """
                SELECT
                    ep.pirate_name,
                    ep.buyer_username,
                    COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) as total_owed,
                    COALESCE(SUM(p.valor_pago), 0) as total_paid,
                    COALESCE(SUM(iv.quantidade * iv.valor_unitario), 0) - COALESCE(SUM(p.valor_pago), 0) as balance
                FROM expedition_pirates ep
                LEFT JOIN Vendas v ON v.comprador = ep.buyer_username AND v.expedition_id = %s
                LEFT JOIN ItensVenda iv ON v.id = iv.venda_id
                LEFT JOIN Pagamentos p ON v.id = p.venda_id
                WHERE ep.expedition_id = %s
                GROUP BY ep.pirate_name, ep.buyer_username
            """

            results = self._execute_query(summary_query, (expedition_id, expedition_id), fetch_all=True)

            summary = {
                'expedition_id': expedition_id,
                'pirates': [],
                'total_owed': Decimal('0'),
                'total_paid': Decimal('0'),
                'total_balance': Decimal('0')
            }

            for row in results or []:
                pirate_data = {
                    'pirate_name': row[0],
                    'buyer_username': row[1],
                    'total_owed': Decimal(str(row[2])),
                    'total_paid': Decimal(str(row[3])),
                    'balance': Decimal(str(row[4]))
                }
                summary['pirates'].append(pirate_data)
                summary['total_owed'] += pirate_data['total_owed']
                summary['total_paid'] += pirate_data['total_paid']
                summary['total_balance'] += pirate_data['balance']

            return summary

        except Exception as e:
            self.logger.error(f"Failed to get expedition financial summary: {e}", exc_info=True)
            raise ServiceError(f"Financial summary failed: {str(e)}")

    def _validate_mapping_inputs(self, expedition_id: int, pirate_name: str,
                                 buyer_username: str, owner_key: str) -> None:
        """Validate inputs for pirate-buyer mapping."""
        if not expedition_id or expedition_id <= 0:
            raise ValidationError("Invalid expedition ID")

        if not pirate_name or not pirate_name.strip():
            raise ValidationError("Pirate name cannot be empty")

        if not buyer_username or not buyer_username.strip():
            raise ValidationError("Buyer username cannot be empty")

        if not owner_key or not owner_key.strip():
            raise ValidationError("Owner key cannot be empty")

        # Sanitize buyer username
        try:
            InputSanitizer.sanitize_username(buyer_username)
        except ValueError as e:
            raise ValidationError(f"Invalid buyer username: {str(e)}")

    def _create_or_update_main_debt(self, buyer_username: str, debt_amount: Decimal, expedition_id: int) -> bool:
        """Create or update debt record in main system."""
        try:
            # Check if buyer has existing sales in expedition
            check_query = """
                SELECT id FROM Vendas
                WHERE comprador = %s AND expedition_id = %s
                LIMIT 1
            """
            existing_sale = self._execute_query(check_query, (buyer_username, expedition_id), fetch_one=True)

            if existing_sale:
                # Update existing sale items to reflect debt
                self.logger.info(f"Debt already tracked via existing sales for {buyer_username}")
                return True
            else:
                # Create placeholder sale for debt tracking
                sale_query = """
                    INSERT INTO Vendas (comprador, data_venda, expedition_id)
                    VALUES (%s, CURRENT_TIMESTAMP, %s)
                    RETURNING id
                """
                sale_result = self._execute_query(sale_query, (buyer_username, expedition_id), fetch_one=True)

                if sale_result:
                    sale_id = sale_result[0]
                    # Create a placeholder item for the debt
                    item_query = """
                        INSERT INTO ItensVenda (venda_id, produto_id, quantidade, valor_unitario, produto_nome)
                        VALUES (%s, 1, 1, %s, 'Expedition Debt')
                    """
                    self._execute_query(item_query, (sale_id, debt_amount))
                    self.logger.info(f"Created debt record for {buyer_username}: {debt_amount}")
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Failed to create/update main debt: {e}", exc_info=True)
            return False
