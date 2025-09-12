from dataclasses import dataclass
from typing import Optional, Any, Dict, List
from datetime import datetime


@dataclass
class LoginRequest:
    username: str
    password: str
    chat_id: int


@dataclass
class LoginResponse:
    success: bool
    user_id: Optional[int] = None
    username: Optional[str] = None
    level: Optional[str] = None
    message: str = ""


@dataclass
class ProductSelectionRequest:
    product_id: int
    quantity: int
    buyer_name: Optional[str] = None
    custom_price: Optional[float] = None


@dataclass
class PurchaseRequest:
    buyer_name: str
    items: List[ProductSelectionRequest]
    total_amount: float
    chat_id: int


@dataclass
class PurchaseResponse:
    success: bool
    total_amount: float
    sale_id: Optional[int] = None
    message: str = ""
    warnings: List[str] = None


@dataclass
class InventoryAddRequest:
    product_id: int
    quantity: int
    unit_price: float
    unit_cost: float


@dataclass
class InventoryResponse:
    success: bool
    product_name: str
    added_quantity: int
    new_total: int
    message: str = ""


@dataclass
class ReportRequest:
    report_type: str  # 'sales', 'debts'
    buyer_name: Optional[str] = None  # Legacy field, kept for compatibility
    comprador_filter: Optional[str] = None  # New field for buyer name filtering
    product_name_filter: Optional[str] = None  # Filter by product name
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


@dataclass
class ReportResponse:
    success: bool
    report_data: List[Dict[str, Any]]
    csv_file_path: Optional[str] = None
    summary: Dict[str, Any] = None
    message: str = ""


@dataclass
class PaymentRequest:
    sale_id: int
    amount: float
    chat_id: int


@dataclass
class PaymentResponse:
    success: bool
    remaining_debt: float
    total_paid: float
    is_fully_paid: bool
    message: str = ""


@dataclass
class UserManagementRequest:
    action: str  # 'add', 'edit', 'remove'
    username: str
    password: Optional[str] = None
    level: Optional[str] = None
    target_user_id: Optional[int] = None


@dataclass
class UserManagementResponse:
    success: bool
    username: str
    user_id: Optional[int] = None
    level: Optional[str] = None
    message: str = ""


@dataclass
class SmartContractRequest:
    action: str  # 'create', 'add_transaction', 'shakehands'
    contract_code: Optional[str] = None
    description: Optional[str] = None
    participant_chat_id: Optional[int] = None


@dataclass
class SmartContractResponse:
    success: bool
    contract_id: Optional[str] = None
    transaction_id: Optional[int] = None
    status: Optional[str] = None
    message: str = ""


@dataclass
class ValidationResult:
    is_valid: bool
    sanitized_value: Any = None
    error_message: str = ""


@dataclass
class ConversationState:
    current_state: int
    user_data: Dict[str, Any]
    protected_messages: set
    form_data: Dict[str, Any] = None
    temp_data: Dict[str, Any] = None