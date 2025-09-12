"""
Test the business service report generation specifically.
This would have caught the missing get_sale_items method.
"""

import pytest
import os
from unittest.mock import Mock, patch

from services.handler_business_service import HandlerBusinessService
from models.handler_models import ReportRequest, ReportResponse
from models.sale import Sale, SaleItem
from models.product import Product


class TestBusinessServiceDividas:
    """Test business service debt report generation."""
    
    @pytest.fixture(autouse=True)
    def setup_environment(self):
        """Setup test environment."""
        os.environ["DATABASE_URL"] = "postgresql://test:test@localhost:5432/test_db"
        os.environ["BOT_TOKEN"] = "test_token"
        yield
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]
        if "BOT_TOKEN" in os.environ:
            del os.environ["BOT_TOKEN"]
    
    def test_generate_debt_report_calls_get_sale_items(self):
        """
        Test that debt report generation calls get_sale_items method.
        This would have caught the missing method error.
        """
        # Mock the services that business service depends on
        mock_sales_service = Mock()
        mock_product_service = Mock()
        
        # Setup mock data
        sample_sales = [
            Sale(id=1, comprador="testuser", data="2024-01-01"),
            Sale(id=2, comprador="testuser", data="2024-01-02")
        ]
        
        sample_items = {
            1: [SaleItem(id=1, venda_id=1, produto_id=1, quantidade=2, valor_unitario=50.0)],
            2: [SaleItem(id=2, venda_id=2, produto_id=2, quantidade=1, valor_unitario=30.0)]
        }
        
        sample_products = {
            1: Product(id=1, nome="Test Product 1", emoji="🎮", media_type=None, media_file_id=None),
            2: Product(id=2, nome="Test Product 2", emoji="🖱️", media_type=None, media_file_id=None)
        }
        
        # Configure mocks
        mock_sales_service.get_sales_by_buyer.return_value = sample_sales
        mock_sales_service.get_sale_items.side_effect = lambda sale_id: sample_items.get(sale_id, [])
        mock_product_service.get_product_by_id.side_effect = lambda prod_id: sample_products.get(prod_id)
        
        # Patch the service container to return our mocks
        with patch('core.modern_service_container.get_sales_service', return_value=mock_sales_service), \
             patch('core.modern_service_container.get_product_service', return_value=mock_product_service), \
             patch('services.base_service.get_db_manager', return_value=Mock()):
            
            # Create business service
            business_service = HandlerBusinessService(None)
            business_service.sales_service = mock_sales_service
            business_service.product_service = mock_product_service
            
            # Create report request
            request = ReportRequest(report_type="debts", buyer_name="testuser")
            
            # This would fail if get_sale_items method was missing
            response = business_service.generate_report(request)
            
            # Verify the method was called
            mock_sales_service.get_sale_items.assert_called()
            assert mock_sales_service.get_sale_items.call_count == 2  # Called for each sale
            
            # Verify successful response
            assert response.success == True
            assert len(response.report_data) == 2
            
            # Verify data structure
            first_item = response.report_data[0]
            assert 'id' in first_item
            assert 'produto_nome' in first_item
            assert 'quantidade' in first_item
            assert 'valor_total' in first_item
            assert 'data_venda' in first_item
    
    def test_generate_debt_report_handles_missing_method_gracefully(self):
        """
        Test that business service handles missing methods gracefully.
        This simulates the original bug condition.
        """
        mock_sales_service = Mock()
        
        # Setup sales but no get_sale_items method (simulate the original bug)
        sample_sales = [Sale(id=1, comprador="testuser", data="2024-01-01")]
        mock_sales_service.get_sales_by_buyer.return_value = sample_sales
        
        # Remove the get_sale_items method to simulate the original bug
        del mock_sales_service.get_sale_items
        
        with patch('core.modern_service_container.get_sales_service', return_value=mock_sales_service), \
             patch('services.base_service.get_db_manager', return_value=Mock()):
            
            business_service = HandlerBusinessService(None)
            business_service.sales_service = mock_sales_service
            
            request = ReportRequest(report_type="debts", buyer_name="testuser")
            
            # This should return error response, not crash
            response = business_service.generate_report(request)
            
            # Should return error response
            assert response.success == False
            assert response.report_data == []
            assert "Erro ao gerar relatório" in response.message