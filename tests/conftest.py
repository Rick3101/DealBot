"""
Test configuration and fixtures for the Telegram bot handlers.
Provides common test utilities, mocks, and fixtures.
"""

import pytest
import asyncio
import logging
import os
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from typing import Dict, Any, Optional
from dataclasses import dataclass
from telegram import Update, User, Chat, Message
from telegram.ext import ContextTypes, ConversationHandler

# Suppress logging during tests
logging.getLogger().setLevel(logging.CRITICAL)

# Import mock databases
from tests.mocks.mock_database import get_mock_db_manager, reset_mock_database
from tests.mocks.schema_accurate_mock_database import get_schema_accurate_mock_db, reset_schema_mock_db

# Import service container components
from core.modern_service_container import initialize_services, get_container, get_service_registry
from core.interfaces import IUserService, IProductService, ISalesService, ISmartContractService


@dataclass
class MockTelegramObjects:
    """Container for mock Telegram objects"""
    update: Update
    context: ContextTypes.DEFAULT_TYPE
    user: User
    chat: Chat
    message: Message
    
    @staticmethod
    def create_update(callback_data: str = None, text: str = None, chat_id: int = 12345, user_id: int = 67890):
        """Create a complete mock update with proper bot associations"""
        # Create mock bot
        mock_bot = Mock()
        mock_bot.send_message = AsyncMock()
        mock_bot.edit_message_text = AsyncMock()
        mock_bot.delete_message = AsyncMock()
        mock_bot.defaults = None
        
        # Create user
        user = User(
            id=user_id,
            is_bot=False,
            first_name="Test",
            last_name="User",
            username="testuser"
        )
        
        # Create chat
        chat = Chat(id=chat_id, type=Chat.PRIVATE)
        
        # Create message with bot association
        message = Mock(spec=Message)
        message.message_id = 1
        message.from_user = user
        message.chat = chat
        message.text = text or "/test"
        message.reply_text = AsyncMock()
        message.edit_text = AsyncMock()
        message.delete = AsyncMock()
        message._bot = mock_bot  # Associate bot with message
        message.get_bot = Mock(return_value=mock_bot)
        
        # Create callback query if needed
        callback_query = None
        if callback_data:
            callback_query = Mock()
            callback_query.data = callback_data
            callback_query.from_user = user
            callback_query.message = message
            callback_query.answer = AsyncMock()
            callback_query._bot = mock_bot
            callback_query.get_bot = Mock(return_value=mock_bot)
        
        # Create update
        update = Mock(spec=Update)
        update.update_id = 1
        update.effective_user = user
        update.effective_chat = chat
        update.message = message if not callback_data else None
        update.callback_query = callback_query
        update._bot = mock_bot
        update.get_bot = Mock(return_value=mock_bot)
        
        return update


class MockServiceContainer:
    """Mock service container for testing"""
    
    def __init__(self):
        self.services = {}
        self._initialized = True
    
    def get_service(self, service_type):
        if service_type not in self.services:
            self.services[service_type] = Mock()
        return self.services[service_type]
    
    def register_service(self, service_type, service_instance):
        self.services[service_type] = service_instance


@pytest.fixture
def mock_user():
    """Create a mock Telegram user"""
    return User(
        id=12345,
        is_bot=False,
        first_name="Test",
        last_name="User",
        username="testuser",
        language_code="pt-BR"
    )


@pytest.fixture
def mock_chat():
    """Create a mock Telegram chat"""
    return Chat(
        id=-100123456789,
        type=Chat.PRIVATE
    )


@pytest.fixture
def mock_message(mock_user, mock_chat):
    """Create a mock Telegram message"""
    # Create mock bot
    mock_bot = Mock()
    mock_bot.send_message = AsyncMock()
    mock_bot.edit_message_text = AsyncMock()
    mock_bot.delete_message = AsyncMock()
    mock_bot.defaults = None
    
    message = Mock(spec=Message)
    message.message_id = 1
    message.from_user = mock_user
    message.chat = mock_chat
    message.text = "/test"
    message.reply_text = AsyncMock()
    message.edit_text = AsyncMock()
    message.delete = AsyncMock()
    message._bot = mock_bot  # Associate bot with message
    message.get_bot = Mock(return_value=mock_bot)
    return message


