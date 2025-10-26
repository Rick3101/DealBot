from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from decimal import Decimal
import json


class ExpeditionStatus(Enum):
    """Expedition status levels."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    @classmethod
    def from_string(cls, status_str: str) -> 'ExpeditionStatus':
        """Convert string to ExpeditionStatus enum."""
        try:
            return cls(status_str.lower())
        except ValueError:
            return cls.ACTIVE  # Default to active status


class PaymentStatus(Enum):
    """Payment status for item consumptions."""
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"

    @classmethod
    def from_string(cls, status_str: str) -> 'PaymentStatus':
        """Convert string to PaymentStatus enum."""
        try:
            return cls(status_str.lower())
        except ValueError:
            return cls.PENDING  # Default to pending status


class AssignmentStatus(Enum):
    """Assignment status for expedition consumptions."""
    ASSIGNED = "assigned"
    PARTIALLY_CONSUMED = "partially_consumed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

    @classmethod
    def from_string(cls, status_str: str) -> 'AssignmentStatus':
        """Convert string to AssignmentStatus enum."""
        try:
            return cls(status_str.lower())
        except ValueError:
            return cls.ASSIGNED  # Default to assigned status


@dataclass
class Expedition:
    """Expedition domain model."""
    id: int
    name: str
    owner_chat_id: int
    status: ExpeditionStatus
    deadline: Optional[datetime] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    owner_key: Optional[str] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'Expedition':
        """Create Expedition from database row."""
        if not row:
            return None

        # Handle both 7-field (old) and 8-field (new with owner_key) rows
        if len(row) == 8:
            id_, name, owner_chat_id, status, deadline, created_at, completed_at, owner_key = row
        else:
            # Backward compatibility for 7-field rows
            id_, name, owner_chat_id, status, deadline, created_at, completed_at = row
            owner_key = None

        return cls(
            id=id_,
            name=name,
            owner_chat_id=owner_chat_id,
            status=ExpeditionStatus.from_string(status),
            deadline=deadline,
            created_at=created_at,
            completed_at=completed_at,
            owner_key=owner_key
        )

    def to_dict(self) -> dict:
        """Convert expedition to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'owner_chat_id': self.owner_chat_id,
            'status': self.status.value,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

    def is_active(self) -> bool:
        """Check if expedition is currently active."""
        return self.status == ExpeditionStatus.ACTIVE

    def is_overdue(self) -> bool:
        """Check if expedition is overdue."""
        if not self.deadline or not self.is_active():
            return False
        return datetime.now() > self.deadline


