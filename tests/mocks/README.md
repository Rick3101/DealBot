# Mock Handler System

This folder contains a comprehensive mock system for testing Telegram bot handlers with real handler instances and mocked service dependencies.

## Overview

Instead of mocking the handlers themselves, this system creates **real handler instances** with **mocked service dependencies**. This provides more accurate testing that closely matches production behavior.

## Components

### 1. `mock_services.py`
Contains mock implementations of all service dependencies:
- `MockUserService` - User authentication and management
- `MockProductService` - Product CRUD operations  
- `MockSalesService` - Sales and payment processing
- `MockHandlerBusinessService` - High-level business logic
- `MockServiceContainer` - Container for organizing all services

### 2. `mock_handler_factory.py`
Factory for creating real handler instances with mocked services:
- `MockHandlerFactory` - Main factory class
- Context managers for each handler type
- Automatic service dependency injection

### 3. `mock_handlers.py`
Pre-configured scenarios and builders:
- `HandlerScenarios` - Common test scenarios (success, failure, permissions, etc.)  
- `MockHandlerBuilder` - Builder pattern for custom configurations
- Convenience functions for quick handler creation

### 4. `conftest_new_handlers.py`
pytest fixtures for easy test integration:
- Handler-specific fixtures
- Service container fixtures
- Builder and scenario fixtures

## Usage Examples

### Basic Handler Creation

```python
def test_login_handler(login_handler_with_mocks, mock_telegram_objects):
    handler, services = login_handler_with_mocks
    
    result = await handler.start_login(
        mock_telegram_objects.update,
        mock_telegram_objects.context
    )
    
    assert result == LOGIN_USERNAME
```

### Using Builder Pattern

```python
def test_admin_purchase(handler_builder, mock_telegram_objects):
    with handler_builder.with_user("admin", "admin").with_products([...]).build_buy_handler() as (handler, services):
        result = await handler.start_buy(
            mock_telegram_objects.update,
            mock_telegram_objects.context
        )
        assert result == BUY_SELECT_PRODUCT
```

### Using Predefined Scenarios

```python
def test_failed_login(handler_scenarios, mock_handler_factory, mock_telegram_objects):
    mock_services = handler_scenarios.login.failed_authentication()
    
    with mock_handler_factory.create_login_handler(mock_services) as (handler, services):
        # Test failed authentication scenario
        pass
```

### Custom Service Configuration

```python
def test_custom_scenario(mock_handler_factory, mock_telegram_objects):
    from tests.mocks.mock_services import create_mock_services
    
    mock_services = create_mock_services()
    mock_services.configure_user(username="custom", level="owner")
    mock_services.configure_authentication(success=False)
    
    with mock_handler_factory.create_login_handler(mock_services) as (handler, services):
        # Test with custom configuration
        pass
```

## Available Scenarios

### Login Handler
- `login_success` - Successful authentication flow
- `login_failed` - Failed authentication

### Buy Handler  
- `buy_admin` - Admin user making purchase
- `buy_owner` - Owner user making purchase
- `buy_no_stock` - Insufficient stock scenario

### Product Handler
- `product_owner` - Owner creating products
- `product_no_perm` - Insufficient permissions

### User Handler
- `user_owner` - Owner managing users

## Benefits

1. **Real Handler Logic** - Tests actual handler implementation, not mocks
2. **Isolated Dependencies** - Services are mocked, handlers are real
3. **Easy Configuration** - Builder pattern and scenarios for common cases
4. **Maintainable** - Centralized mock definitions
5. **Flexible** - Can create custom scenarios easily
6. **Type Safe** - Full type hints and proper interfaces

## Migration from Old System

Replace hardcoded fixtures:

```python
# OLD
@pytest.fixture
def mock_login_handler():
    handler = Mock()
    handler.start = AsyncMock(return_value=1)
    return handler

# NEW  
def test_login(login_handler_with_mocks, mock_telegram_objects):
    handler, services = login_handler_with_mocks
    # Use real handler with mocked services
```

This system provides much more accurate testing while maintaining the isolation benefits of mocking.