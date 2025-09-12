"""
Contract tests for end-to-end workflow validation.
Tests complete user workflows against real database to catch integration issues.
"""

import pytest
import os
from decimal import Decimal

# Set environment for contract testing
os.environ['CONTRACT_TESTING'] = 'true'

from database.connection import DatabaseManager
from services.user_service import UserService
from services.product_service import ProductService
from services.sales_service import SalesService
from models.user import CreateUserRequest
from models.product import CreateProductRequest, AddStockRequest
from models.sale import CreateSaleRequest, CreateSaleItemRequest
from utils.input_sanitizer import InputSanitizer


class TestWorkflowContracts:
    """End-to-end workflow contract tests."""
    
    def setup_method(self):
        """Set up test environment with real services."""
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            pytest.skip("DATABASE_URL not set for contract testing")
        
        self.db_manager = DatabaseManager(database_url)
        self.user_service = UserService()
        self.product_service = ProductService()
        self.sales_service = SalesService()
        
        # Clean up test data
        self._cleanup_test_data()
    
    def teardown_method(self):
        """Clean up after each test."""
        self._cleanup_test_data()
    
    def _cleanup_test_data(self):
        """Remove any test data from database."""
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Delete in reverse dependency order
                cursor.execute("DELETE FROM ItensVenda WHERE venda_id IN (SELECT id FROM Vendas WHERE comprador LIKE 'contract_test_%')")
                cursor.execute("DELETE FROM Pagamentos WHERE venda_id IN (SELECT id FROM Vendas WHERE comprador LIKE 'contract_test_%')")
                cursor.execute("DELETE FROM Vendas WHERE comprador LIKE 'contract_test_%'")
                cursor.execute("DELETE FROM Estoque WHERE produto_id IN (SELECT id FROM Produtos WHERE nome LIKE 'contract_test_%')")
                cursor.execute("DELETE FROM Produtos WHERE nome LIKE 'contract_test_%'")
                cursor.execute("DELETE FROM Usuarios WHERE username LIKE 'contract_test_%'")
                conn.commit()
    
    @pytest.mark.contract
    def test_complete_buy_workflow_contract(self):
        """
        Contract test for complete buy workflow.
        This should catch schema mismatches that cause runtime failures.
        """
        # Step 1: Create user
        user_request = CreateUserRequest(
            username="contract_test_buyer",
            password="test123",
            nivel="admin"
        )
        user = self.user_service.create_user(user_request)
        assert user is not None
        assert user.username == "contract_test_buyer"
        
        # Step 2: Create product
        product_request = CreateProductRequest(
            nome="contract_test_product",
            emoji="🧪"
        )
        product = self.product_service.create_product(product_request)
        assert product is not None
        assert product.nome == "contract_test_product"
        
        # Step 3: Add stock
        stock_request = AddStockRequest(
            produto_id=product.id,
            quantidade=10,
            valor=Decimal('25.00'),
            custo=Decimal('15.00')
        )
        stock_item = self.product_service.add_stock(stock_request)
        assert stock_item is not None
        assert stock_item.produto_id == product.id
        assert stock_item.quantidade == 10
        
        # Step 4: Verify stock availability
        available_stock = self.product_service.get_available_quantity(product.id)
        assert available_stock == 10
        
        # Step 5: Create sale (this was failing with column "data" error)
        sale_item_request = CreateSaleItemRequest(
            produto_id=product.id,
            quantidade=3,
            valor_unitario=Decimal('25.00')
        )
        
        sale_request = CreateSaleRequest(
            comprador="contract_test_buyer",
            items=[sale_item_request]
        )
        
        # This should NOT fail with "column data does not exist"
        sale = self.sales_service.create_sale(sale_request)
        assert sale is not None
        assert sale.comprador == "contract_test_buyer"
        assert len(sale.items) == 1
        assert sale.items[0].quantidade == 3
        
        # Step 6: Verify stock was consumed
        remaining_stock = self.product_service.get_available_quantity(product.id)
        assert remaining_stock == 7  # 10 - 3 = 7
        
        # Step 7: Verify sale can be retrieved
        retrieved_sale = self.sales_service.get_sale_by_id(sale.id)
        assert retrieved_sale is not None
        assert retrieved_sale.comprador == "contract_test_buyer"
        assert len(retrieved_sale.items) == 1
    
    @pytest.mark.contract
    def test_product_lifecycle_contract(self):
        """Contract test for complete product lifecycle."""
        # Create product
        product_request = CreateProductRequest(
            nome="contract_test_lifecycle",
            emoji="🔄"
        )
        product = self.product_service.create_product(product_request)
        assert product.nome == "contract_test_lifecycle"
        
        # Add multiple stock batches (tests FIFO)
        stock1 = AddStockRequest(
            produto_id=product.id,
            quantidade=5,
            valor=Decimal('10.00'),
            custo=Decimal('5.00')
        )
        stock2 = AddStockRequest(
            produto_id=product.id,
            quantidade=8,
            valor=Decimal('12.00'),
            custo=Decimal('6.00')
        )
        
        self.product_service.add_stock(stock1)
        self.product_service.add_stock(stock2)
        
        # Verify total stock
        total_stock = self.product_service.get_available_quantity(product.id)
        assert total_stock == 13  # 5 + 8
        
        # Test stock consumption (FIFO)
        consumed = self.product_service.consume_stock(product.id, 7)  # Should consume all of first batch + 2 from second
        assert consumed == True
        
        remaining = self.product_service.get_available_quantity(product.id)
        assert remaining == 6  # 13 - 7 = 6
        
        # Test product update
        updated = self.product_service.update_product_name(product.id, "contract_test_lifecycle_updated")
        assert updated == True
        
        # Verify update
        updated_product = self.product_service.get_product_by_id(product.id)
        assert updated_product.nome == "contract_test_lifecycle_updated"
        
        # Test product deletion (should cascade delete stock)
        deleted = self.product_service.delete_product(product.id)
        assert deleted == True
        
        # Verify deletion
        deleted_product = self.product_service.get_product_by_id(product.id)
        assert deleted_product is None
    
    @pytest.mark.contract 
    def test_user_management_contract(self):
        """Contract test for user management workflows."""
        # Create user
        user_request = CreateUserRequest(
            username="contract_test_user",
            password="secure123",
            nivel="user"
        )
        user = self.user_service.create_user(user_request)
        assert user.username == "contract_test_user"
        assert user.nivel == "user"
        
        # Test user lookup
        found_user = self.user_service.get_user_by_username("contract_test_user")
        assert found_user is not None
        assert found_user.id == user.id
        
        # Test username existence check
        exists = self.user_service.username_exists("contract_test_user")
        assert exists == True
        
        # Test user update
        updated = self.user_service.update_user_level(user.id, "admin")
        assert updated == True
        
        # Verify update
        updated_user = self.user_service.get_user_by_id(user.id)
        assert updated_user.nivel == "admin"
        
        # Test user deletion
        deleted = self.user_service.delete_user(user.id)
        assert deleted == True
        
        # Verify deletion
        deleted_user = self.user_service.get_user_by_id(user.id)
        assert deleted_user is None
    
    @pytest.mark.contract
    def test_sales_and_payments_contract(self):
        """Contract test for sales and payment workflows."""
        # Setup: Create user and product with stock
        user_request = CreateUserRequest(
            username="contract_test_payment_buyer",
            password="test123",
            nivel="admin"
        )
        user = self.user_service.create_user(user_request)
        
        product_request = CreateProductRequest(
            nome="contract_test_payment_product",
            emoji="💰"
        )
        product = self.product_service.create_product(product_request)
        
        stock_request = AddStockRequest(
            produto_id=product.id,
            quantidade=20,
            valor=Decimal('50.00'),
            custo=Decimal('30.00')
        )
        self.product_service.add_stock(stock_request)
        
        # Create sale
        sale_item = CreateSaleItemRequest(
            produto_id=product.id,
            quantidade=5,
            valor_unitario=Decimal('50.00')
        )
        sale_request = CreateSaleRequest(
            comprador="contract_test_payment_buyer",
            items=[sale_item]
        )
        sale = self.sales_service.create_sale(sale_request)
        
        # Test debt tracking
        unpaid_sales = self.sales_service.get_unpaid_sales("contract_test_payment_buyer")
        assert len(unpaid_sales) == 1
        assert unpaid_sales[0].sale.id == sale.id
        
        # Test debt summary
        debt_summary = self.sales_service.get_buyer_debt_summary("contract_test_payment_buyer")
        assert debt_summary["balance_due"] == 250.0  # 5 * 50.00
        
        # Make partial payment
        from models.sale import CreatePaymentRequest
        payment_request = CreatePaymentRequest(
            venda_id=sale.id,
            valor_pago=Decimal('100.00')
        )
        payment = self.sales_service.create_payment(payment_request)
        assert payment.valor_pago == Decimal('100.00')
        
        # Check updated debt
        updated_debt = self.sales_service.get_buyer_debt_summary("contract_test_payment_buyer")
        assert updated_debt["balance_due"] == 150.0  # 250 - 100 = 150
        
        # Make full payment
        final_payment_request = CreatePaymentRequest(
            venda_id=sale.id,
            valor_pago=Decimal('150.00')
        )
        final_payment = self.sales_service.create_payment(final_payment_request)
        
        # Verify no unpaid sales
        final_unpaid = self.sales_service.get_unpaid_sales("contract_test_payment_buyer")
        assert len(final_unpaid) == 0
    
    @pytest.mark.contract
    def test_inventory_fifo_contract(self):
        """Contract test for FIFO inventory consumption."""
        # Create product
        product_request = CreateProductRequest(
            nome="contract_test_fifo",
            emoji="📦"
        )
        product = self.product_service.create_product(product_request)
        
        # Add stock in three batches with different costs
        batch1 = AddStockRequest(
            produto_id=product.id,
            quantidade=10,
            valor=Decimal('20.00'),
            custo=Decimal('10.00')
        )
        batch2 = AddStockRequest(
            produto_id=product.id,
            quantidade=15,
            valor=Decimal('25.00'),
            custo=Decimal('12.00')
        )
        batch3 = AddStockRequest(
            produto_id=product.id,
            quantidade=8,
            valor=Decimal('30.00'),
            custo=Decimal('15.00')
        )
        
        self.product_service.add_stock(batch1)
        self.product_service.add_stock(batch2)
        self.product_service.add_stock(batch3)
        
        # Total: 33 items
        total = self.product_service.get_available_quantity(product.id)
        assert total == 33
        
        # Consume 12 items (should consume all of batch1 + 2 from batch2)
        consumed = self.product_service.consume_stock(product.id, 12)
        assert consumed == True
        
        remaining = self.product_service.get_available_quantity(product.id)
        assert remaining == 21  # 33 - 12 = 21
        
        # Consume 13 more (should consume remaining 13 from batch2)
        consumed2 = self.product_service.consume_stock(product.id, 13)
        assert consumed2 == True
        
        final_remaining = self.product_service.get_available_quantity(product.id)
        assert final_remaining == 8  # Should only have batch3 left
    
    @pytest.mark.contract
    def test_input_sanitization_contract(self):
        """Contract test for input sanitization across services."""
        # Test malicious inputs are properly sanitized
        malicious_inputs = [
            "'; DROP TABLE usuarios; --",
            "<script>alert('xss')</script>",
            "../../etc/passwd",
            "admin' OR '1'='1",
            "\\x00\\x01\\x02"
        ]
        
        for malicious_input in malicious_inputs:
            # Test user creation with malicious username
            try:
                sanitized = InputSanitizer.sanitize_username(malicious_input)
                # Should not contain SQL injection patterns
                assert "DROP" not in sanitized.upper()
                assert "SCRIPT" not in sanitized.upper()
                assert "'" not in sanitized
            except ValueError:
                # Expected for invalid inputs
                pass
            
            # Test product name sanitization
            try:
                sanitized_product = InputSanitizer.sanitize_product_name(malicious_input)
                assert len(sanitized_product) <= 100  # Within limits
                assert "<script>" not in sanitized_product
            except ValueError:
                # Expected for invalid inputs
                pass


if __name__ == "__main__":
    # Run contract tests directly
    pytest.main([__file__, "-v", "-m", "contract"])