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
from models.cash_balance import CashBalance, CashTransaction, CreateCashTransactionRequest, RevenueReport, CashBalanceHistory
from models.expedition import (
    Expedition, ExpeditionItem, PirateName, ItemConsumption, ExpeditionStatus, PaymentStatus,
    ExpeditionCreateRequest, ExpeditionItemRequest, ItemConsumptionRequest,
    ExpeditionResponse, ItemConsumptionResponse
)
from decimal import Decimal


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

    # === EXPEDITION INTEGRATION METHODS ===

    @abstractmethod
    def map_pirate_to_buyer(self, expedition_id: int, pirate_name: str, buyer_username: str,
                           owner_key: str) -> bool:
        """Create a mapping between a pirate name and a real buyer username."""
        pass

    @abstractmethod
    def get_buyer_for_pirate(self, expedition_id: int, pirate_name: str) -> Optional[str]:
        """Get the real buyer username for a pirate name (owner access only)."""
        pass

    @abstractmethod
    def get_pirate_for_buyer(self, expedition_id: int, buyer_username: str) -> Optional[str]:
        """Get the pirate name for a real buyer username."""
        pass

    @abstractmethod
    def sync_expedition_debt_to_main_system(self, expedition_id: int) -> Dict[str, any]:
        """Synchronize expedition debts with the main debt tracking system."""
        pass

    @abstractmethod
    def create_integrated_sale_record(self, expedition_id: int, pirate_name: str,
                                    product_name: str, quantity: int, total_price: Decimal,
                                    product_emoji: str = "") -> bool:
        """Create a sale record in the main system for an expedition consumption."""
        pass

    @abstractmethod
    def record_expedition_payment(self, expedition_id: int, pirate_name: str,
                                 payment_amount: Decimal, payment_method: str = "expedition",
                                 payment_notes: Optional[str] = None) -> bool:
        """Record a payment in the expedition payments system."""
        pass

    @abstractmethod
    def get_expedition_financial_summary(self, expedition_id: int) -> Dict[str, any]:
        """Get financial summary for an expedition including debt and payment totals."""
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


class ICashBalanceService(ABC):
    """Interface for cash balance and revenue management services."""

    @abstractmethod
    def get_current_balance(self) -> CashBalance:
        """Get the current cash balance."""
        pass

    @abstractmethod
    def add_revenue_from_payment(self, pagamento_id: int, valor: Decimal, venda_id: Optional[int] = None) -> CashTransaction:
        """Add revenue from a payment to cash balance."""
        pass

    @abstractmethod
    def add_expense(self, valor: Decimal, descricao: str, usuario_chat_id: Optional[int] = None) -> CashTransaction:
        """Add an expense (reduces cash balance)."""
        pass

    @abstractmethod
    def adjust_balance(self, valor: Decimal, descricao: str, usuario_chat_id: Optional[int] = None) -> CashTransaction:
        """Make a manual balance adjustment."""
        pass

    @abstractmethod
    def get_transactions_history(self, limit: int = 50, offset: int = 0) -> List[CashTransaction]:
        """Get transaction history."""
        pass

    @abstractmethod
    def get_revenue_report(self, days: int = 30) -> RevenueReport:
        """Generate revenue report for the specified number of days."""
        pass

    @abstractmethod
    def get_balance_history(self, days: int = 30) -> CashBalanceHistory:
        """Get balance history for a period."""
        pass