@pytest.fixture
def mock_context():
    """Create a mock Telegram context"""
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    context.user_data = {}
    context.chat_data = {}
    context.bot_data = {}
    context.args = []
    context.bot = Mock()
    context.bot.send_message = AsyncMock()
    context.bot.edit_message_text = AsyncMock()
    context.bot.delete_message = AsyncMock()
    return context


@pytest.fixture
def mock_update(mock_user, mock_chat, mock_message):
    """Create a mock Telegram update"""
    update = Mock(spec=Update)
    update.update_id = 1
    update.effective_user = mock_user
    update.effective_chat = mock_chat
    update.message = mock_message
    update.callback_query = None
    return update


@pytest.fixture
def mock_telegram_objects(mock_update, mock_context, mock_user, mock_chat, mock_message):
    """Create a container with all mock Telegram objects"""
    return MockTelegramObjects(
        update=mock_update,
        context=mock_context,
        user=mock_user,
        chat=mock_chat,
        message=mock_message
    )


@pytest.fixture
def mock_user_service():
    """Create a mock user service"""
    service = Mock()
    service.authenticate_user = AsyncMock(return_value=True)
    service.get_user_permission_level = Mock(return_value="owner")  # Set to owner for permissions
    service.create_user = AsyncMock(return_value=1)
    service.update_user = AsyncMock(return_value=True)
    service.delete_user = AsyncMock(return_value=True)
    service.get_all_users = AsyncMock(return_value=[])
    service.username_exists = Mock(return_value=False)  # Default: username doesn't exist
    service.check_username_exists = Mock(return_value=False)  # Alternative name
    service.get_user_by_chat_id = Mock(return_value=None)
    service.get_user_by_username = Mock(return_value=None)
    return service


@pytest.fixture
def mock_product_service():
    """Create a mock product service"""
    service = Mock()
    service.get_all_products = AsyncMock(return_value=[])
    service.get_product_by_id = AsyncMock(return_value=None)
    service.create_product = AsyncMock(return_value=1)
    service.update_product = AsyncMock(return_value=True)
    service.delete_product = AsyncMock(return_value=True)
    service.product_exists = Mock(return_value=False)
    service.get_available_quantity = Mock(return_value=0)
    service.add_stock = Mock(return_value=True)
    service.consume_stock = Mock(return_value=True)
    return service


@pytest.fixture
def mock_sales_service():
    """Create a mock sales service"""
    service = Mock()
    service.create_sale = AsyncMock(return_value=1)
    service.get_sales = AsyncMock(return_value=[])
    service.process_payment = AsyncMock(return_value=True)
    service.get_debt_report = AsyncMock(return_value=[])
    return service


@pytest.fixture
def mock_smartcontract_service():
    """Create a mock smart contract service"""
    service = Mock()
    service.create_contract = AsyncMock(return_value=1)
    service.add_transaction = AsyncMock(return_value=1)
    service.confirm_transaction = AsyncMock(return_value=True)
    service.get_contract_transactions = AsyncMock(return_value=[])
    return service


@pytest.fixture
def mock_service_container(mock_user_service, mock_product_service, mock_sales_service, mock_smartcontract_service):
    """Create a mock service container with all services"""
    container = MockServiceContainer()
    container.register_service("user_service", mock_user_service)
    container.register_service("product_service", mock_product_service)
    container.register_service("sales_service", mock_sales_service)
    container.register_service("smartcontract_service", mock_smartcontract_service)
    return container


@pytest.fixture
def mock_handler_business_service():
    """Create a mock handler business service"""
    service = Mock()
    service.handle_login = AsyncMock(return_value={"success": True, "message": "Login successful"})
    service.handle_product_creation = AsyncMock(return_value={"success": True, "product_id": 1})
    service.handle_purchase = AsyncMock(return_value={"success": True, "sale_id": 1})
    service.handle_inventory_update = AsyncMock(return_value={"success": True})
    return service


@pytest.fixture(autouse=True)
def test_environment():
    """Set up test environment variables automatically for all tests"""
    original_env = os.environ.copy()
    
    # Set test environment variables - only override if not already set
    test_vars = {
        "ENVIRONMENT": "development"
    }
    
    for key, value in test_vars.items():
        os.environ[key] = value
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def schema_accurate_db():
    """Provide a schema-accurate mock database for testing."""
    reset_schema_mock_db()
    db = get_schema_accurate_mock_db()
    yield db
    reset_schema_mock_db()


