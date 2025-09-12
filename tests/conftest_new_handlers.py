"""
Additional fixtures for the new mock handler system.
Import this in tests that want to use the new mock handlers.
"""

import pytest
from tests.mocks import MockHandlerFactory, MockServiceContainer
from tests.mocks.mock_handlers import MockHandlerBuilder, HandlerScenarios


@pytest.fixture
def mock_handler_factory():
    """Provide the mock handler factory for creating real handlers with mocked services."""
    return MockHandlerFactory()


@pytest.fixture
def mock_services():
    """Provide a configured mock service container."""
    from tests.mocks.mock_services import create_mock_services
    return create_mock_services()


@pytest.fixture
def handler_builder():
    """Provide a handler builder for creating complex test scenarios."""
    return MockHandlerBuilder()


@pytest.fixture
def handler_scenarios():
    """Provide access to predefined handler scenarios."""
    return HandlerScenarios


# Specific handler fixtures using the new system
@pytest.fixture
def login_handler_with_mocks(mock_handler_factory, mock_services):
    """Create a login handler with mocked services."""
    with mock_handler_factory.create_login_handler(mock_services) as (handler, services):
        yield handler, services


@pytest.fixture
def buy_handler_with_mocks(mock_handler_factory, mock_services):
    """Create a buy handler with mocked services."""
    with mock_handler_factory.create_buy_handler(mock_services) as (handler, services):
        yield handler, services


@pytest.fixture
def product_handler_with_mocks(mock_handler_factory, mock_services):
    """Create a product handler with mocked services."""
    with mock_handler_factory.create_product_handler(mock_services) as (handler, services):
        yield handler, services


@pytest.fixture
def user_handler_with_mocks(mock_handler_factory, mock_services):
    """Create a user handler with mocked services."""
    with mock_handler_factory.create_user_handler(mock_services) as (handler, services):
        yield handler, services