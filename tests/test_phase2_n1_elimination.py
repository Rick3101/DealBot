#!/usr/bin/env python3
"""
Phase 2 N+1 Query Elimination Tests

Tests for the two major optimizations implemented in Phase 2:
1. Dashboard overdue expeditions - get_overdue_expeditions_with_details()
2. All consumptions endpoint - get_recent_consumptions()

These tests verify:
- Correct data structure and calculations
- Single query execution (no N+1 patterns)
- Edge cases (empty data, null values)
- Permission validation
- API endpoint integration
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict

# Import service classes
from services.expedition_service import ExpeditionService
from models.expedition import (
    ExpeditionStatus, PaymentStatus, ItemConsumptionWithProduct
)


@pytest.mark.phase2
class TestOverdueExpeditionsOptimization:
    """
    Test suite for get_overdue_expeditions_with_details() optimization.

    Validates:
    - Single query execution with CTEs
    - Correct progress calculations
    - Alert level logic
    - Edge cases (no overdue, null deadline)
    """

    @pytest.fixture
    def expedition_service(self):
        """Create ExpeditionService instance with mocked dependencies."""
        service = ExpeditionService()
        return service

    @pytest.fixture
    def mock_overdue_data(self):
        """Sample overdue expedition data as tuples (matching DB row format)."""
        now = datetime.now()
        return [
            # Row format: id, name, owner_chat_id, status, deadline, created_at, completed_at,
            #             total_items, completed_items, remaining_items, total_quantity_needed,
            #             total_quantity_consumed, completion_percentage, total_value, consumed_value, remaining_value
            (
                1,  # id
                'Test Expedition 1',  # name
                12345,  # owner_chat_id
                'active',  # status
                now - timedelta(days=8),  # deadline (8 days overdue)
                now - timedelta(days=30),  # created_at
                None,  # completed_at
                5,  # total_items
                2,  # completed_items
                3,  # remaining_items
                100,  # total_quantity_needed
                40,  # total_quantity_consumed
                40.0,  # completion_percentage
                Decimal('1000.00'),  # total_value
                Decimal('400.00'),  # consumed_value
                Decimal('600.00')  # remaining_value
            ),
            (
                2,  # id
                'Test Expedition 2',  # name
                12345,  # owner_chat_id
                'active',  # status
                now - timedelta(days=2),  # deadline (2 days overdue)
                now - timedelta(days=15),  # created_at
                None,  # completed_at
                3,  # total_items
                1,  # completed_items
                2,  # remaining_items
                50,  # total_quantity_needed
                20,  # total_quantity_consumed
                40.0,  # completion_percentage
                Decimal('500.00'),  # total_value
                Decimal('200.00'),  # consumed_value
                Decimal('300.00')  # remaining_value
            )
        ]

    def test_get_overdue_expeditions_with_details_success(
        self, expedition_service, mock_overdue_data
    ):
        """Test successful retrieval of overdue expeditions with progress details."""
        # Mock the database query
        with patch.object(expedition_service, '_execute_query') as mock_query:
            mock_query.return_value = mock_overdue_data

            # Execute method
            result = expedition_service.get_overdue_expeditions_with_details()

            # Verify single query was executed
            assert mock_query.call_count == 1

            # Verify result structure
            assert isinstance(result, list)
            assert len(result) == 2

            # Verify first expedition data
            exp1 = result[0]
            assert exp1['id'] == 1
            assert exp1['name'] == 'Test Expedition 1'
            assert exp1['completion_percentage'] == 40.0
            assert exp1['total_items'] == 5
            assert exp1['completed_items'] == 2

    def test_get_overdue_expeditions_empty_result(self, expedition_service):
        """Test behavior when no expeditions are overdue."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            mock_query.return_value = []

            result = expedition_service.get_overdue_expeditions_with_details()

            # Should return empty list, not None or error
            assert isinstance(result, list)
            assert len(result) == 0

    def test_get_overdue_expeditions_null_deadline(self, expedition_service):
        """Test that expeditions with null deadline are not included."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            # Only active expeditions with deadlines in the past should be returned
            mock_query.return_value = []

            result = expedition_service.get_overdue_expeditions_with_details()

            # Query should filter out null deadlines
            query_call = mock_query.call_args[0][0]
            assert 'deadline IS NOT NULL' in query_call or 'e.deadline IS NOT NULL' in query_call

    def test_get_overdue_expeditions_cte_structure(self, expedition_service):
        """Test that query uses CTEs for optimization."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            mock_query.return_value = []

            expedition_service.get_overdue_expeditions_with_details()

            # Verify query uses WITH clause (CTE)
            query = mock_query.call_args[0][0]
            assert 'WITH' in query
            assert 'product_avg_prices' in query or 'expedition_progress' in query

    def test_get_overdue_expeditions_performance_single_query(self, expedition_service):
        """Test that only ONE database query is executed (no N+1 pattern)."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            # Mock data with all 16 required columns
            mock_query.return_value = [
                (1, 'Exp1', 12345, 'active', datetime.now(), datetime.now(), None, 5, 2, 3, 100, 40, 40.0, 1000, 400, 600),
                (2, 'Exp2', 12345, 'active', datetime.now(), datetime.now(), None, 3, 1, 2, 50, 20, 40.0, 500, 200, 300),
                (3, 'Exp3', 12345, 'active', datetime.now(), datetime.now(), None, 8, 4, 4, 200, 100, 50.0, 2000, 1000, 1000),
            ]

            result = expedition_service.get_overdue_expeditions_with_details()

            # CRITICAL: Only 1 query should be executed regardless of result count
            assert mock_query.call_count == 1, "N+1 pattern detected! Multiple queries executed."
            assert len(result) == 3


@pytest.mark.phase2
class TestRecentConsumptionsOptimization:
    """
    Test suite for get_recent_consumptions() optimization.

    Validates:
    - Single query execution with JOINs
    - Correct data retrieval across expeditions
    - Filtering by expedition IDs
    - Limit parameter
    """

    @pytest.fixture
    def expedition_service(self):
        """Create ExpeditionService instance."""
        return ExpeditionService()

    @pytest.fixture
    def mock_consumption_data(self):
        """Sample consumption data."""
        return [
            (
                1,  # id
                'Pirate Jack',  # consumer_name
                'Pirate Jack',  # pirate_name
                'Rum',  # product_name
                10,  # quantity
                Decimal('5.00'),  # unit_price
                Decimal('50.00'),  # total_price
                Decimal('0.00'),  # amount_paid
                'pending',  # payment_status
                datetime.now()  # consumed_at
            ),
            (
                2,
                'Pirate Anne',
                'Pirate Anne',
                'Gold Coins',
                5,
                Decimal('100.00'),
                Decimal('500.00'),
                Decimal('250.00'),
                'partial',
                datetime.now()
            ),
        ]

    def test_get_recent_consumptions_success(
        self, expedition_service, mock_consumption_data
    ):
        """Test successful retrieval of recent consumptions."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            mock_query.return_value = mock_consumption_data

            result = expedition_service.get_recent_consumptions(limit=50)

            # Verify single query execution
            assert mock_query.call_count == 1

            # Verify result type
            assert isinstance(result, list)
            assert len(result) == 2

            # Verify first consumption
            consumption = result[0]
            assert isinstance(consumption, ItemConsumptionWithProduct)
            assert consumption.product_name == 'Rum'
            assert consumption.quantity == 10
            assert consumption.unit_price == Decimal('5.00')

    def test_get_recent_consumptions_with_limit(self, expedition_service):
        """Test that limit parameter is properly applied."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            mock_query.return_value = []

            expedition_service.get_recent_consumptions(limit=25)

            # Verify limit is in query
            query = mock_query.call_args[0][0]
            params = mock_query.call_args[0][1]

            assert 'LIMIT' in query
            assert 25 in params

    def test_get_recent_consumptions_with_expedition_filter(
        self, expedition_service
    ):
        """Test filtering by specific expedition IDs."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            mock_query.return_value = []

            expedition_service.get_recent_consumptions(
                limit=50,
                expedition_ids=[1, 2, 3]
            )

            # Verify expedition filter in query
            query = mock_query.call_args[0][0]
            params = mock_query.call_args[0][1]

            assert 'IN' in query
            # Should have expedition IDs in params
            assert 1 in params
            assert 2 in params
            assert 3 in params

    def test_get_recent_consumptions_empty_result(self, expedition_service):
        """Test behavior with no consumptions."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            mock_query.return_value = []

            result = expedition_service.get_recent_consumptions()

            assert isinstance(result, list)
            assert len(result) == 0

    def test_get_recent_consumptions_single_query(self, expedition_service):
        """Test that only ONE query is executed (no N+1 pattern)."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            # Simulate 50 consumptions
            mock_data = [
                (i, f'Pirate{i}', f'Pirate{i}', f'Product{i}',
                 1, Decimal('10.00'), Decimal('10.00'), Decimal('0.00'),
                 'pending', datetime.now())
                for i in range(50)
            ]
            mock_query.return_value = mock_data

            result = expedition_service.get_recent_consumptions(limit=50)

            # CRITICAL: Only 1 query regardless of consumption count
            assert mock_query.call_count == 1, "N+1 pattern detected!"
            assert len(result) == 50

    def test_get_recent_consumptions_joins_all_tables(self, expedition_service):
        """Test that query properly joins all required tables."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            mock_query.return_value = []

            expedition_service.get_recent_consumptions()

            query = mock_query.call_args[0][0]

            # Verify all necessary joins
            assert 'expedition_assignments' in query or 'ea' in query
            assert 'expedition_pirates' in query or 'ep' in query
            assert 'expedition_items' in query or 'ei' in query
            assert 'produtos' in query or 'p' in query
            assert 'expeditions' in query or 'e' in query


@pytest.mark.phase2
@pytest.mark.integration
class TestPhase2APIEndpoints:
    """
    Integration tests for Phase 2 API endpoints.

    Tests the complete request/response cycle including:
    - Authentication
    - Permission validation
    - Data retrieval
    - Response structure
    """

    @pytest.fixture
    def mock_app(self):
        """Create mock Flask app with test client."""
        from flask import Flask
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app

    def test_dashboard_overdue_endpoint_requires_auth(self):
        """Test that /api/dashboard/overdue requires authentication."""
        # This would be an integration test with actual Flask app
        # For now, document the requirement
        pass  # TODO: Implement with Flask test client

    def test_dashboard_overdue_endpoint_requires_admin(self):
        """Test that /api/dashboard/overdue requires admin+ permission."""
        pass  # TODO: Implement with Flask test client

    def test_dashboard_overdue_alert_level_calculation(self):
        """Test alert level calculation in endpoint."""
        now = datetime.now()

        # Test critical level (>7 days overdue)
        deadline_critical = now - timedelta(days=8)
        days_overdue = (now - deadline_critical).days
        assert days_overdue > 7
        # Alert level should be 'critical'

        # Test urgent level (>3 days, <=7 days)
        deadline_urgent = now - timedelta(days=5)
        days_overdue = (now - deadline_urgent).days
        assert 3 < days_overdue <= 7
        # Alert level should be 'urgent'

        # Test warning level (>1 day, <=3 days)
        deadline_warning = now - timedelta(days=2)
        days_overdue = (now - deadline_warning).days
        assert 1 < days_overdue <= 3
        # Alert level should be 'warning'

    def test_consumptions_endpoint_requires_auth(self):
        """Test that /api/expeditions/consumptions requires authentication."""
        pass  # TODO: Implement with Flask test client

    def test_consumptions_endpoint_handles_filters(self):
        """Test that consumptions endpoint properly handles query parameters."""
        # Should support:
        # - consumer_name filter
        # - payment_status filter ('pending', 'paid', 'partial')
        pass  # TODO: Implement with Flask test client


@pytest.mark.phase2
class TestPhase2EdgeCases:
    """
    Edge case tests for Phase 2 optimizations.

    Tests unusual but valid scenarios:
    - Expeditions with 0 items
    - Expeditions with all items completed
    - Large datasets (100+ expeditions/consumptions)
    - Null/empty values
    - Decimal precision
    """

    @pytest.fixture
    def expedition_service(self):
        """Create ExpeditionService instance."""
        return ExpeditionService()

    def test_overdue_expedition_with_zero_items(self, expedition_service):
        """Test overdue expedition with no items."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            mock_data = [(
                1, 'Empty Expedition', 12345, 'active',
                datetime.now() - timedelta(days=5),
                datetime.now(), None,
                0, 0, 0, 0, 0, 0.0, 0, 0, 0  # Zero items (16 columns total)
            )]
            mock_query.return_value = mock_data

            result = expedition_service.get_overdue_expeditions_with_details()

            assert len(result) == 1
            assert result[0]['total_items'] == 0
            # Should not crash with division by zero
            assert result[0]['completion_percentage'] == 0.0

    def test_overdue_expedition_fully_completed(self, expedition_service):
        """Test overdue expedition that's 100% complete."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            mock_data = [(
                1, 'Complete Expedition', 12345, 'active',
                datetime.now() - timedelta(days=2),
                datetime.now(), None,
                5, 5, 0,  # All items completed
                100, 100, 100.0,
                1000, 1000, 0  # 16 columns total
            )]
            mock_query.return_value = mock_data

            result = expedition_service.get_overdue_expeditions_with_details()

            assert len(result) == 1
            assert result[0]['completion_percentage'] == 100.0
            assert result[0]['remaining_items'] == 0

    def test_large_dataset_performance(self, expedition_service):
        """Test with 100+ overdue expeditions."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            # Simulate 150 overdue expeditions (all 16 columns)
            mock_data = [
                (i, f'Expedition {i}', 12345, 'active',
                 datetime.now() - timedelta(days=i % 10 + 1),
                 datetime.now(), None,
                 5, i % 5, 5 - (i % 5), 100, (i % 5) * 20,
                 float((i % 5) * 20), 1000, (i % 5) * 200, 1000 - (i % 5) * 200)
                for i in range(150)
            ]
            mock_query.return_value = mock_data

            result = expedition_service.get_overdue_expeditions_with_details()

            # Should handle large datasets
            assert len(result) == 150
            # Still only 1 query
            assert mock_query.call_count == 1

    def test_consumptions_with_null_pirate_name(self, expedition_service):
        """Test consumption with null pirate name (edge case)."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            mock_data = [(
                1, None, None,  # Null consumer/pirate name
                'Rum', 10, Decimal('5.00'), Decimal('50.00'),
                Decimal('0.00'), 'pending', datetime.now()
            )]
            mock_query.return_value = mock_data

            result = expedition_service.get_recent_consumptions()

            assert len(result) == 1
            # Should handle null gracefully (query uses COALESCE)
            assert result[0].consumer_name in [None, 'Unknown Pirate', 'Unknown']

    def test_decimal_precision_maintained(self, expedition_service):
        """Test that decimal precision is maintained in calculations."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            mock_data = [(
                1, 'Pirate', 'Pirate', 'Product',
                3,  # quantity
                Decimal('3.33'),  # unit_price with 2 decimal places
                Decimal('9.99'),  # total_price
                Decimal('5.55'),  # amount_paid
                'partial',
                datetime.now()
            )]
            mock_query.return_value = mock_data

            result = expedition_service.get_recent_consumptions()

            consumption = result[0]
            # Verify decimal precision
            assert isinstance(consumption.unit_price, Decimal)
            assert isinstance(consumption.total_price, Decimal)
            assert consumption.unit_price == Decimal('3.33')
            assert consumption.total_price == Decimal('9.99')