class IBroadcastService(ABC):
    """Interface for broadcast messaging services."""
    
    @abstractmethod
    def create_text_broadcast(self, sender_chat_id: int, content: str, message_type: str) -> int:
        """Create a text broadcast message (text, html, markdown)."""
        pass
    
    @abstractmethod
    def create_poll_broadcast(self, sender_chat_id: int, question: str, options: List[str]) -> int:
        """Create a poll broadcast message."""
        pass
    
    @abstractmethod
    def create_dice_broadcast(self, sender_chat_id: int, emoji: str) -> int:
        """Create a dice broadcast message."""
        pass
    
    @abstractmethod
    def send_broadcast(self, broadcast_id: int) -> Dict[str, Any]:
        """Send broadcast message to all users."""
        pass
    
    @abstractmethod
    def get_broadcast_status(self, broadcast_id: int) -> Optional[Dict[str, Any]]:
        """Get broadcast status and statistics."""
        pass
    
    @abstractmethod
    def get_all_broadcasts(self, sender_chat_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all broadcast messages, optionally filtered by sender."""
        pass
    
    @abstractmethod
    def delete_broadcast(self, broadcast_id: int) -> bool:
        """Delete a broadcast message."""
        pass


class IExpeditionService(ABC):
    """Interface for expedition management services."""

    @abstractmethod
    def create_expedition(self, request: ExpeditionCreateRequest) -> Expedition:
        """Create a new expedition."""
        pass

    @abstractmethod
    def get_expedition_by_id(self, expedition_id: int) -> Optional[Expedition]:
        """Get expedition by ID."""
        pass

    @abstractmethod
    def get_expeditions_by_owner(self, owner_chat_id: int) -> List[Expedition]:
        """Get all expeditions for a specific owner."""
        pass

    @abstractmethod
    def get_all_expeditions(self) -> List[Expedition]:
        """Get all expeditions."""
        pass

    @abstractmethod
    def get_active_expeditions(self) -> List[Expedition]:
        """Get all active expeditions."""
        pass

    @abstractmethod
    def get_overdue_expeditions(self) -> List[Expedition]:
        """Get expeditions that are past their deadline."""
        pass

    @abstractmethod
    def update_expedition_status(self, expedition_id: int, status: ExpeditionStatus) -> bool:
        """Update expedition status."""
        pass

    @abstractmethod
    def add_items_to_expedition(self, expedition_id: int, items: List[ExpeditionItemRequest]) -> List[ExpeditionItem]:
        """Add items to an expedition with inventory validation."""
        pass

    @abstractmethod
    def get_expedition_items(self, expedition_id: int) -> List[ExpeditionItem]:
        """Get all items for an expedition."""
        pass

    @abstractmethod
    def consume_item(self, request: ItemConsumptionRequest) -> ItemConsumption:
        """Record item consumption for an expedition."""
        pass

    @abstractmethod
    def get_expedition_consumptions(self, expedition_id: int) -> List[ItemConsumption]:
        """Get all item consumptions for an expedition."""
        pass

    @abstractmethod
    def get_user_consumptions(self, consumer_name: str) -> List[ItemConsumption]:
        """Get all consumptions for a specific user."""
        pass

    @abstractmethod
    def get_expedition_response(self, expedition_id: int) -> Optional[ExpeditionResponse]:
        """Get complete expedition data with progress statistics."""
        pass

    @abstractmethod
    def check_expedition_completion(self, expedition_id: int) -> bool:
        """Check if expedition is complete and update status if necessary."""
        pass

    @abstractmethod
    def delete_expedition(self, expedition_id: int) -> bool:
        """Delete an expedition and all related data."""
        pass

    @abstractmethod
    def update_payment_status(self, consumption_id: int, status: PaymentStatus) -> bool:
        """Update payment status for an item consumption."""
        pass

    @abstractmethod
    def get_unpaid_consumptions(self, consumer_name: Optional[str] = None) -> List[ItemConsumptionResponse]:
        """Get unpaid item consumptions, optionally filtered by consumer."""
        pass


class IBramblerService(ABC):
    """Interface for pirate name anonymization services."""

    @abstractmethod
    def generate_pirate_names(self, expedition_id: int, original_names: List[str]) -> List[PirateName]:
        """Generate and store pirate names for expedition anonymization."""
        pass

    @abstractmethod
    def get_pirate_name(self, expedition_id: int, original_name: str) -> Optional[str]:
        """Get pirate name for an original name in an expedition."""
        pass

    @abstractmethod
    def get_original_name(self, expedition_id: int, pirate_name: str) -> Optional[str]:
        """Get original name from pirate name (owner access only)."""
        pass

    @abstractmethod
    def encrypt_name_mapping(self, expedition_id: int, original_name: str, pirate_name: str, owner_key: str) -> str:
        """Create encrypted mapping between original and pirate names."""
        pass

    @abstractmethod
    def decrypt_name_mapping(self, expedition_id: int, encrypted_mapping: str, owner_key: str) -> Optional[Dict[str, str]]:
        """Decrypt name mapping for owner access."""
        pass

    @abstractmethod
    def get_expedition_pirate_names(self, expedition_id: int) -> List[PirateName]:
        """Get all pirate names for an expedition."""
        pass

    @abstractmethod
    def delete_expedition_names(self, expedition_id: int) -> bool:
        """Delete all pirate names for an expedition."""
        pass

    @abstractmethod
    def generate_unique_pirate_name(self) -> str:
        """Generate a unique pirate name."""
        pass

    @abstractmethod
    def encrypt_product_name(self, product_name: str, expedition_id: int, owner_key: str) -> str:
        """Encrypt product name for expedition item anonymization."""
        pass

    @abstractmethod
    def decrypt_product_name(self, encrypted_product: str, owner_key: str) -> Optional[str]:
        """Decrypt product name for owner access."""
        pass

    @abstractmethod
    def generate_anonymized_item_code(self, product_name: str, expedition_id: int) -> str:
        """Generate anonymized item code for product tracking."""
        pass

    @abstractmethod
    def encrypt_item_notes(self, notes: str, expedition_id: int, owner_key: str) -> str:
        """Encrypt item notes for expedition privacy."""
        pass

    @abstractmethod
    def decrypt_item_notes(self, encrypted_notes: str, owner_key: str) -> Optional[str]:
        """Decrypt item notes for owner access."""
        pass

    @abstractmethod
    def validate_encryption_key(self, owner_key: str, expedition_id: int) -> bool:
        """Validate that an owner key is valid for encryption operations."""
        pass


class IWebSocketService(ABC):
    """Interface for WebSocket real-time updates and notifications."""

    @abstractmethod
    def broadcast_expedition_progress(self, expedition_id: int, progress_data: Dict[str, Any]) -> bool:
        """Broadcast expedition progress updates to connected clients."""
        pass

    @abstractmethod
    def send_deadline_alert(self, expedition_id: int, alert_type: str, alert_data: Dict[str, Any]) -> bool:
        """Send deadline alert notifications."""
        pass

    @abstractmethod
    def notify_expedition_completion(self, expedition_id: int, completion_data: Dict[str, Any]) -> bool:
        """Notify about expedition completion."""
        pass

    @abstractmethod
    def subscribe_to_expedition(self, user_id: int, expedition_id: int) -> bool:
        """Subscribe user to expedition updates."""
        pass

    @abstractmethod
    def unsubscribe_from_expedition(self, user_id: int, expedition_id: int) -> bool:
        """Unsubscribe user from expedition updates."""
        pass

    @abstractmethod
    def get_active_subscribers(self, expedition_id: int) -> List[int]:
        """Get list of active subscribers for an expedition."""
        pass

    @abstractmethod
    def broadcast_system_alert(self, alert_data: Dict[str, Any]) -> bool:
        """Broadcast system-wide alerts."""
        pass


class IExportService(ABC):
    """Interface for export and reporting services."""

    @abstractmethod
    def export_expedition_data(self, expedition_id: Optional[int] = None,
                             status_filter: Optional[str] = None,
                             date_from: Optional[datetime] = None,
                             date_to: Optional[datetime] = None) -> str:
        """Export expedition data to CSV format."""
        pass

    @abstractmethod
    def export_pirate_activity_report(self, expedition_id: Optional[int] = None,
                                    anonymized: bool = True,
                                    date_from: Optional[datetime] = None,
                                    date_to: Optional[datetime] = None) -> str:
        """Export pirate activity report (anonymized by default)."""
        pass

    @abstractmethod
    def export_profit_loss_report(self, expedition_id: Optional[int] = None,
                                date_from: Optional[datetime] = None,
                                date_to: Optional[datetime] = None) -> str:
        """Export profit/loss report for expeditions."""
        pass

    @abstractmethod
    def search_expeditions(self, search_query: Optional[str] = None,
                          status_filter: Optional[str] = None,
                          owner_chat_id: Optional[int] = None,
                          date_from: Optional[datetime] = None,
                          date_to: Optional[datetime] = None,
                          sort_by: str = "created_at",
                          sort_order: str = "DESC",
                          limit: int = 100,
                          offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """Search expeditions with advanced filtering and sorting."""
        pass

    @abstractmethod
    def cleanup_export_files(self, older_than_hours: int = 24) -> int:
        """Clean up old export files from temp directory."""
        pass

    @abstractmethod
    def generate_expedition_summary_report(self, expedition_ids: List[int]) -> str:
        """Generate a comprehensive summary report for multiple expeditions."""
        pass


class IAssignmentService(ABC):
    """Interface for expedition assignment and consumption management services."""

    @abstractmethod
    def create_assignment(self, expedition_id: int, pirate_name: str, item_id: int,
                         quantity: int, unit_price: Decimal, assignment_type: str = 'consumption',
                         due_date: Optional[datetime] = None, notes: Optional[str] = None):
        """Create a new assignment for expedition consumption."""
        pass

    @abstractmethod
    def record_consumption(self, assignment_id: int, consumed_quantity: int,
                          actual_price: Optional[Decimal] = None, consumption_notes: Optional[str] = None):
        """Record consumption for an assignment."""
        pass

    @abstractmethod
    def get_assignment_by_id(self, assignment_id: int):
        """Get assignment by ID."""
        pass

    @abstractmethod
    def get_expedition_assignments(self, expedition_id: int, status_filter: Optional[str] = None):
        """Get all assignments for an expedition."""
        pass

    @abstractmethod
    def get_pirate_assignments(self, expedition_id: int, pirate_name: str, status_filter: Optional[str] = None):
        """Get assignments for a specific pirate in an expedition."""
        pass

    @abstractmethod
    def calculate_pirate_debt(self, expedition_id: int, pirate_name: str) -> Dict[str, Decimal]:
        """Calculate total debt for a pirate in an expedition."""
        pass

    @abstractmethod
    def get_overdue_assignments(self, expedition_id: Optional[int] = None):
        """Get assignments that are overdue."""
        pass

    @abstractmethod
    def cancel_assignment(self, assignment_id: int, cancellation_reason: Optional[str] = None) -> bool:
        """Cancel an assignment."""
        pass

