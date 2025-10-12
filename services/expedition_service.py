"""
Expedition service implementation for managing expeditions and their operations.
Extends BaseService for database operations and error handling.
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from decimal import Decimal

from services.base_service import BaseService, ServiceError, ValidationError, NotFoundError
from core.interfaces import IExpeditionService, IProductService, IAssignmentService
from models.expedition import (
    Expedition, ExpeditionItem, ItemConsumption, ExpeditionStatus, PaymentStatus,
    ExpeditionCreateRequest, ExpeditionItemRequest, ItemConsumptionRequest,
    ExpeditionResponse, ItemConsumptionResponse, Assignment, AssignmentStatus,
    ExpeditionItemWithProduct, ItemConsumptionWithProduct
)
from utils.encryption import generate_owner_key
from utils.query_cache import get_query_cache


class ExpeditionService(BaseService, IExpeditionService, IAssignmentService):
    """
    Service for managing expeditions, items, and consumptions.
    Implements full CRUD operations with inventory validation.
    """

    def __init__(self, product_service: IProductService = None):
        super().__init__()
        self._product_service = product_service

    def create_expedition(self, request: ExpeditionCreateRequest) -> Expedition:
        """Create a new expedition with validation."""
        # Validate request
        validation_errors = request.validate()
        if validation_errors:
            raise ValidationError(f"Invalid expedition data: {', '.join(validation_errors)}")

        self._log_operation("CreateExpedition", name=request.name, owner=request.owner_chat_id)

        # First, create expedition to get the ID
        query = """
            INSERT INTO expeditions (name, owner_chat_id, status, deadline, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, name, owner_chat_id, status, deadline, created_at, completed_at
        """

        params = (
            request.name.strip(),
            request.owner_chat_id,
            ExpeditionStatus.ACTIVE.value,
            request.deadline,
            datetime.now()
        )

        result = self._execute_query(query, params, fetch_one=True)
        if not result:
            raise ServiceError("Failed to create expedition")

        expedition = Expedition.from_db_row(result)

        # Generate owner key for this expedition
        try:
            owner_key = generate_owner_key(expedition.id, request.owner_chat_id)

            # Update expedition with owner key and user ID
            update_query = """
                UPDATE expeditions
                SET owner_key = %s, owner_user_id = %s
                WHERE id = %s
                RETURNING id, name, owner_chat_id, status, deadline, created_at, completed_at
            """

            update_params = (owner_key, request.owner_chat_id, expedition.id)
            updated_result = self._execute_query(update_query, update_params, fetch_one=True)

            if updated_result:
                expedition = Expedition.from_db_row(updated_result)
                self.logger.info(f"Created expedition {expedition.id} with secure owner key")
            else:
                self.logger.warning(f"Failed to update expedition {expedition.id} with owner key")

        except Exception as e:
            self.logger.error(f"Failed to generate owner key for expedition {expedition.id}: {e}")
            # Continue without owner key for backward compatibility

        self.logger.info(f"Created expedition {expedition.id}: {expedition.name}")

        # Invalidate relevant caches
        self._invalidate_cache("expeditions")

        return expedition

    def get_expedition_by_id(self, expedition_id: int) -> Optional[Expedition]:
        """Get expedition by ID."""
        query = """
            SELECT id, name, owner_chat_id, status, deadline, created_at, completed_at
            FROM expeditions
            WHERE id = %s
        """

        result = self._execute_query(query, (expedition_id,), fetch_one=True)
        return Expedition.from_db_row(result) if result else None

    def get_expeditions_by_owner(self, owner_chat_id: int) -> List[Expedition]:
        """Get all expeditions for a specific owner."""
        query = """
            SELECT id, name, owner_chat_id, status, deadline, created_at, completed_at
            FROM expeditions
            WHERE owner_chat_id = %s
            ORDER BY created_at DESC
        """

        results = self._execute_query(query, (owner_chat_id,), fetch_all=True)
        return [Expedition.from_db_row(row) for row in results or []]

    def get_all_expeditions(self) -> List[Expedition]:
        """Get all expeditions (cached for 2 minutes)."""
        query = """
            SELECT id, name, owner_chat_id, status, deadline, created_at, completed_at
            FROM expeditions
            ORDER BY created_at DESC
        """

        results = self._execute_cached_query(query, cache_ttl=120, fetch_all=True)
        return [Expedition.from_db_row(row) for row in results or []]

    def get_active_expeditions(self) -> List[Expedition]:
        """Get all active expeditions (cached for 1 minute)."""
        query = """
            SELECT id, name, owner_chat_id, status, deadline, created_at, completed_at
            FROM expeditions
            WHERE status = %s
            ORDER BY created_at DESC
        """

        results = self._execute_cached_query(query, (ExpeditionStatus.ACTIVE.value,), cache_ttl=60, fetch_all=True)
        return [Expedition.from_db_row(row) for row in results or []]

    def get_overdue_expeditions(self) -> List[Expedition]:
        """Get expeditions that are past their deadline."""
        query = """
            SELECT id, name, owner_chat_id, status, deadline, created_at, completed_at
            FROM expeditions
            WHERE status = %s AND deadline IS NOT NULL AND deadline < %s
            ORDER BY deadline ASC
        """

        results = self._execute_query(
            query,
            (ExpeditionStatus.ACTIVE.value, datetime.now()),
            fetch_all=True
        )
        return [Expedition.from_db_row(row) for row in results or []]

    def update_expedition_status(self, expedition_id: int, status: ExpeditionStatus) -> bool:
        """Update expedition status."""
        expedition = self.get_expedition_by_id(expedition_id)
        if not expedition:
            raise NotFoundError(f"Expedition {expedition_id} not found")

        completed_at = datetime.now() if status == ExpeditionStatus.COMPLETED else None

        query = """
            UPDATE expeditions
            SET status = %s, completed_at = %s
            WHERE id = %s
        """

        rows_affected = self._execute_query(
            query,
            (status.value, completed_at, expedition_id)
        )

        self._log_operation("UpdateExpeditionStatus", expedition_id=expedition_id, status=status.value)

        # Invalidate relevant caches
        if rows_affected > 0:
            self._invalidate_cache("expeditions")

        return rows_affected > 0

    def add_expedition_item(self, item_request: ExpeditionItemRequest) -> ExpeditionItem:
        """Add a single item to an expedition with validation."""
        expedition = self.get_expedition_by_id(item_request.expedition_id)
        if not expedition:
            raise NotFoundError(f"Expedition {item_request.expedition_id} not found")

        if not expedition.is_active():
            raise ValidationError("Cannot add items to inactive expedition")

        # Validate item request
        validation_errors = item_request.validate()
        if validation_errors:
            raise ValidationError(f"Invalid item data: {', '.join(validation_errors)}")

        # Validate product exists if product service is available
        if self._product_service:
            product = self._product_service.get_product_by_id(item_request.produto_id)
            if not product:
                raise NotFoundError(f"Product {item_request.produto_id} not found")

        # Insert the item
        query = """
            INSERT INTO expedition_items (expedition_id, produto_id, quantity_required, created_at)
            VALUES (%s, %s, %s, %s)
            RETURNING id, expedition_id, produto_id, quantity_required, quantity_consumed, created_at
        """

        params = (
            item_request.expedition_id,
            item_request.produto_id,
            item_request.quantity_required,
            datetime.now()
        )

        result = self._execute_query(query, params, fetch_one=True)
        if not result:
            raise ServiceError("Failed to add item to expedition")

        self._log_operation("AddExpeditionItem",
                          expedition_id=item_request.expedition_id,
                          product_id=item_request.produto_id,
                          quantity=item_request.quantity_required)

        # Invalidate expedition cache after adding item
        self._invalidate_expedition_cache(item_request.expedition_id)

        return ExpeditionItem.from_db_row(result)

    def remove_expedition_item(self, expedition_id: int, product_id: int) -> bool:
        """Remove an item from an expedition."""
        expedition = self.get_expedition_by_id(expedition_id)
        if not expedition:
            raise NotFoundError(f"Expedition {expedition_id} not found")

        if not expedition.is_active():
            raise ValidationError("Cannot remove items from inactive expedition")

        # Check if there are any consumptions for this item
        consumption_check_query = """
            SELECT COUNT(*) FROM item_consumptions ic
            JOIN expedition_items ei ON ic.expedition_item_id = ei.id
            WHERE ei.expedition_id = %s AND ei.produto_id = %s
        """

        consumption_result = self._execute_query(
            consumption_check_query,
            (expedition_id, product_id),
            fetch_one=True
        )

        if consumption_result and consumption_result[0] > 0:
            raise ValidationError("Cannot remove item that has already been consumed")

        # Remove the item
        query = """
            DELETE FROM expedition_items
            WHERE expedition_id = %s AND produto_id = %s
        """

        rows_affected = self._execute_query(query, (expedition_id, product_id))

        if rows_affected > 0:
            self._log_operation("RemoveExpeditionItem",
                              expedition_id=expedition_id,
                              product_id=product_id)
            # Invalidate expedition cache after removing item
            self._invalidate_expedition_cache(expedition_id)

        return rows_affected > 0

    def add_items_to_expedition(self, expedition_id: int, items: List[ExpeditionItemRequest]) -> List[ExpeditionItem]:
        """Add items to an expedition with inventory validation."""
        expedition = self.get_expedition_by_id(expedition_id)
        if not expedition:
            raise NotFoundError(f"Expedition {expedition_id} not found")

        if not expedition.is_active():
            raise ValidationError("Cannot add items to inactive expedition")

        # Validate all items
        for item_request in items:
            validation_errors = item_request.validate()
            if validation_errors:
                raise ValidationError(f"Invalid item data: {', '.join(validation_errors)}")

            # Validate product exists if product service is available
            if self._product_service:
                product = self._product_service.get_product_by_id(item_request.produto_id)
                if not product:
                    raise NotFoundError(f"Product {item_request.produto_id} not found")

        # Insert all items in a transaction
        operations = []
        for item_request in items:
            operations.append((
                """
                INSERT INTO expedition_items (expedition_id, produto_id, quantity_required, quantity_consumed, target_unit_price, created_at)
                VALUES (%s, %s, %s, 0, %s, %s)
                """,
                (expedition_id, item_request.produto_id, item_request.quantity_required, item_request.unit_cost, datetime.now())
            ))

        success = self._execute_transaction(operations)
        if not success:
            raise ServiceError("Failed to add items to expedition")

        # Return the created items
        self._log_operation("AddItemsToExpedition", expedition_id=expedition_id, item_count=len(items))

        # Invalidate expedition cache after adding items
        self._invalidate_expedition_cache(expedition_id)

        return self.get_expedition_items(expedition_id)

    def get_expedition_items(self, expedition_id: int) -> List[ExpeditionItem]:
        """Get all items for an expedition."""
        query = """
            SELECT id, expedition_id, produto_id, quantity_required, quantity_consumed, created_at
            FROM expedition_items
            WHERE expedition_id = %s
            ORDER BY created_at ASC
        """

        results = self._execute_query(query, (expedition_id,), fetch_all=True)
        return [ExpeditionItem.from_db_row(row) for row in results or []]

    def consume_item(self, request: ItemConsumptionRequest) -> Assignment:
        """
        Record item consumption for an expedition using the assignment-based system.
        This method:
        1. Gets or creates expedition_pirate record
        2. Creates expedition_assignment
        3. Updates expedition_items quantity tracking
        4. Creates corresponding sale record for debt tracking
        """
        # Validate request
        validation_errors = request.validate()
        if validation_errors:
            raise ValidationError(f"Invalid consumption data: {', '.join(validation_errors)}")

        # Get expedition item to validate
        item_query = """
            SELECT ei.id, ei.expedition_id, ei.produto_id, ei.quantity_required, ei.quantity_consumed,
                   e.status, e.owner_chat_id
            FROM expedition_items ei
            JOIN expeditions e ON ei.expedition_id = e.id
            WHERE ei.id = %s
        """

        item_result = self._execute_query(item_query, (request.expedition_item_id,), fetch_one=True)
        if not item_result:
            raise NotFoundError("Expedition item not found")

        (item_id, expedition_id, produto_id, quantity_required,
         quantity_consumed, expedition_status, owner_chat_id) = item_result

        # Validate expedition is active
        if expedition_status != ExpeditionStatus.ACTIVE.value:
            raise ValidationError("Cannot consume items from inactive expedition")

        # Check if consumption would exceed requirement
        new_consumed = (quantity_consumed or 0) + request.quantity_consumed
        if new_consumed > quantity_required:
            raise ValidationError(
                f"Consumption would exceed requirement. "
                f"Required: {quantity_required}, Already consumed: {quantity_consumed or 0}, "
                f"Trying to consume: {request.quantity_consumed}"
            )

        total_cost = request.calculate_total_cost()
        now = datetime.now()

        # Step 1: Get or create expedition_pirate record
        pirate_query = """
            SELECT id FROM expedition_pirates
            WHERE expedition_id = %s AND original_name = %s
        """
        pirate_result = self._execute_query(pirate_query, (expedition_id, request.consumer_name.strip()), fetch_one=True)

        if pirate_result:
            pirate_id = pirate_result[0]
        else:
            # Create new pirate record
            create_pirate_query = """
                INSERT INTO expedition_pirates
                (expedition_id, pirate_name, original_name, role, status, joined_at)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id
            """
            pirate_result = self._execute_query(
                create_pirate_query,
                (expedition_id, request.pirate_name.strip(), request.consumer_name.strip(),
                 'participant', 'active', now),
                fetch_one=True
            )
            if not pirate_result:
                raise ServiceError("Failed to create pirate record")
            pirate_id = pirate_result[0]
            self.logger.info(f"Created new pirate record {pirate_id} for {request.consumer_name}")

        # Step 2: Create assignment and update item in transaction
        operations = [
            # Create expedition_assignment
            (
                """
                INSERT INTO expedition_assignments
                (expedition_id, pirate_id, expedition_item_id, assigned_quantity,
                 consumed_quantity, unit_price, total_cost, assignment_status,
                 payment_status, assigned_at, completed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (expedition_id, pirate_id, request.expedition_item_id,
                 request.quantity_consumed,  # assigned = consumed for immediate consumption
                 request.quantity_consumed,
                 request.unit_price, total_cost,
                 'completed',  # Completed immediately
                 PaymentStatus.PENDING.value,
                 now, now)
            ),
            # Update expedition_items quantity
            (
                """
                UPDATE expedition_items
                SET quantity_consumed = quantity_consumed + %s
                WHERE id = %s
                """,
                (request.quantity_consumed, request.expedition_item_id)
            )
        ]

        success = self._execute_transaction(operations)
        if not success:
            raise ServiceError("Failed to record item consumption")

        # Invalidate expedition cache after consumption to ensure fresh data
        self._invalidate_expedition_cache(expedition_id)

        # Get the created assignment
        assignment_query = """
            SELECT ea.id, ea.expedition_id, ep.pirate_name, ea.expedition_item_id,
                   ea.consumed_quantity, ea.unit_price, ea.total_cost,
                   'consumption', ea.assignment_status, ea.assigned_at,
                   ea.deadline as due_date, ea.completed_at, NULL as notes,
                   ea.assigned_at as created_at, ea.completed_at as updated_at
            FROM expedition_assignments ea
            JOIN expedition_pirates ep ON ea.pirate_id = ep.id
            WHERE ea.expedition_id = %s AND ea.pirate_id = %s
              AND ea.expedition_item_id = %s AND ea.assigned_at = %s
        """

        assignment_result = self._execute_query(
            assignment_query,
            (expedition_id, pirate_id, request.expedition_item_id, now),
            fetch_one=True
        )

        if not assignment_result:
            raise ServiceError("Failed to retrieve created assignment")

        assignment = Assignment.from_db_row(assignment_result)

        # Create a corresponding sale record in the sales system for debt tracking
        try:
            from core.modern_service_container import get_sales_service
            from models.sale import CreateSaleRequest, CreateSaleItemRequest

            sales_service = get_sales_service()

            # Create sale request for the consumption
            sale_request = CreateSaleRequest(
                comprador=request.consumer_name,
                items=[CreateSaleItemRequest(
                    produto_id=produto_id,
                    quantidade=request.quantity_consumed,
                    valor_unitario=request.unit_price
                )],
                expedition_id=expedition_id
            )

            # Create sale for debt tracking WITHOUT stock consumption
            sale = sales_service.create_expedition_sale(sale_request)

            self._log_operation("ConsumeItemSaleCreated",
                              expedition_id=expedition_id,
                              consumer=request.consumer_name,
                              sale_id=sale.id,
                              total_cost=total_cost,
                              stock_consumed=False)

        except Exception as e:
            self.logger.warning(f"Failed to create sale record for consumption tracking: {e}")
            # Don't fail the consumption, just log the issue

        self._log_operation("ConsumeItem",
                          expedition_id=expedition_id,
                          consumer=request.consumer_name,
                          quantity=request.quantity_consumed,
                          pirate_id=pirate_id,
                          assignment_id=assignment.id)

        return assignment

    def get_expedition_consumptions(self, expedition_id: int) -> List[Assignment]:
        """Get all assignments (consumptions) for an expedition."""
        query = """
            SELECT ea.id, ea.expedition_id, ea.pirate_id, ea.expedition_item_id,
                   ea.assigned_quantity, ea.consumed_quantity, ea.unit_price, ea.total_cost,
                   ea.assignment_status, ea.payment_status, ea.assigned_at, ea.completed_at,
                   ep.original_name, ep.pirate_name
            FROM expedition_assignments ea
            JOIN expedition_pirates ep ON ea.pirate_id = ep.id
            WHERE ea.expedition_id = %s
            ORDER BY ea.assigned_at DESC
        """

        results = self._execute_query(query, (expedition_id,), fetch_all=True)
        return [Assignment.from_db_row(row) for row in results or []]

    def pay_assignment(self, assignment_id: int, amount: Decimal) -> Assignment:
        """
        Process payment for an assignment (full or partial).
        Updates expedition_assignments and creates expedition_payments record.
        """
        if amount <= 0:
            raise ValidationError("Payment amount must be greater than zero")

        # Get current assignment with payment tracking
        query = """
            SELECT ea.id, ea.expedition_id, ea.pirate_id, ea.expedition_item_id,
                   ea.assigned_quantity, ea.consumed_quantity, ea.unit_price, ea.total_cost,
                   ea.assignment_status, ea.payment_status, ea.assigned_at, ea.completed_at,
                   ep.original_name, ep.pirate_name,
                   COALESCE(SUM(ep2.payment_amount), 0) as amount_paid
            FROM expedition_assignments ea
            JOIN expedition_pirates ep ON ea.pirate_id = ep.id
            LEFT JOIN expedition_payments ep2 ON ep2.assignment_id = ea.id AND ep2.payment_status = 'completed'
            WHERE ea.id = %s
            GROUP BY ea.id, ep.id, ep.original_name, ep.pirate_name
        """
        result = self._execute_query(query, (assignment_id,), fetch_one=True)
        if not result:
            raise NotFoundError(f"Assignment {assignment_id} not found")

        # Extract assignment data
        (a_id, expedition_id, pirate_id, expedition_item_id,
         assigned_qty, consumed_qty, unit_price, total_cost,
         assignment_status, payment_status, assigned_at, completed_at,
         original_name, pirate_name, amount_paid) = result

        # Check if already fully paid
        if payment_status == PaymentStatus.PAID.value:
            raise ValidationError("Assignment is already fully paid")

        # Calculate new amount paid and remaining
        current_paid = amount_paid or Decimal('0.00')
        new_paid = current_paid + amount
        remaining = total_cost - new_paid

        # Validate payment doesn't exceed total
        if new_paid > total_cost:
            raise ValidationError(f"Payment exceeds total cost. Total: {total_cost}, Already paid: {current_paid}, Trying to pay: {amount}")

        # Determine new payment status
        if remaining <= Decimal('0.01'):  # Account for rounding
            new_status = PaymentStatus.PAID.value
        elif new_paid > Decimal('0.00'):
            new_status = PaymentStatus.PARTIAL.value
        else:
            new_status = PaymentStatus.PENDING.value

        # Build transaction operations
        operations = [
            # Update assignment payment status
            (
                """
                UPDATE expedition_assignments
                SET payment_status = %s
                WHERE id = %s
                """,
                (new_status, assignment_id)
            ),
            # Create payment record
            (
                """
                INSERT INTO expedition_payments
                (expedition_id, assignment_id, pirate_id, payment_amount,
                 payment_status, processed_at, notes)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (expedition_id, assignment_id, pirate_id, amount,
                 'completed', datetime.now(),
                 f'Payment for assignment {assignment_id}')
            )
        ]

        # Execute all updates in transaction
        success = self._execute_transaction(operations)
        if not success:
            raise ServiceError("Failed to process payment")

        # Get updated assignment
        updated_result = self._execute_query(query, (assignment_id,), fetch_one=True)
        if not updated_result:
            raise ServiceError("Failed to retrieve updated assignment")

        self._log_operation("PayAssignment",
                          assignment_id=assignment_id,
                          amount=amount,
                          new_total_paid=new_paid,
                          status=new_status,
                          pirate=original_name)

        # Invalidate expedition cache after payment
        self._invalidate_expedition_cache(expedition_id)

        return Assignment.from_db_row(updated_result)

    def get_user_consumptions(self, consumer_name: str) -> List[Assignment]:
        """Get all assignments (consumptions) for a specific user."""
        query = """
            SELECT ea.id, ea.expedition_id, ea.pirate_id, ea.expedition_item_id,
                   ea.assigned_quantity, ea.consumed_quantity, ea.unit_price, ea.total_cost,
                   ea.assignment_status, ea.payment_status, ea.assigned_at, ea.completed_at,
                   ep.original_name, ep.pirate_name
            FROM expedition_assignments ea
            JOIN expedition_pirates ep ON ea.pirate_id = ep.id
            WHERE ep.original_name = %s
            ORDER BY ea.assigned_at DESC
        """

        results = self._execute_query(query, (consumer_name,), fetch_all=True)
        return [Assignment.from_db_row(row) for row in results or []]

    def get_expedition_details_optimized(self, expedition_id: int) -> Optional[dict]:
        """
        Get complete expedition data in a SINGLE optimized query with JOINs.
        This method reduces database round-trips from 10+ to 1.

        Returns a raw dictionary with all expedition data including:
        - Expedition details
        - Items with product information
        - Consumptions with product information
        """
        cache = get_query_cache()
        cache_key_query = f"expedition_details_{expedition_id}"

        # Check cache first (60 second TTL)
        cached_result = cache.get(cache_key_query, (expedition_id,))
        if cached_result is not None:
            self.logger.debug(f"Cache hit for expedition {expedition_id}")
            return cached_result

        # Single optimized query with JOINs
        query = """
        WITH expedition_data AS (
            SELECT
                e.id, e.name, e.owner_chat_id, e.status, e.deadline,
                e.created_at, e.completed_at
            FROM expeditions e
            WHERE e.id = %s
        ),
        items_data AS (
            SELECT
                ei.id,
                ei.produto_id,
                p.nome as product_name,
                p.emoji as product_emoji,
                ei.quantity_required as quantity_needed,
                COALESCE(
                    (SELECT AVG(e2.preco) FROM Estoque e2
                     WHERE e2.produto_id = ei.produto_id AND e2.quantidade_restante > 0),
                    0
                ) as unit_price,
                COALESCE(ei.quantity_consumed, 0) as quantity_consumed,
                ei.created_at as added_at
            FROM expedition_items ei
            JOIN produtos p ON ei.produto_id = p.id
            WHERE ei.expedition_id = %s
            ORDER BY ei.created_at ASC
        ),
        consumptions_data AS (
            SELECT
                ea.id,
                ep.original_name as consumer_name,
                p.nome as product_name,
                ea.consumed_quantity as quantity,
                ea.unit_price,
                ea.total_cost as total_price,
                COALESCE(
                    (SELECT SUM(payment_amount) FROM expedition_payments
                     WHERE assignment_id = ea.id AND payment_status = 'completed'),
                    0
                ) as amount_paid,
                ea.payment_status,
                ea.assigned_at as consumed_at
            FROM expedition_assignments ea
            JOIN expedition_pirates ep ON ea.pirate_id = ep.id
            JOIN expedition_items ei ON ea.expedition_item_id = ei.id
            JOIN produtos p ON ei.produto_id = p.id
            WHERE ea.expedition_id = %s
            ORDER BY ea.assigned_at DESC
        )
        SELECT
            (SELECT row_to_json(expedition_data.*) FROM expedition_data) as expedition,
            (SELECT json_agg(items_data.*) FROM items_data) as items,
            (SELECT json_agg(consumptions_data.*) FROM consumptions_data) as consumptions
        """

        try:
            result = self._execute_query(
                query,
                (expedition_id, expedition_id, expedition_id),
                fetch_one=True
            )

            if not result or not result[0]:
                self.logger.warning(f"No expedition found with ID {expedition_id}")
                return None

            # Parse the JSON aggregates
            expedition_json = result[0] if result[0] else None
            items_json = result[1] if result[1] else []
            consumptions_json = result[2] if result[2] else []

            if not expedition_json:
                return None

            response_data = {
                'expedition': expedition_json,
                'items': items_json if items_json else [],
                'consumptions': consumptions_json if consumptions_json else []
            }

            # Cache the result for 60 seconds
            cache.set(cache_key_query, (expedition_id,), response_data, ttl=60)

            self.logger.debug(f"Fetched expedition {expedition_id} with optimized query")
            return response_data

        except Exception as e:
            self.logger.error(f"Failed to fetch expedition details: {e}", exc_info=True)
            return None

    def get_expedition_response(self, expedition_id: int) -> Optional[ExpeditionResponse]:
        """
        Get complete expedition data with progress statistics.
        Now uses optimized single-query approach with caching.
        """
        # Try optimized query first
        raw_data = self.get_expedition_details_optimized(expedition_id)
        if not raw_data:
            # Fallback to original multi-query approach
            expedition = self.get_expedition_by_id(expedition_id)
            if not expedition:
                return None

            items = self.get_expedition_items(expedition_id)

            # Convert to ExpeditionItemWithProduct
            items_with_product = []
            for item in items:
                # Fetch product details and average price from stock
                if self._product_service:
                    product = self._product_service.get_product_by_id(item.produto_id)
                    if product:
                        # Get average price from stock
                        price_query = """
                            SELECT COALESCE(AVG(preco), 0)
                            FROM Estoque
                            WHERE produto_id = %s AND quantidade_restante > 0
                        """
                        price_result = self._execute_query(price_query, (item.produto_id,), fetch_one=True)
                        unit_price = Decimal(str(price_result[0])) if price_result and price_result[0] else Decimal('0')

                        items_with_product.append(
                            ExpeditionItemWithProduct(
                                id=item.id,
                                produto_id=item.produto_id,
                                product_name=product.nome,
                                product_emoji=product.emoji or '',
                                quantity_needed=item.quantity_required,
                                unit_price=unit_price,
                                quantity_consumed=item.quantity_consumed,
                                added_at=item.created_at
                            )
                        )

            # Fetch consumptions
            consumptions = self.get_expedition_consumptions(expedition_id)
            consumptions_with_product = []
            for consumption in consumptions:
                # Get product name from expedition item
                item_query = """
                    SELECT p.nome
                    FROM expedition_items ei
                    JOIN produtos p ON ei.produto_id = p.id
                    WHERE ei.id = %s
                """
                item_result = self._execute_query(item_query, (consumption.expedition_item_id,), fetch_one=True)
                product_name = item_result[0] if item_result else "Unknown"

                consumptions_with_product.append(
                    ItemConsumptionWithProduct(
                        id=consumption.id,
                        consumer_name=consumption.consumer_name,
                        product_name=product_name,
                        quantity=consumption.quantity_consumed,
                        unit_price=consumption.unit_price,
                        total_price=consumption.total_cost,
                        amount_paid=consumption.amount_paid,
                        payment_status=consumption.payment_status,
                        consumed_at=consumption.consumed_at
                    )
                )

            return ExpeditionResponse.create(expedition, items_with_product, consumptions_with_product)

        # Parse optimized query results
        expedition_data = raw_data['expedition']
        expedition = Expedition(
            id=expedition_data['id'],
            name=expedition_data['name'],
            owner_chat_id=expedition_data['owner_chat_id'],
            status=ExpeditionStatus.from_string(expedition_data['status']),
            deadline=datetime.fromisoformat(expedition_data['deadline']) if expedition_data.get('deadline') else None,
            created_at=datetime.fromisoformat(expedition_data['created_at']) if expedition_data.get('created_at') else None,
            completed_at=datetime.fromisoformat(expedition_data['completed_at']) if expedition_data.get('completed_at') else None
        )

        # Parse items
        items = []
        for item_data in raw_data['items']:
            items.append(ExpeditionItemWithProduct(
                id=item_data['id'],
                produto_id=item_data['produto_id'],
                product_name=item_data['product_name'],
                product_emoji=item_data['product_emoji'] or '',
                quantity_needed=item_data['quantity_needed'],
                unit_price=Decimal(str(item_data['unit_price'])) if item_data.get('unit_price') else Decimal('0'),
                quantity_consumed=item_data['quantity_consumed'] or 0,
                added_at=datetime.fromisoformat(item_data['added_at']) if item_data.get('added_at') else None
            ))

        # Parse consumptions
        consumptions = []
        for consumption_data in raw_data['consumptions']:
            consumptions.append(ItemConsumptionWithProduct(
                id=consumption_data['id'],
                consumer_name=consumption_data['consumer_name'],
                product_name=consumption_data['product_name'],
                quantity=consumption_data['quantity'],
                unit_price=Decimal(str(consumption_data['unit_price'])),
                total_price=Decimal(str(consumption_data['total_price'])),
                amount_paid=Decimal(str(consumption_data.get('amount_paid', 0))),
                payment_status=PaymentStatus.from_string(consumption_data['payment_status']),
                consumed_at=datetime.fromisoformat(consumption_data['consumed_at']) if consumption_data.get('consumed_at') else None
            ))

        return ExpeditionResponse.create(expedition, items, consumptions)

    def get_all_expedition_responses_bulk(self) -> Dict[int, Dict]:
        """
        Get lightweight progress data for ALL expeditions in a single optimized query.
        Returns dict keyed by expedition_id with progress statistics.
        Optimized for dashboard/timeline endpoints with precomputed prices.
        """
        query = """
        WITH product_avg_prices AS (
            SELECT
                produto_id,
                AVG(preco) as avg_price
            FROM Estoque
            WHERE quantidade_restante > 0
            GROUP BY produto_id
        ),
        expedition_progress AS (
            SELECT
                e.id as expedition_id,
                e.name,
                e.owner_chat_id,
                e.status,
                e.deadline,
                e.created_at,
                e.completed_at,
                COUNT(DISTINCT ei.id) as total_items,
                COALESCE(SUM(ei.quantity_required), 0) as total_quantity_needed,
                COALESCE(SUM(ei.quantity_consumed), 0) as total_quantity_consumed,
                COALESCE(SUM(ei.quantity_required * COALESCE(pap.avg_price, 0)), 0) as total_value,
                COALESCE(SUM(ei.quantity_consumed * COALESCE(pap.avg_price, 0)), 0) as consumed_value
            FROM expeditions e
            LEFT JOIN expedition_items ei ON e.id = ei.expedition_id
            LEFT JOIN product_avg_prices pap ON ei.produto_id = pap.produto_id
            GROUP BY e.id, e.name, e.owner_chat_id, e.status, e.deadline, e.created_at, e.completed_at
        )
        SELECT
            expedition_id,
            name,
            owner_chat_id,
            status,
            deadline,
            created_at,
            completed_at,
            total_items,
            total_quantity_needed,
            total_quantity_consumed,
            CASE
                WHEN total_quantity_needed > 0
                THEN ROUND((total_quantity_consumed::numeric / total_quantity_needed::numeric * 100), 2)
                ELSE 0
            END as completion_percentage,
            total_value,
            consumed_value,
            (total_value - consumed_value) as remaining_value
        FROM expedition_progress
        ORDER BY created_at DESC
        """

        try:
            results = self._execute_query(query, fetch_all=True)

            if not results:
                return {}

            # Build dict keyed by expedition_id
            expedition_data = {}
            for row in results:
                expedition_data[row[0]] = {
                    "id": row[0],
                    "name": row[1],
                    "owner_chat_id": row[2],
                    "status": row[3],
                    "deadline": row[4].isoformat() if row[4] else None,
                    "created_at": row[5].isoformat() if row[5] else None,
                    "completed_at": row[6].isoformat() if row[6] else None,
                    "total_items": int(row[7]),
                    "total_quantity_needed": int(row[8]),
                    "total_quantity_consumed": int(row[9]),
                    "completion_percentage": float(row[10]),
                    "total_value": float(row[11]),
                    "consumed_value": float(row[12]),
                    "remaining_value": float(row[13])
                }

            self.logger.debug(f"Fetched bulk expedition data for {len(expedition_data)} expeditions")
            return expedition_data

        except Exception as e:
            self.logger.error(f"Failed to fetch bulk expedition data: {e}", exc_info=True)
            return {}

    def check_expedition_completion(self, expedition_id: int) -> bool:
        """Check if expedition is complete and update status if necessary."""
        expedition = self.get_expedition_by_id(expedition_id)
        if not expedition or not expedition.is_active():
            return False

        items = self.get_expedition_items(expedition_id)
        if not items:
            return False

        # Check if all items are complete
        all_complete = all(item.is_complete() for item in items)

        if all_complete:
            self.update_expedition_status(expedition_id, ExpeditionStatus.COMPLETED)
            self._log_operation("ExpeditionCompleted", expedition_id=expedition_id)
            return True

        return False

    def delete_expedition(self, expedition_id: int) -> bool:
        """Delete an expedition and all related data."""
        expedition = self.get_expedition_by_id(expedition_id)
        if not expedition:
            raise NotFoundError(f"Expedition {expedition_id} not found")

        # Delete in proper order to respect foreign key constraints
        operations = [
            ("DELETE FROM item_consumptions WHERE expedition_id = %s", (expedition_id,)),
            ("DELETE FROM pirate_names WHERE expedition_id = %s", (expedition_id,)),
            ("DELETE FROM expedition_items WHERE expedition_id = %s", (expedition_id,)),
            ("DELETE FROM expeditions WHERE id = %s", (expedition_id,))
        ]

        success = self._execute_transaction(operations)
        if success:
            self._log_operation("DeleteExpedition", expedition_id=expedition_id)

        return success

    def update_payment_status(self, consumption_id: int, status: PaymentStatus) -> bool:
        """Update payment status for an item consumption."""
        # Get consumption details first
        consumption_query = """
            SELECT id, expedition_id, consumer_name, total_cost
            FROM item_consumptions
            WHERE id = %s
        """

        consumption_result = self._execute_query(consumption_query, (consumption_id,), fetch_one=True)
        if not consumption_result:
            return False

        _, expedition_id, consumer_name, total_cost = consumption_result

        # Update the payment status
        query = """
            UPDATE item_consumptions
            SET payment_status = %s
            WHERE id = %s
        """

        rows_affected = self._execute_query(query, (status.value, consumption_id))

        if rows_affected > 0:
            # If marked as paid, try to create payment record in sales system
            if status == PaymentStatus.PAID:
                try:
                    # Find related sales for this consumer and expedition
                    from core.modern_service_container import get_sales_service
                    sales_service = get_sales_service()

                    expedition_sales = sales_service.get_sales_by_expedition(expedition_id)
                    consumer_sales = [s for s in expedition_sales if s.comprador == consumer_name]

                    if consumer_sales:
                        # Find unpaid sales for this consumer
                        for sale in consumer_sales:
                            sale_with_payments = sales_service.get_sale_with_payments(sale.id)
                            if sale_with_payments and not sale_with_payments.is_fully_paid:
                                # Create payment for this sale
                                from models.sale import CreatePaymentRequest
                                payment_request = CreatePaymentRequest(
                                    venda_id=sale.id,
                                    valor_pago=min(total_cost, sale_with_payments.balance_due)
                                )

                                payment = sales_service.create_payment(payment_request)
                                self._log_operation("ExpeditionPaymentCreated",
                                                  consumption_id=consumption_id,
                                                  sale_id=sale.id,
                                                  payment_id=payment.id,
                                                  amount=payment.valor_pago)
                                break

                except Exception as e:
                    self.logger.warning(f"Failed to create payment record for consumption {consumption_id}: {e}")

            self._log_operation("UpdatePaymentStatus", consumption_id=consumption_id, status=status.value)

        return rows_affected > 0

    def get_unpaid_consumptions(self, consumer_name: Optional[str] = None) -> List[ItemConsumptionResponse]:
        """Get unpaid item consumptions, optionally filtered by consumer."""
        base_query = """
            SELECT ic.id, ic.expedition_id, ic.expedition_item_id, ic.consumer_name, ic.pirate_name,
                   ic.quantity_consumed, ic.unit_price, ic.total_cost, ic.amount_paid, ic.payment_status, ic.consumed_at,
                   e.name as expedition_name, p.name as product_name
            FROM item_consumptions ic
            JOIN expeditions e ON ic.expedition_id = e.id
            JOIN expedition_items ei ON ic.expedition_item_id = ei.id
            JOIN produtos p ON ei.produto_id = p.id
            WHERE ic.payment_status != %s
        """

        params = [PaymentStatus.PAID.value]

        if consumer_name:
            base_query += " AND ic.consumer_name = %s"
            params.append(consumer_name)

        base_query += " ORDER BY ic.consumed_at DESC"

        results = self._execute_query(base_query, tuple(params), fetch_all=True)

        responses = []
        for row in results or []:
            # Parse consumption data
            consumption_data = row[:11]  # First 11 columns are consumption fields (including amount_paid)
            expedition_name = row[11]
            product_name = row[12]

            consumption = ItemConsumption.from_db_row(consumption_data)

            # Calculate remaining debt
            remaining_debt = consumption.total_cost - consumption.amount_paid

            response = ItemConsumptionResponse(
                consumption=consumption,
                expedition_name=expedition_name,
                product_name=product_name,
                remaining_debt=remaining_debt
            )
            responses.append(response)

        return responses

    def get_expedition_progress(self, expedition_id: int) -> dict:
        """
        Get comprehensive progress tracking for an expedition.

        Args:
            expedition_id: Expedition ID

        Returns:
            Dictionary with progress statistics
        """
        expedition = self.get_expedition_by_id(expedition_id)
        if not expedition:
            return {"error": "Expedition not found"}

        items = self.get_expedition_items(expedition_id)
        consumptions = self.get_expedition_consumptions(expedition_id)

        # Calculate progress statistics
        total_items = len(items)
        total_required_quantity = sum(item.quantity_required for item in items)
        total_consumed_quantity = sum(item.quantity_consumed or 0 for item in items)
        completed_items = sum(1 for item in items if item.is_complete())

        # Calculate financial statistics
        total_consumption_value = sum(c.total_cost for c in consumptions)
        paid_consumptions = [c for c in consumptions if c.payment_status == PaymentStatus.PAID.value]
        total_paid_value = sum(c.total_cost for c in paid_consumptions)
        total_unpaid_value = total_consumption_value - total_paid_value

        # Calculate completion percentages
        item_completion_percentage = (completed_items / total_items * 100) if total_items > 0 else 0
        quantity_completion_percentage = (total_consumed_quantity / total_required_quantity * 100) if total_required_quantity > 0 else 0
        payment_completion_percentage = (total_paid_value / total_consumption_value * 100) if total_consumption_value > 0 else 0

        # Unique consumers
        unique_consumers = set(c.consumer_name for c in consumptions)

        # Deadline information
        is_overdue = False
        days_until_deadline = None
        if expedition.deadline:
            from datetime import datetime
            now = datetime.now()
            if expedition.deadline < now:
                is_overdue = True
                days_until_deadline = (now - expedition.deadline).days
            else:
                days_until_deadline = (expedition.deadline - now).days

        return {
            "expedition_id": expedition_id,
            "expedition_name": expedition.name,
            "status": expedition.status,
            "is_active": expedition.is_active(),
            "is_overdue": is_overdue,
            "days_until_deadline": days_until_deadline,
            "progress": {
                "total_items": total_items,
                "completed_items": completed_items,
                "item_completion_percentage": round(item_completion_percentage, 2),
                "total_required_quantity": total_required_quantity,
                "total_consumed_quantity": total_consumed_quantity,
                "quantity_completion_percentage": round(quantity_completion_percentage, 2)
            },
            "financial": {
                "total_consumption_value": float(total_consumption_value),
                "total_paid_value": float(total_paid_value),
                "total_unpaid_value": float(total_unpaid_value),
                "payment_completion_percentage": round(payment_completion_percentage, 2),
                "total_consumptions": len(consumptions),
                "paid_consumptions": len(paid_consumptions)
            },
            "participants": {
                "unique_consumers": len(unique_consumers),
                "consumer_names": list(unique_consumers)
            }
        }

    def get_expedition_timeline(self, expedition_id: int) -> List[dict]:
        """
        Get chronological timeline of expedition events.

        Args:
            expedition_id: Expedition ID

        Returns:
            List of timeline events
        """
        timeline = []

        # Get expedition details
        expedition = self.get_expedition_by_id(expedition_id)
        if not expedition:
            return timeline

        # Add expedition creation event
        timeline.append({
            "timestamp": expedition.created_at,
            "type": "expedition_created",
            "description": f"Expedition '{expedition.name}' created",
            "details": {
                "expedition_name": expedition.name,
                "owner_chat_id": expedition.owner_chat_id
            }
        })

        # Add items added events
        items = self.get_expedition_items(expedition_id)
        for item in items:
            timeline.append({
                "timestamp": item.created_at,
                "type": "item_added",
                "description": f"Item requirement added: Product {item.produto_id}",
                "details": {
                    "produto_id": item.produto_id,
                    "quantity_required": item.quantity_required
                }
            })

        # Add consumption events
        consumptions = self.get_expedition_consumptions(expedition_id)
        for consumption in consumptions:
            timeline.append({
                "timestamp": consumption.consumed_at,
                "type": "item_consumed",
                "description": f"{consumption.consumer_name} consumed {consumption.quantity_consumed} units",
                "details": {
                    "consumer_name": consumption.consumer_name,
                    "pirate_name": consumption.pirate_name,
                    "quantity_consumed": consumption.quantity_consumed,
                    "unit_price": float(consumption.unit_price),
                    "total_cost": float(consumption.total_cost),
                    "payment_status": consumption.payment_status
                }
            })

        # Add completion event if completed
        if expedition.completed_at:
            timeline.append({
                "timestamp": expedition.completed_at,
                "type": "expedition_completed",
                "description": f"Expedition '{expedition.name}' completed",
                "details": {
                    "completed_at": str(expedition.completed_at)
                }
            })

        # Sort timeline by timestamp
        timeline.sort(key=lambda x: x["timestamp"])

        return timeline

    def get_consumer_expedition_summary(self, consumer_name: str) -> dict:
        """
        Get summary of all expedition activity for a specific consumer.

        Args:
            consumer_name: Name of the consumer

        Returns:
            Dictionary with consumer expedition summary
        """
        consumptions = self.get_user_consumptions(consumer_name)

        # Group consumptions by expedition
        expedition_consumptions = {}
        for consumption in consumptions:
            exp_id = consumption.expedition_id
            if exp_id not in expedition_consumptions:
                expedition_consumptions[exp_id] = []
            expedition_consumptions[exp_id].append(consumption)

        # Build summary
        expedition_summaries = []
        total_spent = 0
        total_paid = 0
        total_unpaid = 0

        for exp_id, exp_consumptions in expedition_consumptions.items():
            expedition = self.get_expedition_by_id(exp_id)
            if not expedition:
                continue

            exp_total = sum(c.total_cost for c in exp_consumptions)
            exp_paid = sum(c.total_cost for c in exp_consumptions if c.payment_status == PaymentStatus.PAID.value)
            exp_unpaid = exp_total - exp_paid

            expedition_summaries.append({
                "expedition_id": exp_id,
                "expedition_name": expedition.name,
                "expedition_status": expedition.status,
                "consumptions_count": len(exp_consumptions),
                "total_consumed_quantity": sum(c.quantity_consumed for c in exp_consumptions),
                "total_spent": float(exp_total),
                "total_paid": float(exp_paid),
                "total_unpaid": float(exp_unpaid)
            })

            total_spent += exp_total
            total_paid += exp_paid
            total_unpaid += exp_unpaid

        return {
            "consumer_name": consumer_name,
            "expeditions_participated": len(expedition_summaries),
            "total_consumptions": len(consumptions),
            "total_spent": float(total_spent),
            "total_paid": float(total_paid),
            "total_unpaid": float(total_unpaid),
            "expedition_details": expedition_summaries
        }

    def get_deadline_alerts(self, days_ahead: int = 7) -> List[dict]:
        """
        Get expeditions that are approaching deadline or overdue.

        Args:
            days_ahead: Number of days ahead to check for approaching deadlines

        Returns:
            List of expedition deadline alerts
        """
        from datetime import datetime, timedelta

        now = datetime.now()
        future_date = now + timedelta(days=days_ahead)

        # Get expeditions with deadlines
        query = """
            SELECT id, name, owner_chat_id, status, deadline, created_at, completed_at
            FROM expeditions
            WHERE deadline IS NOT NULL AND status = %s
            ORDER BY deadline ASC
        """

        results = self._execute_query(query, (ExpeditionStatus.ACTIVE.value,), fetch_all=True)
        expeditions = [Expedition.from_db_row(row) for row in results or []]

        alerts = []
        for expedition in expeditions:
            if not expedition.deadline:
                continue

            days_until_deadline = (expedition.deadline - now).days
            is_overdue = expedition.deadline < now

            # Include if overdue or approaching deadline
            if is_overdue or days_until_deadline <= days_ahead:
                progress = self.get_expedition_progress(expedition.id)

                alert = {
                    "expedition_id": expedition.id,
                    "expedition_name": expedition.name,
                    "owner_chat_id": expedition.owner_chat_id,
                    "deadline": str(expedition.deadline),
                    "days_until_deadline": days_until_deadline,
                    "is_overdue": is_overdue,
                    "alert_level": self._get_deadline_alert_level(days_until_deadline, is_overdue),
                    "progress_summary": {
                        "item_completion_percentage": progress.get("progress", {}).get("item_completion_percentage", 0),
                        "quantity_completion_percentage": progress.get("progress", {}).get("quantity_completion_percentage", 0),
                        "payment_completion_percentage": progress.get("financial", {}).get("payment_completion_percentage", 0)
                    }
                }

                alerts.append(alert)

        return alerts

    def _get_deadline_alert_level(self, days_until_deadline: int, is_overdue: bool) -> str:
        """Get alert level based on deadline proximity."""
        if is_overdue:
            return "critical"
        elif days_until_deadline <= 1:
            return "urgent"
        elif days_until_deadline <= 3:
            return "warning"
        else:
            return "info"

    def get_expedition_dashboard_summary(self) -> dict:
        """
        Get comprehensive dashboard summary of all expeditions.

        Returns:
            Dictionary with dashboard statistics
        """
        # Get all expeditions
        all_expeditions = self.get_all_expeditions()
        active_expeditions = [e for e in all_expeditions if e.is_active()]
        completed_expeditions = [e for e in all_expeditions if e.status == ExpeditionStatus.COMPLETED.value]

        # Get overdue expeditions
        overdue_expeditions = self.get_overdue_expeditions()
        deadline_alerts = self.get_deadline_alerts(7)

        # Calculate aggregate statistics
        total_consumptions = 0
        total_consumption_value = 0
        total_paid_value = 0
        unique_consumers = set()

        for expedition in all_expeditions:
            consumptions = self.get_expedition_consumptions(expedition.id)
            total_consumptions += len(consumptions)
            total_consumption_value += sum(c.total_cost for c in consumptions)
            total_paid_value += sum(c.total_cost for c in consumptions if c.payment_status == PaymentStatus.PAID.value)
            unique_consumers.update(c.consumer_name for c in consumptions)

        return {
            "expeditions": {
                "total": len(all_expeditions),
                "active": len(active_expeditions),
                "completed": len(completed_expeditions),
                "overdue": len(overdue_expeditions)
            },
            "financial": {
                "total_consumption_value": float(total_consumption_value),
                "total_paid_value": float(total_paid_value),
                "total_unpaid_value": float(total_consumption_value - total_paid_value),
                "payment_completion_percentage": round((total_paid_value / total_consumption_value * 100) if total_consumption_value > 0 else 0, 2)
            },
            "activity": {
                "total_consumptions": total_consumptions,
                "unique_consumers": len(unique_consumers),
                "average_consumptions_per_expedition": round(total_consumptions / len(all_expeditions), 2) if all_expeditions else 0
            },
            "alerts": {
                "deadline_alerts_count": len(deadline_alerts),
                "critical_alerts": len([a for a in deadline_alerts if a["alert_level"] == "critical"]),
                "urgent_alerts": len([a for a in deadline_alerts if a["alert_level"] == "urgent"]),
                "warning_alerts": len([a for a in deadline_alerts if a["alert_level"] == "warning"])
            }
        }

    def auto_complete_eligible_expeditions(self) -> List[int]:
        """
        Automatically check and complete expeditions that have all items fulfilled.

        Returns:
            List of expedition IDs that were auto-completed
        """
        active_expeditions = self.get_active_expeditions()
        completed_expedition_ids = []

        for expedition in active_expeditions:
            if self.check_expedition_completion(expedition.id):
                completed_expedition_ids.append(expedition.id)
                self._log_operation("AutoCompletedExpedition", expedition_id=expedition.id)

        return completed_expedition_ids

    def get_expedition_owner_key(self, expedition_id: int, owner_chat_id: int) -> Optional[str]:
        """
        Get the owner key for an expedition.
        Only returns the key if the requesting user is the expedition owner.

        Args:
            expedition_id: Expedition identifier
            owner_chat_id: Owner's chat ID for validation

        Returns:
            Owner key if valid owner, None otherwise
        """
        query = """
            SELECT owner_key
            FROM expeditions
            WHERE id = %s AND owner_chat_id = %s
        """

        result = self._execute_query(query, (expedition_id, owner_chat_id), fetch_one=True)
        if result and result[0]:
            self._log_operation("RetrievedOwnerKey", expedition_id=expedition_id, owner=owner_chat_id)
            return result[0]

        return None

    def verify_expedition_ownership(self, expedition_id: int, chat_id: int) -> bool:
        """
        Verify that a user owns an expedition.

        Args:
            expedition_id: Expedition identifier
            chat_id: User's chat ID

        Returns:
            True if user owns the expedition, False otherwise
        """
        query = "SELECT 1 FROM expeditions WHERE id = %s AND owner_chat_id = %s"
        result = self._execute_query(query, (expedition_id, chat_id), fetch_one=True)
        return bool(result)

    # === ASSIGNMENT MANAGEMENT FUNCTIONALITY ===
    # Consolidated from AssignmentService for unified expedition operations

    def create_assignment(self, expedition_id: int, pirate_name: str, item_id: int,
                         quantity: int, unit_price: Decimal, assignment_type: str = 'consumption',
                         due_date: Optional[datetime] = None, notes: Optional[str] = None) -> Assignment:
        """Create a new assignment for expedition consumption."""
        self._log_operation("CreateAssignment",
                          expedition_id=expedition_id,
                          pirate_name=pirate_name,
                          item_id=item_id,
                          quantity=quantity)

        try:
            # Validate inputs
            self._validate_assignment_inputs(expedition_id, pirate_name, item_id, quantity, unit_price)

            # Check if expedition and item exist
            self._validate_expedition_and_item(expedition_id, item_id)

            # Calculate assignment amount
            assignment_amount = Decimal(str(quantity)) * unit_price

            # Create assignment record
            insert_query = """
                INSERT INTO expedition_assignments
                (expedition_id, pirate_name, item_id, quantity, unit_price, assignment_amount,
                 assignment_type, assignment_status, due_date, notes, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id, expedition_id, pirate_name, item_id, quantity, unit_price,
                         assignment_amount, assignment_type, assignment_status, assigned_date,
                         due_date, consumed_date, notes, created_at, updated_at
            """

            now = datetime.now()
            values = (
                expedition_id,
                pirate_name,
                item_id,
                quantity,
                float(unit_price),
                float(assignment_amount),
                assignment_type,
                AssignmentStatus.ASSIGNED.value,
                due_date,
                notes,
                now,
                now
            )

            result = self._execute_query(insert_query, values, fetch_one=True)

            if not result:
                raise ServiceError("Failed to create assignment")

            assignment = Assignment.from_db_row(result)
            self.logger.info(f"Created assignment {assignment.id} for expedition {expedition_id}")

            return assignment

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to create assignment: {e}", exc_info=True)
            raise ServiceError(f"Assignment creation failed: {str(e)}")

    def record_consumption(self, assignment_id: int, consumed_quantity: int,
                          actual_price: Optional[Decimal] = None, consumption_notes: Optional[str] = None) -> Assignment:
        """Record consumption for an assignment."""
        self._log_operation("RecordConsumption",
                          assignment_id=assignment_id,
                          consumed_quantity=consumed_quantity)

        try:
            # Get current assignment
            assignment = self.get_assignment_by_id(assignment_id)
            if not assignment:
                raise NotFoundError(f"Assignment {assignment_id} not found")

            # Validate consumption
            if consumed_quantity <= 0:
                raise ValidationError("Consumed quantity must be positive")

            if consumed_quantity > assignment.quantity:
                raise ValidationError(f"Consumed quantity ({consumed_quantity}) exceeds assigned quantity ({assignment.quantity})")

            # Calculate actual amount
            price_per_unit = actual_price if actual_price else assignment.unit_price
            actual_amount = Decimal(str(consumed_quantity)) * price_per_unit

            # Update assignment status
            new_status = AssignmentStatus.COMPLETED.value if consumed_quantity == assignment.quantity else AssignmentStatus.PARTIALLY_CONSUMED.value

            # Update assignment record
            update_query = """
                UPDATE expedition_assignments
                SET consumed_quantity = %s, actual_price = %s, actual_amount = %s,
                    assignment_status = %s, consumed_date = %s, consumption_notes = %s, updated_at = %s
                WHERE id = %s
                RETURNING id, expedition_id, pirate_name, item_id, quantity, unit_price,
                         assignment_amount, assignment_type, assignment_status, assigned_date,
                         due_date, consumed_date, notes, created_at, updated_at
            """

            values = (
                consumed_quantity,
                float(price_per_unit) if actual_price else None,
                float(actual_amount),
                new_status,
                datetime.now(),
                consumption_notes,
                datetime.now(),
                assignment_id
            )

            result = self._execute_query(update_query, values, fetch_one=True)

            if not result:
                raise ServiceError("Failed to update assignment consumption")

            updated_assignment = Assignment.from_db_row(result)

            # Create corresponding sale record if consumption is complete
            if new_status == AssignmentStatus.COMPLETED.value:
                self._create_consumption_sale_record(updated_assignment, actual_amount)

            self.logger.info(f"Recorded consumption for assignment {assignment_id}")
            return updated_assignment

        except (ValidationError, NotFoundError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to record consumption: {e}", exc_info=True)
            raise ServiceError(f"Consumption recording failed: {str(e)}")

    def get_assignment_by_id(self, assignment_id: int) -> Optional[Assignment]:
        """Get assignment by ID."""
        query = """
            SELECT id, expedition_id, pirate_name, item_id, quantity, unit_price,
                   assignment_amount, assignment_type, assignment_status, assigned_date,
                   due_date, consumed_date, notes, created_at, updated_at
            FROM expedition_assignments
            WHERE id = %s
        """

        result = self._execute_query(query, (assignment_id,), fetch_one=True)
        return Assignment.from_db_row(result) if result else None

    def get_expedition_assignments(self, expedition_id: int, status_filter: Optional[str] = None) -> List[Assignment]:
        """Get all assignments for an expedition."""
        base_query = """
            SELECT id, expedition_id, pirate_name, item_id, quantity, unit_price,
                   assignment_amount, assignment_type, assignment_status, assigned_date,
                   due_date, consumed_date, notes, created_at, updated_at
            FROM expedition_assignments
            WHERE expedition_id = %s
        """

        params = [expedition_id]

        if status_filter:
            base_query += " AND assignment_status = %s"
            params.append(status_filter)

        base_query += " ORDER BY created_at DESC"

        results = self._execute_query(base_query, params, fetch_all=True)
        return [Assignment.from_db_row(row) for row in results or []]

    def get_pirate_assignments(self, expedition_id: int, pirate_name: str, status_filter: Optional[str] = None) -> List[Assignment]:
        """Get assignments for a specific pirate in an expedition."""
        base_query = """
            SELECT id, expedition_id, pirate_name, item_id, quantity, unit_price,
                   assignment_amount, assignment_type, assignment_status, assigned_date,
                   due_date, consumed_date, notes, created_at, updated_at
            FROM expedition_assignments
            WHERE expedition_id = %s AND pirate_name = %s
        """

        params = [expedition_id, pirate_name]

        if status_filter:
            base_query += " AND assignment_status = %s"
            params.append(status_filter)

        base_query += " ORDER BY created_at DESC"

        results = self._execute_query(base_query, params, fetch_all=True)
        return [Assignment.from_db_row(row) for row in results or []]

    def calculate_pirate_debt(self, expedition_id: int, pirate_name: str) -> Dict[str, Decimal]:
        """Calculate total debt for a pirate in an expedition."""
        query = """
            SELECT
                SUM(CASE WHEN assignment_status = 'completed' THEN actual_amount ELSE 0 END) as consumed_amount,
                SUM(CASE WHEN assignment_status IN ('assigned', 'partially_consumed') THEN assignment_amount ELSE 0 END) as pending_amount,
                COUNT(*) as total_assignments,
                COUNT(CASE WHEN assignment_status = 'completed' THEN 1 END) as completed_assignments
            FROM expedition_assignments
            WHERE expedition_id = %s AND pirate_name = %s
        """

        result = self._execute_query(query, (expedition_id, pirate_name), fetch_one=True)

        if result:
            consumed_amount = Decimal(str(result[0] or 0))
            pending_amount = Decimal(str(result[1] or 0))
            total_assignments = result[2] or 0
            completed_assignments = result[3] or 0

            return {
                'consumed_amount': consumed_amount,
                'pending_amount': pending_amount,
                'total_debt': consumed_amount + pending_amount,
                'total_assignments': total_assignments,
                'completed_assignments': completed_assignments,
                'completion_rate': (completed_assignments / total_assignments * 100) if total_assignments > 0 else 0
            }
        else:
            return {
                'consumed_amount': Decimal('0'),
                'pending_amount': Decimal('0'),
                'total_debt': Decimal('0'),
                'total_assignments': 0,
                'completed_assignments': 0,
                'completion_rate': 0
            }

    def get_overdue_assignments(self, expedition_id: Optional[int] = None) -> List[Assignment]:
        """Get assignments that are overdue."""
        base_query = """
            SELECT id, expedition_id, pirate_name, item_id, quantity, unit_price,
                   assignment_amount, assignment_type, assignment_status, assigned_date,
                   due_date, consumed_date, notes, created_at, updated_at
            FROM expedition_assignments
            WHERE due_date < %s AND assignment_status IN ('assigned', 'partially_consumed')
        """

        params = [datetime.now()]

        if expedition_id:
            base_query += " AND expedition_id = %s"
            params.append(expedition_id)

        base_query += " ORDER BY due_date ASC"

        results = self._execute_query(base_query, params, fetch_all=True)
        return [Assignment.from_db_row(row) for row in results or []]

    def cancel_assignment(self, assignment_id: int, cancellation_reason: Optional[str] = None) -> bool:
        """Cancel an assignment."""
        self._log_operation("CancelAssignment", assignment_id=assignment_id)

        try:
            update_query = """
                UPDATE expedition_assignments
                SET assignment_status = 'cancelled',
                    consumption_notes = %s,
                    updated_at = %s
                WHERE id = %s AND assignment_status IN ('assigned', 'partially_consumed')
            """

            notes = f"CANCELLED: {cancellation_reason}" if cancellation_reason else "CANCELLED"
            rows_affected = self._execute_query(update_query, (notes, datetime.now(), assignment_id))

            success = rows_affected > 0
            if success:
                self.logger.info(f"Cancelled assignment {assignment_id}")

            return success

        except Exception as e:
            self.logger.error(f"Failed to cancel assignment: {e}", exc_info=True)
            raise ServiceError(f"Assignment cancellation failed: {str(e)}")

    def _validate_assignment_inputs(self, expedition_id: int, pirate_name: str, item_id: int,
                                  quantity: int, unit_price: Decimal) -> None:
        """Validate assignment creation inputs."""
        if expedition_id <= 0:
            raise ValidationError("Invalid expedition ID")

        if not pirate_name or not pirate_name.strip():
            raise ValidationError("Pirate name is required")

        if item_id <= 0:
            raise ValidationError("Invalid item ID")

        if quantity <= 0:
            raise ValidationError("Quantity must be positive")

        if unit_price <= 0:
            raise ValidationError("Unit price must be positive")

    def _validate_expedition_and_item(self, expedition_id: int, item_id: int) -> None:
        """Validate that expedition and item exist and are valid."""
        # Check expedition exists
        expedition_query = "SELECT id FROM expeditions WHERE id = %s"
        expedition_result = self._execute_query(expedition_query, (expedition_id,), fetch_one=True)
        if not expedition_result:
            raise NotFoundError(f"Expedition {expedition_id} not found")

        # Check item exists and belongs to expedition
        item_query = "SELECT id FROM expedition_items WHERE id = %s AND expedition_id = %s"
        item_result = self._execute_query(item_query, (item_id, expedition_id), fetch_one=True)
        if not item_result:
            raise NotFoundError(f"Item {item_id} not found in expedition {expedition_id}")

    def _invalidate_expedition_cache(self, expedition_id: int) -> None:
        """
        Invalidate all cached queries related to a specific expedition.
        This ensures fresh data after consumption or changes.
        """
        cache = get_query_cache()
        # Invalidate the expedition details cache using pattern matching
        pattern = f"expedition_details_{expedition_id}"
        invalidated = cache.invalidate(pattern)
        self.logger.debug(f"Invalidated {invalidated} cache entries for expedition {expedition_id}")

    def _create_consumption_sale_record(self, assignment: Assignment, actual_amount: Decimal) -> None:
        """Create a sale record for completed consumption."""
        try:
            # Get item details
            item_query = """
                SELECT product_name, product_emoji
                FROM expedition_items
                WHERE id = %s
            """
            item_result = self._execute_query(item_query, (assignment.item_id,), fetch_one=True)

            if item_result:
                product_name = item_result[0]
                product_emoji = item_result[1] or ""

                # Create sale record
                sale_query = """
                    INSERT INTO vendas (nome_comprador, produto, quantidade, preco_total, data_venda, emoji_produto)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """

                sale_values = (
                    assignment.pirate_name,
                    product_name,
                    assignment.consumed_quantity or assignment.quantity,
                    float(actual_amount),
                    assignment.consumed_date or datetime.now(),
                    product_emoji
                )

                self._execute_query(sale_query, sale_values)
                self.logger.info(f"Created sale record for assignment {assignment.id}")

        except Exception as e:
            self.logger.error(f"Failed to create sale record for assignment {assignment.id}: {e}")
            # Don't raise exception as this is not critical for assignment completion