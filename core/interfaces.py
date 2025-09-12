"""
Service interfaces and abstractions for dependency injection.
Defines contracts that services must implement.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from models.user import User, UserLevel, CreateUserRequest, UpdateUserRequest
from models.product import Product, ProductWithStock, CreateProductRequest, UpdateProductRequest, AddStockRequest, StockItem
from models.sale import Sale, SaleItem, CreateSaleRequest, CreatePaymentRequest, Payment, SaleWithPayments


class IUserService(ABC):
    """Interface for user management services."""
    
    @abstractmethod
    def authenticate_user(self, username: str, password: str, chat_id: int) -> Optional[User]:
        """Authenticate user and update their chat_id."""
        pass
    
    @abstractmethod
    def get_user_by_chat_id(self, chat_id: int) -> Optional[User]:
        """Get user by their Telegram chat ID."""
        pass
    
    @abstractmethod
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        pass
    
    @abstractmethod
    def get_user_permission_level(self, chat_id: int) -> Optional[UserLevel]:
        """Get user's permission level by chat ID."""
        pass
    
    @abstractmethod
    def create_user(self, request: CreateUserRequest) -> User:
        """Create a new user."""
        pass
    
    @abstractmethod
    def update_user(self, request: UpdateUserRequest) -> User:
        """Update an existing user."""
        pass
    
    @abstractmethod
    def delete_user(self, user_id: int) -> bool:
        """Delete a user."""
        pass
    
    @abstractmethod
    def get_all_users(self) -> List[User]:
        """Get all users."""
        pass
    
    @abstractmethod
    def username_exists(self, username: str, exclude_user_id: Optional[int] = None) -> bool:
        """Check if username already exists."""
        pass


class IProductService(ABC):
    """Interface for product management services."""
    
    @abstractmethod
    def get_product_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID."""
        pass
    
    @abstractmethod
    def get_product_by_name(self, name: str) -> Optional[Product]:
        """Get product by name."""
        pass
    
    @abstractmethod
    def get_all_products(self) -> List[Product]:
        """Get all products."""
        pass
    
    @abstractmethod
    def get_products_with_stock(self) -> List[ProductWithStock]:
        """Get all products with their current stock information."""
        pass
    
    @abstractmethod
    def create_product(self, request: CreateProductRequest) -> Product:
        """Create a new product."""
        pass
    
    @abstractmethod
    def update_product(self, request: UpdateProductRequest) -> Product:
        """Update an existing product."""
        pass
    
    @abstractmethod
    def delete_product(self, product_id: int) -> bool:
        """Delete a product."""
        pass
    
    @abstractmethod
    def add_stock(self, request: AddStockRequest) -> StockItem:
        """Add stock for a product."""
        pass
    
    @abstractmethod
    def get_available_quantity(self, product_id: int) -> int:
        """Get total available quantity for a product."""
        pass
    
    @abstractmethod
    def consume_stock(self, product_id: int, quantity: int) -> List[StockItem]:
        """Consume stock using FIFO method."""
        pass


class ISalesService(ABC):
    """Interface for sales management services."""
    
    @abstractmethod
    def create_sale(self, request: CreateSaleRequest) -> Sale:
        """Create a new sale with items."""
        pass
    
    @abstractmethod
    def get_sale_by_id(self, sale_id: int) -> Optional[Sale]:
        """Get sale by ID."""
        pass
    
    @abstractmethod
    def get_all_sales(self) -> List[Sale]:
        """Get all sales."""
        pass
    
    @abstractmethod
    def get_sales_by_buyer(self, buyer_name: str) -> List[Sale]:
        """Get all sales for a specific buyer."""
        pass
    
    @abstractmethod
    def get_unpaid_sales(self, buyer_name: Optional[str] = None) -> List[SaleWithPayments]:
        """Get sales that haven't been fully paid."""
        pass
    
    @abstractmethod
    def add_payment(self, request: CreatePaymentRequest) -> Payment:
        """Add a payment to a sale."""
        pass
    
    @abstractmethod
    def get_sale_with_payments(self, sale_id: int) -> Optional[SaleWithPayments]:
        """Get sale with all payment information."""
        pass


class ISmartContractService(ABC):
    """Interface for smart contract management services."""
    
    @abstractmethod
    def create_smart_contract(self, chat_id: int, codigo: str) -> int:
        """Create a new smart contract."""
        pass
    
    @abstractmethod
    def get_smart_contract_by_code(self, chat_id: int, codigo: str) -> Optional[Tuple[int, int, str, datetime]]:
        """Get smart contract by code and chat_id."""
        pass
    
    @abstractmethod
    def add_transaction(self, contrato_id: int, descricao: str) -> int:
        """Add a new transaction to a smart contract."""
        pass
    
    @abstractmethod
    def list_contract_transactions(self, contrato_id: int) -> List[Tuple[int, str]]:
        """List all transactions for a smart contract."""
        pass
    
    @abstractmethod
    def confirm_transaction(self, transaction_id: int) -> bool:
        """Confirm a transaction."""
        pass
    
    @abstractmethod
    def delete_smart_contract(self, contract_id: int) -> bool:
        """Delete a smart contract and all its transactions."""
        pass
    
    @abstractmethod
    def get_transaction_details(self, transaction_id: int) -> Optional[Tuple[int, int, str, bool, datetime]]:
        """Get details of a specific transaction."""
        pass


class IDatabaseManager(ABC):
    """Interface for database management."""
    
    @abstractmethod
    def get_connection(self):
        """Get database connection."""
        pass
    
    @abstractmethod
    def health_check(self) -> bool:
        """Perform database health check."""
        pass
    
    @abstractmethod
    def close(self):
        """Close database connections."""
        pass


class IContext(ABC):
    """Interface for application context."""
    
    @abstractmethod
    def get_database_url(self) -> str:
        """Get database connection URL."""
        pass
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        pass


class IServiceContainer(ABC):
    """Interface for service container."""
    
    @abstractmethod
    def register_service(self, interface_type: type, implementation: Any, singleton: bool = True):
        """Register a service implementation."""
        pass
    
    @abstractmethod
    def get_service(self, interface_type: type):
        """Get service instance by interface type."""
        pass
    
    @abstractmethod
    def configure_services(self, config: Dict[str, Any]):
        """Configure services with settings."""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all services."""
        pass