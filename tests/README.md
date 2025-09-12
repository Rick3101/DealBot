# Telegram Bot Handler Tests

This directory contains comprehensive tests for all Telegram bot handlers using pytest and modern testing practices.

## 📁 Test Structure

```
tests/
├── __init__.py                     # Test package initialization
├── conftest.py                     # Pytest configuration and fixtures
├── test_config.py                  # Test environment configuration
├── run_tests.py                    # Test runner script
├── README.md                       # This documentation
└── test_handlers/                  # Handler-specific tests
    ├── __init__.py
    ├── test_login_handler.py        # Login authentication tests
    ├── test_product_handler.py      # Product CRUD tests
    ├── test_buy_handler.py          # Purchase flow tests
    ├── test_user_handler.py         # User management tests
    ├── test_estoque_handler.py      # Inventory management tests
    ├── test_start_handler.py        # Bot initialization tests
    └── test_commands_handler.py     # Command listing tests
```

## 🧪 Test Categories

### Unit Tests
- **Handler Logic**: Test individual handler methods and conversation flows
- **Validation**: Test input validation and sanitization
- **Error Handling**: Test error boundaries and exception handling
- **Permission Checks**: Test access control and authorization

### Integration Tests
- **Service Integration**: Test handlers with actual service interactions
- **Database Operations**: Test with real database connections
- **End-to-End Flows**: Test complete conversation workflows

## 🚀 Running Tests

### Quick Start

```bash
# Run all tests
python tests/run_tests.py

# Run interactive test selection
python tests/run_tests.py
```

### Command Line Options

```bash
# Run specific test type
python tests/run_tests.py --type unit
python tests/run_tests.py --type integration
python tests/run_tests.py --type all

# Run specific handler tests
python tests/run_tests.py --handler login
python tests/run_tests.py --handler product
python tests/run_tests.py --handler buy

# Run with coverage
python tests/run_tests.py --coverage

# Verbose output
python tests/run_tests.py --verbose

# Install dependencies first
python tests/run_tests.py --install-deps
```

### Direct Pytest Commands

```bash
# Install dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/

# Run specific handler
pytest tests/test_handlers/test_login_handler.py

# Run with coverage
pytest tests/ --cov=handlers --cov=services --cov=core --cov-report=html

# Run only unit tests
pytest tests/ -m unit

# Run only integration tests
pytest tests/ -m integration
```

## 📋 Test Fixtures and Utilities

### Available Fixtures

- **mock_telegram_objects**: Complete set of mocked Telegram objects
- **mock_user_service**: Mocked user service with authentication
- **mock_product_service**: Mocked product service with CRUD operations
- **mock_sales_service**: Mocked sales service with transaction handling
- **mock_service_container**: Complete service container mock
- **test_data_factory**: Factory for creating test data
- **test_environment**: Test environment setup

### Utility Functions

- **assert_handler_response()**: Validate handler response structure
- **assert_telegram_call_made()**: Verify Telegram API calls
- **TestUtils.simulate_conversation_flow()**: Test complete conversation flows
- **TestUtils.create_callback_query_update()**: Create callback query updates

## 🎯 Test Patterns

### Handler Test Structure

```python
class TestHandlerName:
    """Test cases for handler functionality"""
    
    @pytest.fixture
    def mock_handler(self):
        """Create mock handler"""
        
    async def test_command_start(self):
        """Test command initiation"""
        
    async def test_valid_input(self):
        """Test valid input handling"""
        
    async def test_invalid_input(self):
        """Test invalid input handling"""
        
    async def test_error_handling(self):
        """Test error scenarios"""
        
    async def test_permission_validation(self):
        """Test permission checks"""
        
    @pytest.mark.parametrize("input,expected", [...])
    async def test_input_validation(self, input, expected):
        """Test various input combinations"""
        
    async def test_complete_flow(self):
        """Test end-to-end workflow"""
```

### Conversation Flow Testing