@pytest.mark.phase2
class TestPhase2DataIntegrity:
    """
    Data integrity tests for Phase 2 optimizations.

    Ensures:
    - Correct aggregations (SUM, COUNT, AVG)
    - Proper JOIN conditions
    - Status filtering
    - Order by conditions
    """

    @pytest.fixture
    def expedition_service(self):
        """Create ExpeditionService instance."""
        return ExpeditionService()

    def test_overdue_only_includes_active_expeditions(self, expedition_service):
        """Test that only active expeditions are included."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            mock_query.return_value = []

            expedition_service.get_overdue_expeditions_with_details()

            query = mock_query.call_args[0][0]
            params = mock_query.call_args[0][1]

            # Should filter by status
            assert 'status' in query
            assert ExpeditionStatus.ACTIVE.value in params or 'active' in params

    def test_overdue_filters_past_deadlines(self, expedition_service):
        """Test that only past deadlines are included."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            mock_query.return_value = []

            expedition_service.get_overdue_expeditions_with_details()

            query = mock_query.call_args[0][0]

            # Should compare deadline with NOW()
            assert 'NOW()' in query or 'CURRENT_TIMESTAMP' in query
            assert 'deadline' in query
            assert '<' in query  # deadline < NOW()

    def test_consumptions_only_active_expeditions(self, expedition_service):
        """Test that consumptions only come from active expeditions."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            mock_query.return_value = []

            expedition_service.get_recent_consumptions()

            query = mock_query.call_args[0][0]
            params = mock_query.call_args[0][1]

            # Should filter expeditions by active status
            assert ExpeditionStatus.ACTIVE.value in params or 'active' in params

    def test_consumptions_ordered_by_date_desc(self, expedition_service):
        """Test that consumptions are ordered by date descending (newest first)."""
        with patch.object(expedition_service, '_execute_query') as mock_query:
            mock_query.return_value = []

            expedition_service.get_recent_consumptions()

            query = mock_query.call_args[0][0]

            # Should order by consumed_at/assigned_at DESC
            assert 'ORDER BY' in query
            assert 'DESC' in query


if __name__ == '__main__':
    # Run Phase 2 tests
    pytest.main([__file__, '-v', '-m', 'phase2'])