@pytest.fixture
def mock_db_manager_with_schema():
    """Mock database manager that uses schema-accurate database."""
    from tests.mocks.schema_accurate_mock_database import get_schema_accurate_mock_db
    
    mock_db = get_schema_accurate_mock_db()
    
    with patch('database.get_db_manager') as mock_manager:
        mock_manager.return_value = mock_db
        yield mock_manager


@pytest.fixture(scope="function")
def event_loop():
    """Create an event loop for async tests"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


class TestDataFactory:
    """Factory for creating test data"""
    
    @staticmethod
    def create_user_data(
        username: str = "testuser",
        password: str = "testpass",
        level: str = "admin",
        chat_id: int = 12345
    ) -> Dict[str, Any]:
        return {
            "username": username,
            "password": password,
            "level": level,
            "chat_id": chat_id
        }
    
    @staticmethod
    def create_product_data(
        name: str = "Test Product",
        emoji: str = "🧪",
        media_file_id: Optional[str] = None
    ) -> Dict[str, Any]:
        return {
            "name": name,
            "emoji": emoji,
            "media_file_id": media_file_id
        }
    
    @staticmethod
    def create_sale_data(
        buyer_name: str = "Test Buyer",
        total_amount: float = 100.0
    ) -> Dict[str, Any]:
        return {
            "buyer_name": buyer_name,
            "total_amount": total_amount,
            "items": []
        }


@pytest.fixture
def test_data_factory():
    """Provide test data factory"""
    return TestDataFactory


# Custom assertions
def assert_handler_response(response, expected_message: str = None, expected_state: int = None):
    """Assert handler response properties"""
    assert hasattr(response, 'message')
    assert hasattr(response, 'next_state')
    assert hasattr(response, 'end_conversation')
    
    if expected_message:
        assert expected_message in response.message
    
    if expected_state is not None:
        assert response.next_state == expected_state


def assert_telegram_call_made(mock_method, expected_text: str = None):
    """Assert that a Telegram API call was made"""
    assert mock_method.called
    if expected_text:
        call_args = mock_method.call_args
        assert expected_text in str(call_args)


# Test utilities
class TestUtils:
    """Utility functions for tests"""
    
    @staticmethod
    async def simulate_conversation_flow(handler, updates_and_contexts, expected_states):
        """Simulate a complete conversation flow"""
        results = []
        for i, (update, context) in enumerate(updates_and_contexts):
            result = await handler(update, context)
            results.append(result)
            if i < len(expected_states):
                assert result == expected_states[i], f"State mismatch at step {i}: expected {expected_states[i]}, got {result}"
        return results
    
    @staticmethod
    def create_callback_query_update(data: str, mock_telegram_objects):
        """Create an update with callback query"""
        callback_query = Mock()
        callback_query.data = data
        callback_query.from_user = mock_telegram_objects.user
        callback_query.message = mock_telegram_objects.message
        callback_query.answer = AsyncMock()
        
        mock_telegram_objects.update.callback_query = callback_query
        mock_telegram_objects.update.message = None
        return mock_telegram_objects.update


@pytest.fixture
def test_utils():
    """Provide test utilities"""
    return TestUtils


# Database mocking fixtures

@pytest.fixture(autouse=True)
def mock_database():
    """Auto-use fixture that mocks database operations for all tests."""
    # Reset mock database before each test
    reset_mock_database()
    mock_db = get_mock_db_manager()
    
    # Patch database initialization and connection functions
    with patch('database.initialize_database') as mock_init_db, \
         patch('database.get_db_manager', return_value=mock_db) as mock_get_db, \
         patch('database.close_database') as mock_close_db, \
         patch('database.connection.get_db_manager', return_value=mock_db):
        
        # Configure mocks
        mock_init_db.return_value = None
        mock_close_db.return_value = None
        
        yield mock_db


@pytest.fixture  
def mock_database_manager():
    """Provide access to mock database manager."""
    return get_mock_db_manager()


@pytest.fixture
def mock_all_services():
    """Mock all service dependencies with database operations."""
    with patch('services.user_service.UserService') as mock_user_service, \
         patch('services.product_service.ProductService') as mock_product_service, \
         patch('services.sales_service.SalesService') as mock_sales_service, \
         patch('services.handler_business_service.HandlerBusinessService') as mock_business_service:
        
        # Configure service mocks
        user_service_instance = Mock()
        product_service_instance = Mock()
        sales_service_instance = Mock()
        business_service_instance = Mock()
        
        # Configure return values for common operations
        user_service_instance.authenticate_user.return_value = {"success": True, "user_id": 1}
        user_service_instance.get_user_by_chat_id.return_value = Mock(id=1, username="testuser", level=Mock(value="admin"))
        
        product_service_instance.get_all_products.return_value = []
        product_service_instance.create_product.return_value = 1
        
        sales_service_instance.create_sale.return_value = 1
        
        business_service_instance.get_products_for_purchase.return_value = []
        business_service_instance.process_purchase.return_value = Mock(success=True, message="Success")
        
        mock_user_service.return_value = user_service_instance
        mock_product_service.return_value = product_service_instance
        mock_sales_service.return_value = sales_service_instance
        mock_business_service.return_value = business_service_instance
        
        yield {
            'user_service': user_service_instance,
            'product_service': product_service_instance,
            'sales_service': sales_service_instance,
            'business_service': business_service_instance
        }


@pytest.fixture
def mock_environment():
    """Mock environment variables for tests."""
    test_env = {
        'DATABASE_URL': 'mock://test',
        'BOT_TOKEN': 'test_token_123',
        'ENVIRONMENT': 'development'
    }
    
    with patch.dict(os.environ, test_env):
        yield test_env


@pytest.fixture
def initialized_service_container(mock_user_service, mock_product_service, mock_sales_service, mock_smartcontract_service):
    """
    Fixture that provides a properly initialized service container with mock services.
    Tests can use this when they need the service container to be available.
    """
    # Mock the service container functions directly to return mock services
    with patch('core.modern_service_container.get_user_service', return_value=mock_user_service), \
         patch('core.modern_service_container.get_product_service', return_value=mock_product_service), \
         patch('core.modern_service_container.get_sales_service', return_value=mock_sales_service), \
         patch('core.modern_service_container.get_smartcontract_service', return_value=mock_smartcontract_service), \
         patch('core.modern_service_container.get_container') as mock_get_container, \
         patch('core.modern_service_container.get_service_registry') as mock_get_registry:
        
        # Create a mock container that returns our services
        mock_container = Mock()
        mock_container.get_service.side_effect = lambda service_type: {
            IUserService: mock_user_service,
            IProductService: mock_product_service,
            ISalesService: mock_sales_service,
            ISmartContractService: mock_smartcontract_service
        }.get(service_type, Mock())
        
        mock_registry = Mock()
        mock_registry.get_container.return_value = mock_container
        
        mock_get_container.return_value = mock_container
        mock_get_registry.return_value = mock_registry
        
        yield mock_container


@pytest.fixture(autouse=True)
def mock_service_container_initialization(mock_user_service, mock_product_service, mock_sales_service, mock_smartcontract_service):
    """
    Auto-use fixture that mocks the entire service container system.
    This prevents 'Services not initialized' errors by mocking all service accessor functions.
    """
    mock_db = get_mock_db_manager()
    
    # Create mock container and registry
    mock_container = Mock()
    mock_container.get_service.side_effect = lambda service_type: {
        IUserService: mock_user_service,
        IProductService: mock_product_service,
        ISalesService: mock_sales_service,
        ISmartContractService: mock_smartcontract_service
    }.get(service_type, Mock())
    
    mock_registry = Mock()
    mock_registry.get_container.return_value = mock_container
    mock_registry._initialized = True
    
    with patch('database.get_db_manager', return_value=mock_db), \
         patch('database.connection.get_db_manager', return_value=mock_db), \
         patch('services.base_service.get_db_manager', return_value=mock_db), \
         patch('core.modern_service_container.get_service_registry', return_value=mock_registry), \
         patch('core.modern_service_container.get_container', return_value=mock_container), \
         patch('core.modern_service_container.get_user_service', return_value=mock_user_service), \
         patch('core.modern_service_container.get_product_service', return_value=mock_product_service), \
         patch('core.modern_service_container.get_sales_service', return_value=mock_sales_service), \
         patch('core.modern_service_container.get_smartcontract_service', return_value=mock_smartcontract_service), \
         patch('core.modern_service_container.get_database_manager', return_value=mock_db):
        yield {
            'db': mock_db,
            'container': mock_container,
            'registry': mock_registry,
            'user_service': mock_user_service,
            'product_service': mock_product_service,
            'sales_service': mock_sales_service,
            'smartcontract_service': mock_smartcontract_service
        }


@pytest.fixture
def product_handler():
    """Create a real product handler for testing"""
    from handlers.product_handler import ModernProductHandler
    return ModernProductHandler()


@pytest.fixture
def mock_user_handler(comprehensive_handler_mocks):
    """Create a mock user handler with service dependencies"""
    handler = Mock()
    handler.start = AsyncMock(return_value=1)
    handler.menu_callback = AsyncMock(return_value=2)
    handler.add_username = AsyncMock(return_value=3)
    handler.add_password = AsyncMock(return_value=ConversationHandler.END)
    return handler

@pytest.fixture  
def user_handler(comprehensive_handler_mocks):
    """Create a real user handler for testing"""
    from handlers.user_handler import ModernUserHandler
    return ModernUserHandler()


@pytest.fixture
def user_request(mock_telegram_objects):
    """Create a user handler request"""
    from handlers.base_handler import HandlerRequest
    return HandlerRequest(
        update=mock_telegram_objects.update,
        context=mock_telegram_objects.context,
        user_data=mock_telegram_objects.context.user_data,
        chat_id=mock_telegram_objects.chat.id,
        user_id=mock_telegram_objects.user.id
    )


@pytest.fixture
def comprehensive_handler_mocks(mock_user_service, mock_product_service, mock_sales_service, mock_smartcontract_service):
    """
    Comprehensive fixture that provides properly mocked handlers with service integration.
    This replaces the old approach of mocking handler methods directly.
    """
    # Mock all service accessor functions - handlers call these with context parameter
    with patch('handlers.user_handler.get_user_service', return_value=mock_user_service), \
         patch('handlers.product_handler.get_product_service', return_value=mock_product_service), \
         patch('handlers.buy_handler.get_user_service', return_value=mock_user_service), \
         patch('handlers.buy_handler.get_product_service', return_value=mock_product_service), \
         patch('handlers.estoque_handler.get_product_service', return_value=mock_product_service), \
         patch('handlers.lista_produtos_handler.get_product_service', return_value=mock_product_service), \
         patch('handlers.base_handler.get_user_service', return_value=mock_user_service), \
         patch('core.modern_service_container.get_user_service', return_value=mock_user_service), \
         patch('core.modern_service_container.get_product_service', return_value=mock_product_service), \
         patch('core.modern_service_container.get_sales_service', return_value=mock_sales_service), \
         patch('core.modern_service_container.get_smartcontract_service', return_value=mock_smartcontract_service), \
         patch('services.handler_business_service.HandlerBusinessService') as mock_business_service_class:
        
        # Create comprehensive mock business service
        mock_business_service = Mock()
        
        # Product management responses
        mock_business_service.handle_product_creation = Mock(return_value=Mock(
            success=True,
            message="Produto criado com sucesso!",
            product_id=1
        ))
        
        # User management responses  
        mock_user_response = Mock()
        mock_user_response.success = True
        mock_user_response.message = "Usuário criado com sucesso!"
        mock_user_response.user_id = 1
        mock_business_service.manage_user = Mock(return_value=mock_user_response)
        mock_business_service.handle_user_management = Mock(return_value=mock_user_response)  # Keep for backward compatibility
        
        # Purchase responses
        mock_business_service.handle_purchase = Mock(return_value=Mock(
            success=True,
            message="Compra realizada com sucesso!",
            sale_id=1
        ))
        
        mock_business_service_class.return_value = mock_business_service
        
        yield {
            'user_service': mock_user_service,
            'product_service': mock_product_service,
            'sales_service': mock_sales_service,
            'smartcontract_service': mock_smartcontract_service,
            'business_service': mock_business_service
        }