```python
async def test_complete_conversation_flow(self, handler, test_utils):
    """Test complete conversation from start to finish"""
    
    # Setup conversation steps
    updates_contexts = [
        (update1, context1),  # Start
        (update2, context2),  # Step 1
        (update3, context3),  # Step 2
    ]
    
    expected_states = [1, 2, ConversationHandler.END]
    
    # Execute flow
    results = await test_utils.simulate_conversation_flow(
        handler,
        updates_contexts,
        expected_states
    )
    
    # Verify results
    assert results[-1] == ConversationHandler.END
```

## 📊 Test Coverage

The test suite aims for comprehensive coverage of:

- ✅ **Handler Entry Points**: All command handlers and callbacks
- ✅ **Conversation States**: All conversation flow states
- ✅ **Input Validation**: Valid and invalid input scenarios
- ✅ **Error Handling**: Service errors, validation errors, exceptions
- ✅ **Permission Checks**: Access control for different user levels
- ✅ **Business Logic**: Core functionality and edge cases
- ✅ **Integration Points**: Service interactions and dependencies

### Coverage Reports

After running tests with coverage:

```bash
# View HTML coverage report
open htmlcov/index.html

# View terminal coverage summary
pytest tests/ --cov=handlers --cov-report=term-missing
```

## 🔧 Mock Configuration

### Service Mocks

All service dependencies are mocked to provide:
- Predictable test environments
- Fast test execution
- Isolated unit testing
- Configurable responses

### Telegram Mocks

Telegram objects are fully mocked including:
- Update objects with messages and callbacks
- Context with user data and bot references
- User and chat objects with IDs and metadata
- Async method calls for sending messages

## 🐛 Debugging Tests

### Common Issues

1. **Async Test Failures**
   ```python
   # Ensure async fixtures and tests
   @pytest.fixture
   async def async_fixture():
       # async setup
   
   async def test_async_function():
       # async test
   ```

2. **Mock Configuration**
   ```python
   # Proper mock setup
   mock_service.method.return_value = expected_value
   mock_service.method.side_effect = Exception("error")
   ```

3. **Service Initialization**
   ```python
   # Mock service container properly
   with patch('handlers.handler.get_service', return_value=mock_service):
       # test code
   ```

### Debug Mode

```bash
# Run with debug output
pytest tests/ -v -s --tb=long

# Run single test with debug
pytest tests/test_handlers/test_login_handler.py::TestLoginHandler::test_login_start -v -s
```

## 📝 Adding New Tests

### 1. Create Test File

```python
# tests/test_handlers/test_new_handler.py
import pytest
from unittest.mock import Mock, AsyncMock, patch
from telegram.ext import ConversationHandler

class TestNewHandler:
    @pytest.fixture
    def mock_new_handler(self):
        # Setup mock handler
        
    async def test_basic_functionality(self):
        # Test implementation
```

### 2. Add to Test Runner

Update `run_tests.py` to include the new handler in scenarios.

### 3. Update Documentation

Add the new test file to this README and any relevant documentation.

## 🚦 Continuous Integration

For CI/CD integration:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    pip install pytest pytest-asyncio pytest-cov
    pytest tests/ --cov=handlers --cov=services --cov=core --cov-report=xml
    
- name: Upload Coverage
  uses: codecov/codecov-action@v1
  with:
    file: ./coverage.xml
```

## 🎯 Best Practices

1. **Test Isolation**: Each test should be independent
2. **Clear Naming**: Test names should describe what they test
3. **Comprehensive Coverage**: Test happy path, edge cases, and errors
4. **Fast Execution**: Use mocks to keep tests fast
5. **Maintainable**: Keep tests simple and focused
6. **Documentation**: Comment complex test logic

## 📚 Additional Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio Plugin](https://github.com/pytest-dev/pytest-asyncio)
- [unittest.mock Guide](https://docs.python.org/3/library/unittest.mock.html)
- [Telegram Bot Testing Patterns](https://python-telegram-bot.readthedocs.io/en/stable/)