@dataclass
class ExpeditionItem:
    """Expedition item domain model."""
    id: int
    expedition_id: int
    produto_id: int
    quantity_required: int
    quantity_consumed: int = 0
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'ExpeditionItem':
        """Create ExpeditionItem from database row."""
        if not row:
            return None

        id_, expedition_id, produto_id, quantity_required, quantity_consumed, created_at = row
        return cls(
            id=id_,
            expedition_id=expedition_id,
            produto_id=produto_id,
            quantity_required=quantity_required,
            quantity_consumed=quantity_consumed or 0,
            created_at=created_at
        )

    def to_dict(self) -> dict:
        """Convert expedition item to dictionary."""
        return {
            'id': self.id,
            'expedition_id': self.expedition_id,
            'produto_id': self.produto_id,
            'quantity_required': self.quantity_required,
            'quantity_consumed': self.quantity_consumed,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

    def get_remaining_quantity(self) -> int:
        """Get remaining quantity needed."""
        return max(0, self.quantity_required - self.quantity_consumed)

    def is_complete(self) -> bool:
        """Check if item requirement is complete."""
        return self.quantity_consumed >= self.quantity_required

    def get_progress_percentage(self) -> float:
        """Get completion percentage."""
        if self.quantity_required == 0:
            return 100.0
        return min(100.0, (self.quantity_consumed / self.quantity_required) * 100)


@dataclass
class PirateName:
    """Pirate name domain model for anonymization."""
    id: int
    expedition_id: int
    original_name: str
    pirate_name: str
    encrypted_mapping: str
    created_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'PirateName':
        """Create PirateName from database row."""
        if not row:
            return None

        id_, expedition_id, original_name, pirate_name, encrypted_mapping, created_at = row
        return cls(
            id=id_,
            expedition_id=expedition_id,
            original_name=original_name,
            pirate_name=pirate_name,
            encrypted_mapping=encrypted_mapping,
            created_at=created_at
        )

    def to_dict(self) -> dict:
        """Convert pirate name to dictionary."""
        return {
            'id': self.id,
            'expedition_id': self.expedition_id,
            'original_name': self.original_name,
            'pirate_name': self.pirate_name,
            'encrypted_mapping': self.encrypted_mapping,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


@dataclass
class ItemConsumption:
    """Item consumption domain model."""
    id: int
    expedition_id: int
    expedition_item_id: int
    consumer_name: str
    pirate_name: str
    quantity_consumed: int
    unit_price: Decimal
    total_cost: Decimal
    amount_paid: Decimal
    payment_status: PaymentStatus
    consumed_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'ItemConsumption':
        """Create ItemConsumption from database row."""
        if not row:
            return None

        (id_, expedition_id, expedition_item_id, consumer_name, pirate_name,
         quantity_consumed, unit_price, total_cost, amount_paid, payment_status, consumed_at) = row

        return cls(
            id=id_,
            expedition_id=expedition_id,
            expedition_item_id=expedition_item_id,
            consumer_name=consumer_name,
            pirate_name=pirate_name,
            quantity_consumed=quantity_consumed,
            unit_price=Decimal(str(unit_price)),
            total_cost=Decimal(str(total_cost)),
            amount_paid=Decimal(str(amount_paid)) if amount_paid is not None else Decimal('0.00'),
            payment_status=PaymentStatus.from_string(payment_status),
            consumed_at=consumed_at
        )

    def to_dict(self) -> dict:
        """Convert item consumption to dictionary."""
        return {
            'id': self.id,
            'expedition_id': self.expedition_id,
            'expedition_item_id': self.expedition_item_id,
            'consumer_name': self.consumer_name,
            'pirate_name': self.pirate_name,
            'quantity_consumed': self.quantity_consumed,
            'unit_price': float(self.unit_price),
            'total_cost': float(self.total_cost),
            'amount_paid': float(self.amount_paid),
            'payment_status': self.payment_status.value,
            'consumed_at': self.consumed_at.isoformat() if self.consumed_at else None
        }

    def is_paid(self) -> bool:
        """Check if consumption is fully paid."""
        return self.payment_status == PaymentStatus.PAID

    def get_remaining_amount(self) -> Decimal:
        """Get remaining amount to be paid."""
        return max(Decimal('0.00'), self.total_cost - self.amount_paid)

    def is_pending(self) -> bool:
        """Check if payment is pending."""
        return self.payment_status == PaymentStatus.PENDING


# Request DTOs
@dataclass
class ExpeditionCreateRequest:
    """Request model for creating new expeditions."""
    name: str
    owner_chat_id: int
    deadline: Optional[datetime] = None

    def validate(self) -> List[str]:
        """Validate the create expedition request."""
        errors = []

        if not self.name or len(self.name.strip()) < 3:
            errors.append("Expedition name must be at least 3 characters")

        if len(self.name) > 200:
            errors.append("Expedition name must be 200 characters or less")

        if self.deadline and self.deadline <= datetime.now():
            errors.append("Deadline must be in the future")

        return errors


@dataclass
class ExpeditionItemRequest:
    """Request model for adding items to expeditions."""
    expedition_id: int
    produto_id: int
    quantity_required: int
    unit_cost: Optional[float] = None

    def validate(self) -> List[str]:
        """Validate the expedition item request."""
        errors = []

        if self.quantity_required <= 0:
            errors.append("Quantity required must be greater than 0")

        if self.quantity_required > 10000:
            errors.append("Quantity too high (maximum 10,000)")

        if self.unit_cost is not None and self.unit_cost < 0:
            errors.append("Unit cost cannot be negative")

        return errors


@dataclass
class ItemConsumptionRequest:
    """Request model for consuming expedition items."""
    expedition_item_id: int
    consumer_name: str
    pirate_name: str
    quantity_consumed: int
    unit_price: Decimal

    def validate(self) -> List[str]:
        """Validate the item consumption request."""
        errors = []

        if not self.consumer_name or len(self.consumer_name.strip()) < 2:
            errors.append("Consumer name must be at least 2 characters")

        if not self.pirate_name or len(self.pirate_name.strip()) < 2:
            errors.append("Pirate name must be at least 2 characters")

        if self.quantity_consumed <= 0:
            errors.append("Quantity consumed must be greater than 0")

        if self.unit_price < 0:
            errors.append("Unit price cannot be negative")

        return errors

    def calculate_total_cost(self) -> Decimal:
        """Calculate total cost for the consumption."""
        return self.unit_price * self.quantity_consumed


# Response DTOs
@dataclass
class ExpeditionItemWithProduct:
    """Expedition item with product details for API responses."""
    id: int
    produto_id: int
    product_name: str
    product_emoji: str
    quantity_needed: int
    unit_price: Decimal
    quantity_consumed: int
    added_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'ExpeditionItemWithProduct':
        """Create from database row with product join."""
        if not row or len(row) < 8:
            return None

        return cls(
            id=row[0],
            produto_id=row[1],
            product_name=row[2],
            product_emoji=row[3] or '',
            quantity_needed=row[4],
            unit_price=Decimal(str(row[5])) if row[5] else Decimal('0'),
            quantity_consumed=row[6] or 0,
            added_at=row[7]
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'product_id': self.produto_id,
            'product_name': self.product_name,
            'product_emoji': self.product_emoji,
            'quantity_needed': self.quantity_needed,
            'unit_price': float(self.unit_price),
            'quantity_consumed': self.quantity_consumed,
            'added_at': self.added_at.isoformat() if self.added_at else None
        }


@dataclass
class ItemConsumptionWithProduct:
    """Item consumption with product details for API responses."""
    id: int
    consumer_name: str
    pirate_name: str
    product_name: str
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    amount_paid: Decimal
    payment_status: PaymentStatus
    consumed_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'ItemConsumptionWithProduct':
        """Create from database row with product join."""
        if not row or len(row) < 10:
            return None

        return cls(
            id=row[0],
            consumer_name=row[1],
            pirate_name=row[2],
            product_name=row[3],
            quantity=row[4],
            unit_price=Decimal(str(row[5])),
            total_price=Decimal(str(row[6])),
            amount_paid=Decimal(str(row[7])) if row[7] is not None else Decimal('0.00'),
            payment_status=PaymentStatus.from_string(row[8]),
            consumed_at=row[9]
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'consumer_name': self.consumer_name,
            'pirate_name': self.pirate_name,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'total_price': float(self.total_price),
            'amount_paid': float(self.amount_paid),
            'payment_status': self.payment_status.value,
            'consumed_at': self.consumed_at.isoformat() if self.consumed_at else None
        }


@dataclass
class ExpeditionResponse:
    """Enhanced response model for expedition data with all required fields."""
    expedition: Expedition
    items: List[ExpeditionItemWithProduct]
    consumptions: List[ItemConsumptionWithProduct]
    total_items: int
    consumed_items: int
    remaining_items: int
    completion_percentage: float
    total_value: Decimal
    consumed_value: Decimal
    remaining_value: Decimal

    @classmethod
    def create(cls, expedition: Expedition, items: List[ExpeditionItemWithProduct],
               consumptions: List[ItemConsumptionWithProduct]) -> 'ExpeditionResponse':
        """Create expedition response with all calculated stats."""
        # Calculate item-level stats
        total_items = sum(item.quantity_needed for item in items)
        consumed_items = sum(item.quantity_consumed for item in items)
        remaining_items = total_items - consumed_items

        # Calculate completion percentage
        completion_percentage = 0.0
        if total_items > 0:
            completion_percentage = (consumed_items / total_items) * 100

        # Calculate financial stats
        total_value = sum(item.quantity_needed * item.unit_price for item in items)
        consumed_value = sum(c.total_price for c in consumptions)
        remaining_value = total_value - consumed_value

        return cls(
            expedition=expedition,
            items=items,
            consumptions=consumptions,
            total_items=total_items,
            consumed_items=consumed_items,
            remaining_items=remaining_items,
            completion_percentage=completion_percentage,
            total_value=total_value,
            consumed_value=consumed_value,
            remaining_value=remaining_value
        )

    def to_dict(self) -> dict:
        """Convert response to dictionary."""
        return {
            'expedition': self.expedition.to_dict(),
            'items': [item.to_dict() for item in self.items],
            'consumptions': [c.to_dict() for c in self.consumptions],
            'total_items': self.total_items,
            'consumed_items': self.consumed_items,
            'remaining_items': self.remaining_items,
            'completion_percentage': round(self.completion_percentage, 2),
            'total_value': float(self.total_value),
            'consumed_value': float(self.consumed_value),
            'remaining_value': float(self.remaining_value)
        }


@dataclass
class ItemConsumptionResponse:
    """Response model for item consumption data."""
    consumption: ItemConsumption
    expedition_name: str
    product_name: str
    remaining_debt: Decimal

    def to_dict(self) -> dict:
        """Convert consumption response to dictionary."""
        return {
            'consumption': self.consumption.to_dict(),
            'expedition_name': self.expedition_name,
            'product_name': self.product_name,
            'remaining_debt': float(self.remaining_debt)
        }


@dataclass
class Assignment:
    """Assignment domain model for expedition consumption tracking."""
    id: int
    expedition_id: int
    pirate_name: str
    item_id: int
    quantity: int
    unit_price: Decimal
    assignment_amount: Decimal
    assignment_type: str
    assignment_status: AssignmentStatus
    assigned_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    consumed_date: Optional[datetime] = None
    consumed_quantity: Optional[int] = None
    actual_price: Optional[Decimal] = None
    actual_amount: Optional[Decimal] = None
    notes: Optional[str] = None
    consumption_notes: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'Assignment':
        """Create Assignment from database row."""
        if not row:
            return None

        (id_, expedition_id, pirate_name, item_id, quantity, unit_price,
         assignment_amount, assignment_type, assignment_status, assigned_date,
         due_date, consumed_date, notes, created_at, updated_at) = row

        return cls(
            id=id_,
            expedition_id=expedition_id,
            pirate_name=pirate_name,
            item_id=item_id,
            quantity=quantity,
            unit_price=Decimal(str(unit_price)),
            assignment_amount=Decimal(str(assignment_amount)),
            assignment_type=assignment_type,
            assignment_status=AssignmentStatus.from_string(assignment_status),
            assigned_date=assigned_date,
            due_date=due_date,
            consumed_date=consumed_date,
            notes=notes,
            created_at=created_at,
            updated_at=updated_at
        )

    def to_dict(self) -> dict:
        """Convert assignment to dictionary."""
        return {
            'id': self.id,
            'expedition_id': self.expedition_id,
            'pirate_name': self.pirate_name,
            'item_id': self.item_id,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'assignment_amount': float(self.assignment_amount),
            'assignment_type': self.assignment_type,
            'assignment_status': self.assignment_status.value,
            'assigned_date': self.assigned_date.isoformat() if self.assigned_date else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'consumed_date': self.consumed_date.isoformat() if self.consumed_date else None,
            'consumed_quantity': self.consumed_quantity,
            'actual_price': float(self.actual_price) if self.actual_price else None,
            'actual_amount': float(self.actual_amount) if self.actual_amount else None,
            'notes': self.notes,
            'consumption_notes': self.consumption_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    def is_overdue(self) -> bool:
        """Check if assignment is overdue."""
        if not self.due_date or self.assignment_status in [AssignmentStatus.COMPLETED, AssignmentStatus.CANCELLED]:
            return False
        return datetime.now() > self.due_date

    def is_completed(self) -> bool:
        """Check if assignment is completed."""
        return self.assignment_status == AssignmentStatus.COMPLETED

    def remaining_quantity(self) -> int:
        """Get remaining quantity to be consumed."""
        if self.consumed_quantity:
            return max(0, self.quantity - self.consumed_quantity)
        return self.quantity

    def consumption_percentage(self) -> float:
        """Get percentage of assignment consumed."""
        if self.consumed_quantity and self.quantity > 0:
            return (self.consumed_quantity / self.quantity) * 100
        return 0.0


# Additional Models for Enhanced Expedition System

@dataclass
class ExpeditionPirate:
    """Expedition participants management."""
    id: Optional[int] = None
    expedition_id: int = 0
    pirate_name: str = ""
    original_name: str = ""
    chat_id: Optional[int] = None
    user_id: Optional[int] = None
    encrypted_identity: Optional[str] = None
    joined_at: Optional[datetime] = None
    status: str = "active"

    @classmethod
    def from_db_row(cls, row: tuple) -> 'ExpeditionPirate':
        """Create ExpeditionPirate from database row."""
        if not row:
            return None
        return cls(
            id=row[0],
            expedition_id=row[1],
            pirate_name=row[2],
            original_name=row[3],
            chat_id=row[4],
            user_id=row[5],
            encrypted_identity=row[6],
            joined_at=row[7],
            status=row[8]
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'expedition_id': self.expedition_id,
            'pirate_name': self.pirate_name,
            'original_name': self.original_name,
            'chat_id': self.chat_id,
            'user_id': self.user_id,
            'encrypted_identity': self.encrypted_identity,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'status': self.status
        }


@dataclass
class ExpeditionAssignment:
    """Consumption tracking and debt management."""
    id: Optional[int] = None
    expedition_id: int = 0
    pirate_id: int = 0
    expedition_item_id: int = 0
    assigned_quantity: int = 0
    consumed_quantity: int = 0
    unit_price: Decimal = Decimal('0.00')
    total_cost: Decimal = Decimal('0.00')
    assignment_status: str = "assigned"
    payment_status: str = "pending"
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    deadline: Optional[datetime] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'ExpeditionAssignment':
        """Create ExpeditionAssignment from database row."""
        if not row:
            return None
        return cls(
            id=row[0],
            expedition_id=row[1],
            pirate_id=row[2],
            expedition_item_id=row[3],
            assigned_quantity=row[4],
            consumed_quantity=row[5],
            unit_price=Decimal(str(row[6])),
            total_cost=Decimal(str(row[7])),
            assignment_status=row[8],
            payment_status=row[9],
            assigned_at=row[10],
            completed_at=row[11],
            deadline=row[12]
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'expedition_id': self.expedition_id,
            'pirate_id': self.pirate_id,
            'expedition_item_id': self.expedition_item_id,
            'assigned_quantity': self.assigned_quantity,
            'consumed_quantity': self.consumed_quantity,
            'unit_price': float(self.unit_price),
            'total_cost': float(self.total_cost),
            'assignment_status': self.assignment_status,
            'payment_status': self.payment_status,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'deadline': self.deadline.isoformat() if self.deadline else None
        }


@dataclass
class ExpeditionPayment:
    """Detailed payment tracking."""
    id: Optional[int] = None
    expedition_id: int = 0
    assignment_id: int = 0
    pirate_id: int = 0
    payment_amount: Decimal = Decimal('0.00')
    payment_method: Optional[str] = None
    payment_reference: Optional[str] = None
    payment_status: str = "completed"
    processed_by_chat_id: Optional[int] = None
    processed_at: Optional[datetime] = None
    notes: Optional[str] = None

    @classmethod
    def from_db_row(cls, row: tuple) -> 'ExpeditionPayment':
        """Create ExpeditionPayment from database row."""
        if not row:
            return None
        return cls(
            id=row[0],
            expedition_id=row[1],
            assignment_id=row[2],
            pirate_id=row[3],
            payment_amount=Decimal(str(row[4])),
            payment_method=row[5],
            payment_reference=row[6],
            payment_status=row[7],
            processed_by_chat_id=row[8],
            processed_at=row[9],
            notes=row[10]
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'id': self.id,
            'expedition_id': self.expedition_id,
            'assignment_id': self.assignment_id,
            'pirate_id': self.pirate_id,
            'payment_amount': float(self.payment_amount),
            'payment_method': self.payment_method,
            'payment_reference': self.payment_reference,
            'payment_status': self.payment_status,
            'processed_by_chat_id': self.processed_by_chat_id,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'notes': self.notes
        }


# Enhanced Request/Response DTOs

@dataclass
class BramblerGenerateRequest:
    """Name anonymization request."""
    expedition_id: int
    participant_names: List[str]
    encryption_key: Optional[str] = None

    def validate(self) -> List[str]:
        """Validate brambler request."""
        errors = []
        if self.expedition_id <= 0:
            errors.append("Invalid expedition ID")
        if not self.participant_names or len(self.participant_names) == 0:
            errors.append("No participant names provided")
        return errors


@dataclass
class BramblerResponse:
    """Response for name generation."""
    success: bool
    message: str
    name_mappings: Optional[Dict[str, str]] = None
    encrypted_data: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'success': self.success,
            'message': self.message,
            'name_mappings': self.name_mappings,
            'encrypted_data': self.encrypted_data
        }


@dataclass
class ExpeditionSummary:
    """Dashboard summary data."""
    expedition_id: int
    name: str
    status: str
    progress_percentage: float
    total_items: int
    completed_items: int
    total_participants: int
    total_cost: Decimal
    paid_amount: Decimal
    pending_amount: Decimal
    deadline: Optional[datetime]
    is_overdue: bool
    recent_consumptions: List[Dict[str, Any]]

    @classmethod
    def from_data(cls, data: Dict[str, Any]) -> 'ExpeditionSummary':
        """Create summary from aggregated data."""
        return cls(
            expedition_id=data.get('expedition_id', 0),
            name=data.get('name', ''),
            status=data.get('status', 'active'),
            progress_percentage=data.get('progress_percentage', 0.0),
            total_items=data.get('total_items', 0),
            completed_items=data.get('completed_items', 0),
            total_participants=data.get('total_participants', 0),
            total_cost=data.get('total_cost', Decimal('0.00')),
            paid_amount=data.get('paid_amount', Decimal('0.00')),
            pending_amount=data.get('pending_amount', Decimal('0.00')),
            deadline=data.get('deadline'),
            is_overdue=data.get('is_overdue', False),
            recent_consumptions=data.get('recent_consumptions', [])
        )

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'expedition_id': self.expedition_id,
            'name': self.name,
            'status': self.status,
            'progress_percentage': self.progress_percentage,
            'total_items': self.total_items,
            'completed_items': self.completed_items,
            'total_participants': self.total_participants,
            'total_cost': float(self.total_cost),
            'paid_amount': float(self.paid_amount),
            'pending_amount': float(self.pending_amount),
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'is_overdue': self.is_overdue,
            'recent_consumptions': self.recent_consumptions
        }


@dataclass
class ExpeditionTimelineEntry:
    """Timeline entry for expedition progress."""
    id: int
    expedition_id: int
    event_type: str
    event_description: str
    event_data: Dict[str, Any]
    created_at: datetime
    participant_name: Optional[str] = None
    pirate_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'id': self.id,
            'expedition_id': self.expedition_id,
            'event_type': self.event_type,
            'event_description': self.event_description,
            'event_data': self.event_data,
            'created_at': self.created_at.isoformat(),
            'participant_name': self.participant_name,
            'pirate_name': self.pirate_name
        }


@dataclass
class ExpeditionAnalytics:
    """Analytics data for expedition performance."""
    expedition_id: int
    total_revenue: Decimal
    total_cost: Decimal
    profit_margin: Decimal
    efficiency_score: float
    completion_rate: float
    average_item_price: Decimal
    price_variance: Decimal
    participant_count: int
    timeline_data: List[Dict[str, Any]]
    cost_breakdown: Dict[str, Decimal]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'expedition_id': self.expedition_id,
            'total_revenue': float(self.total_revenue),
            'total_cost': float(self.total_cost),
            'profit_margin': float(self.profit_margin),
            'efficiency_score': self.efficiency_score,
            'completion_rate': self.completion_rate,
            'average_item_price': float(self.average_item_price),
            'price_variance': float(self.price_variance),
            'participant_count': self.participant_count,
            'timeline_data': self.timeline_data,
            'cost_breakdown': {k: float(v) for k, v in self.cost_breakdown.items()}
        }