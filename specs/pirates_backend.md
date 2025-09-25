# 🏴‍☠️ **Pirates Expedition Backend - Implementation Strategy**

## **🎯 Core Concept Mapping**

### **Business Logic → Pirate Theme Translation**
```
Products (Estoque) → Expedition Items (Berry, Syrup, etc.)
Sales (Vendas) → Item Consumption by Pirates
Users → Pirates (anonymized via Brambler)
Inventory → Expedition Resources
Debts → Outstanding Pirate Payments
Smart Contracts → Expedition Agreements
Owner Dashboard → Captain's Command Center
```

---

## **🎮 Game Concept Overview**

### **Pirates Expedition**
> This project aims to create a workflow list for day-to-day operations. In it, we will have several expeditions, each corresponding to a different run. We will calculate deadlines and profits. (The goal is to **evolve the Telegram-Bot-App into a miniapp with this game**).

### **Core Game Mechanics**
- **AFK Management Dashboard**: Visual business intelligence layer over existing bot operations
- **Owner-Only Access**: Single-player experience for business owner
- **Pirate Theme**: All UI elements themed around pirates and expeditions
- **Real Business Data**: Game visualizes actual business operations

---

## **🗄️ Database Extensions**

### **New Tables for Expedition System**
```sql
-- Expeditions (Main expedition data)
CREATE TABLE expeditions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    deadline_date TIMESTAMP NOT NULL,
    created_date TIMESTAMP DEFAULT NOW(),
    status VARCHAR(50) DEFAULT 'active', -- active, completed, cancelled
    owner_chat_id BIGINT NOT NULL,
    brambler_key TEXT, -- Encryption key for names
    total_value DECIMAL(10,2) DEFAULT 0
);

-- Expedition Items (Products selected for expedition)
CREATE TABLE expedition_items (
    id SERIAL PRIMARY KEY,
    expedition_id INTEGER REFERENCES expeditions(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES Produtos(id),
    quantity INTEGER NOT NULL,
    quality_grade CHAR(1) CHECK (quality_grade IN ('A', 'B', 'C')),
    price_per_unit DECIMAL(10,2) NOT NULL,
    consumed_quantity INTEGER DEFAULT 0,
    created_date TIMESTAMP DEFAULT NOW()
);

-- Pirate Names (Brambler anonymization)
CREATE TABLE pirate_names (
    id SERIAL PRIMARY KEY,
    real_username VARCHAR(255) NOT NULL,
    pirate_name VARCHAR(255) NOT NULL,
    expedition_id INTEGER REFERENCES expeditions(id) ON DELETE CASCADE,
    created_date TIMESTAMP DEFAULT NOW(),
    UNIQUE(real_username, expedition_id)
);

-- Item Consumption (When pirates "consume" items)
CREATE TABLE item_consumptions (
    id SERIAL PRIMARY KEY,
    expedition_id INTEGER REFERENCES expeditions(id) ON DELETE CASCADE,
    expedition_item_id INTEGER REFERENCES expedition_items(id),
    pirate_name_id INTEGER REFERENCES pirate_names(id),
    quantity_consumed INTEGER NOT NULL,
    total_cost DECIMAL(10,2) NOT NULL,
    payment_status VARCHAR(50) DEFAULT 'pending', -- pending, partial, paid
    payment_term VARCHAR(100), -- e.g., "30 days", "immediate", etc.
    consumption_date TIMESTAMP DEFAULT NOW(),
    original_sale_id INTEGER REFERENCES Vendas(id) -- Link to original bot sale
);
```

---

## **🔧 API Endpoints Design**

### **Backend Flask Routes**
```python
# Expedition Management
@app.route('/api/expeditions', methods=['GET', 'POST'])
@require_permission('owner')
def expeditions():
    # GET: List all expeditions
    # POST: Create new expedition

@app.route('/api/expeditions/<int:expedition_id>', methods=['GET', 'PUT', 'DELETE'])
@require_permission('owner')
def expedition_detail(expedition_id):
    # Manage individual expedition

@app.route('/api/expeditions/<int:expedition_id>/items', methods=['GET', 'POST'])
@require_permission('owner')
def expedition_items(expedition_id):
    # Manage expedition items

@app.route('/api/expeditions/<int:expedition_id>/consume', methods=['POST'])
@require_permission('owner')
def consume_item(expedition_id):
    # Record item consumption by pirates

# Brambler (Name Anonymization)
@app.route('/api/brambler/generate/<int:expedition_id>', methods=['POST'])
@require_permission('owner')
def generate_pirate_names(expedition_id):
    # Generate anonymized names for expedition

@app.route('/api/brambler/decrypt/<int:expedition_id>', methods=['GET'])
@require_permission('owner')
def decrypt_pirate_names(expedition_id):
    # Decrypt real names (owner only)

# Dashboard Data
@app.route('/api/dashboard/timeline')
@require_permission('owner')
def expedition_timeline():
    # Main dashboard data

@app.route('/api/dashboard/overdue')
@require_permission('owner')
def overdue_expeditions():
    # List of overdue expeditions

# Real-time Updates
@app.route('/api/stream/<int:expedition_id>')
@require_permission('owner')
def expedition_stream(expedition_id):
    # Server-sent events for real-time updates
```

---

## **🔐 Backend Service Architecture**

### **Service Interfaces**
```python
# core/interfaces.py - Add expedition service interfaces
class IExpeditionService(ABC):
    """Interface for expedition management services."""

    @abstractmethod
    def create_expedition(self, request: ExpeditionCreateRequest) -> ExpeditionResponse:
        """Create a new expedition."""
        pass

    @abstractmethod
    def get_expedition_by_id(self, expedition_id: int) -> Optional[ExpeditionResponse]:
        """Get expedition by ID."""
        pass

    @abstractmethod
    def get_expeditions(self, owner_chat_id: int) -> List[ExpeditionResponse]:
        """Get all expeditions for owner."""
        pass

    @abstractmethod
    def add_items_to_expedition(self, expedition_id: int, items: List[ExpeditionItemRequest]) -> bool:
        """Add products as expedition items."""
        pass

    @abstractmethod
    def consume_item(self, consumption_data: ItemConsumptionRequest) -> ItemConsumptionResponse:
        """Record item consumption by pirate."""
        pass

    @abstractmethod
    def check_expedition_completion(self, expedition_id: int) -> bool:
        """Check if all items are consumed."""
        pass

    @abstractmethod
    def delete_expedition(self, expedition_id: int) -> bool:
        """Delete an expedition."""
        pass

class IBramblerService(ABC):
    """Interface for name anonymization services."""

    @abstractmethod
    def generate_pirate_names(self, real_usernames: List[str], expedition_id: int) -> Dict[str, str]:
        """Generate anonymized names for expedition."""
        pass

    @abstractmethod
    def encrypt_name_mapping(self, mapping: Dict[str, str], owner_key: str) -> str:
        """Encrypt real name mapping."""
        pass

    @abstractmethod
    def decrypt_name_mapping(self, encrypted_data: str, owner_key: str) -> Dict[str, str]:
        """Decrypt real names for owner."""
        pass

    @abstractmethod
    def get_pirate_name(self, real_username: str, expedition_id: int) -> Optional[str]:
        """Get pirate name for user in expedition."""
        pass
```

### **Service Classes**
```python
# services/expedition_service.py
from services.base_service import BaseService
from core.interfaces import IExpeditionService
from models.expedition import *
from typing import List, Optional

class ExpeditionService(BaseService, IExpeditionService):
    """Service for expedition management with transaction support."""

    def __init__(self, database_manager):
        super().__init__(database_manager)

    def create_expedition(self, request: ExpeditionCreateRequest) -> ExpeditionResponse:
        """Create new expedition with validation and transaction management."""
        # Implementation with proper error handling and validation

    def get_expeditions(self, owner_chat_id: int) -> List[ExpeditionResponse]:
        """Get all expeditions for owner with proper connection management."""
        # Implementation following BaseService patterns

    def add_items_to_expedition(self, expedition_id: int, items: List[ExpeditionItemRequest]) -> bool:
        """Add products as expedition items with inventory validation."""
        # Implementation with transaction rollback support

    def consume_item(self, consumption_data: ItemConsumptionRequest) -> ItemConsumptionResponse:
        """Record item consumption by pirate with FIFO processing."""
        # Implementation integrating with existing sales system

    def check_expedition_completion(self, expedition_id: int) -> bool:
        """Check if all items are consumed with proper error boundaries."""
        # Implementation with comprehensive status checking

# services/brambler_service.py
from services.base_service import BaseService
from core.interfaces import IBramblerService
from typing import List, Dict, Optional

class BramblerService(BaseService, IBramblerService):
    """Service for name anonymization with encryption support."""

    def __init__(self, database_manager):
        super().__init__(database_manager)
        self.npc_names = [
            'Link', 'Zelda', 'Mario', 'Luigi', 'Samus', 'Pikachu',
            'Cloud', 'Tifa', 'Geralt', 'Ciri', 'Kratos', 'Aloy'
        ]

    def generate_pirate_names(self, real_usernames: List[str], expedition_id: int) -> Dict[str, str]:
        """Generate anonymized names with database persistence."""
        # Implementation with proper transaction management

    def encrypt_name_mapping(self, mapping: Dict[str, str], owner_key: str) -> str:
        """Encrypt real name mapping using secure encryption."""
        # Implementation with proper error handling

    def decrypt_name_mapping(self, encrypted_data: str, owner_key: str) -> Dict[str, str]:
        """Decrypt real names for owner with validation."""
        # Implementation with security validation

    def get_pirate_name(self, real_username: str, expedition_id: int) -> Optional[str]:
        """Get pirate name for user in expedition."""
        # Implementation following BaseService connection patterns
```

### **Service Registration Integration**
```python
# core/modern_service_container.py - Add expedition services registration
from core.interfaces import IExpeditionService, IBramblerService
from services.expedition_service import ExpeditionService
from services.brambler_service import BramblerService

def register_expedition_services(container: DIContainer, database_manager):
    """Register expedition-related services in the DI container."""

    # Register expedition service as singleton
    container.register_service(
        IExpeditionService,
        lambda: ExpeditionService(database_manager),
        singleton=True
    )

    # Register brambler service as singleton
    container.register_service(
        IBramblerService,
        lambda: BramblerService(database_manager),
        singleton=True
    )

# Add to initialize_services() function:
def initialize_services(config: Dict[str, Any]):
    """Initialize all services including expedition services."""
    # ... existing service registration ...

    # Register expedition services
    register_expedition_services(_container, _database_manager)

    # ... rest of initialization ...
```

### **Data Models**
```python
# models/expedition.py
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional, List

@dataclass
class Expedition:
    """Core expedition entity model."""
    id: int
    name: str
    description: str
    deadline_date: datetime
    created_date: datetime
    status: str
    owner_chat_id: int
    brambler_key: Optional[str]
    total_value: Decimal

@dataclass
class ExpeditionCreateRequest:
    """Request DTO for creating expeditions."""
    name: str
    description: str
    deadline_date: datetime
    owner_chat_id: int

@dataclass
class ExpeditionResponse:
    """Response DTO for expedition data."""
    id: int
    name: str
    description: str
    deadline_date: datetime
    status: str
    total_value: Decimal
    items_count: int
    pirates_count: int
    overdue: bool

@dataclass
class ExpeditionItem:
    """Core expedition item entity model."""
    id: int
    expedition_id: int
    product_id: int
    quantity: int
    quality_grade: str
    price_per_unit: Decimal
    consumed_quantity: int
    created_date: datetime

@dataclass
class ExpeditionItemRequest:
    """Request DTO for expedition items."""
    product_id: int
    quantity: int
    quality_grade: str  # A, B, C
    price_per_unit: Decimal

@dataclass
class PirateName:
    """Core pirate name entity model."""
    id: int
    real_username: str
    pirate_name: str
    expedition_id: int
    created_date: datetime

@dataclass
class ItemConsumption:
    """Core item consumption entity model."""
    id: int
    expedition_id: int
    expedition_item_id: int
    pirate_name_id: int
    quantity_consumed: int
    total_cost: Decimal
    payment_status: str
    payment_term: str
    consumption_date: datetime
    original_sale_id: Optional[int]

@dataclass
class ItemConsumptionRequest:
    """Request DTO for item consumption."""
    expedition_id: int
    expedition_item_id: int
    pirate_username: str
    quantity_consumed: int
    payment_term: str

@dataclass
class ItemConsumptionResponse:
    """Response DTO for item consumption."""
    id: int
    expedition_id: int
    pirate_name: str
    item_name: str
    quantity_consumed: int
    total_cost: Decimal
    payment_status: str
    consumption_date: datetime
```

---

## **⚡ Bot Integration**

### **Handler Architecture Integration**
```python
# handlers/expedition_handler.py - Following existing architecture patterns
from handlers.base_handler import BaseHandler
from core.interfaces import IExpeditionService, IBramblerService
from models.expedition import *
from utils.permissions import require_permission
from utils.message_cleaner import add_message_to_delete, protect_message
from utils.input_sanitizer import sanitize_input
from telegram.ext import ConversationHandler

# Conversation states
EXPEDITION_MENU, EXPEDITION_CREATE_NAME, EXPEDITION_CREATE_DESC, EXPEDITION_CREATE_DEADLINE = range(4)
EXPEDITION_ADD_ITEMS, EXPEDITION_SELECT_PRODUCT, EXPEDITION_SET_QUANTITY = range(4, 7)

class ExpeditionHandler(BaseHandler):
    """Handler for expedition management with proper error boundaries."""

    def __init__(self, expedition_service: IExpeditionService, brambler_service: IBramblerService):
        super().__init__()
        self.expedition_service = expedition_service
        self.brambler_service = brambler_service

    @require_permission('owner')
    async def create_expedition_command(self, update, context):
        """Create expedition command with input validation."""
        try:
            # Implementation with proper error handling and auto-cleanup
            # Follow existing conversation patterns from product_handler.py
            pass
        except Exception as e:
            await self.handle_error(update, context, e, "creating expedition")

    @require_permission('owner')
    async def list_expeditions_command(self, update, context):
        """List expeditions with proper message management."""
        try:
            # Implementation following existing patterns
            # Use protect_message for important data
            pass
        except Exception as e:
            await self.handle_error(update, context, e, "listing expeditions")

    @require_permission('owner')
    async def expedition_status_command(self, update, context):
        """Expedition status with auto-cleanup."""
        try:
            # Implementation with message auto-deletion
            pass
        except Exception as e:
            await self.handle_error(update, context, e, "getting expedition status")

    def get_conversation_handler(self) -> ConversationHandler:
        """Get conversation handler following existing patterns."""
        # Implementation similar to product_handler conversation setup
        pass

# Enhanced /buy command integration
# handlers/buy_handler.py - Add expedition integration
class EnhancedBuyHandler(BuyHandler):
    """Enhanced buy handler with expedition integration."""

    def __init__(self, product_service, sales_service, expedition_service):
        super().__init__(product_service, sales_service)
        self.expedition_service = expedition_service

    async def enhanced_buy_command(self, update, context):
        """Enhanced buy command linking to expeditions."""
        # /order product quantity price person payment expedition_id
        # Links purchase to specific expedition
        # Creates item consumption record
        # Updates expedition progress
        # Follows existing buy_handler patterns with expedition integration
        pass
```

### **Handler Registration Integration**
```python
# handlers/handler_migration.py - Add expedition handlers
from handlers.expedition_handler import ExpeditionHandler
from core.modern_service_container import get_service
from core.interfaces import IExpeditionService, IBramblerService

def register_expedition_handlers(application, container):
    """Register expedition handlers following existing patterns."""

    # Get services from container
    expedition_service = container.get_service(IExpeditionService)
    brambler_service = container.get_service(IBramblerService)

    # Create handler instance
    expedition_handler = ExpeditionHandler(expedition_service, brambler_service)

    # Register conversation handler
    expedition_conv_handler = expedition_handler.get_conversation_handler()
    application.add_handler(expedition_conv_handler)

    # Register individual command handlers
    application.add_handler(CommandHandler("expeditions", expedition_handler.list_expeditions_command))
    application.add_handler(CommandHandler("expedition_status", expedition_handler.expedition_status_command))

# Update configure_handlers() function to include expedition handlers
def configure_handlers(application, container):
    """Configure all handlers including expedition handlers."""
    # ... existing handler registration ...

    # Register expedition handlers
    register_expedition_handlers(application, container)

    # ... rest of registration ...
```

### **WebSocket Integration**
```python
# services/websocket_service.py
class ExpeditionWebSocketService:
    def __init__(self):
        self.connected_clients = {}

    async def broadcast_expedition_update(self, expedition_id: int, update_data: dict):
        # Broadcast real-time updates to connected clients

    async def send_deadline_alert(self, expedition_id: int):
        # Send deadline warnings

    async def notify_expedition_completion(self, expedition_id: int):
        # Notify when expedition completes
```

---

## **🛡️ Security & Privacy Implementation**

### **Brambler Encryption System**
```python
# utils/encryption.py
class BramblerEncryption:
    @staticmethod
    def generate_owner_key(chat_id: int, timestamp: str) -> str:
        # Generate unique key for owner

    @staticmethod
    def encrypt_names(name_mapping: dict, key: str) -> str:
        # AES encryption for name mapping

    @staticmethod
    def decrypt_names(encrypted_data: str, key: str) -> dict:
        # Decrypt real names with owner key
```

### **Permission Integration**
```python
# All expedition endpoints require owner permission
@require_permission('owner')
def expedition_endpoints():
    # Only bot owner can access expedition system
    # Integrates with existing permission system
```

---

## **📊 Business Logic Integration**

### **Data Integration Strategy**
- **Existing Products** → **Expedition Items**: Direct mapping with quality modifiers
- **Sales Records** → **Item Consumption**: Maintain audit trail
- **User Management** → **Brambler System**: Anonymous but traceable
- **Debts** → **Pirate Outstanding Payments**: Visual debt tracking

### **Performance Optimization**
- **Database Indexing**: Optimized queries for expedition data
- **Caching Strategy**: Expedition status cached for dashboard
- **Connection Pooling**: Leverage existing database architecture
- **Queue Processing**: Async updates for real-time features

---

## **🚀 Backend Implementation Roadmap**

### **Phase 1: Database & Core Services (2-3 weeks)**
- [ ] Add expedition tables to database/schema.py
- [ ] Create models/expedition.py with all DTOs following existing patterns
- [ ] Add IExpeditionService and IBramblerService to core/interfaces.py
- [ ] Implement services/expedition_service.py extending BaseService
- [ ] Implement services/brambler_service.py with encryption
- [ ] Register expedition services in core/modern_service_container.py
- [ ] Set up basic Flask API endpoints following existing app.py structure

### **Phase 2: Business Logic Integration (2-3 weeks)**
- [ ] Integrate with existing product/sales system
- [ ] Implement item consumption tracking
- [ ] Build expedition completion logic
- [ ] Add deadline monitoring system
- [ ] Create debt tracking integration

### **Phase 3: Advanced Features (2 weeks)**
- [ ] Implement WebSocket real-time updates
- [ ] Add Brambler encryption/decryption
- [ ] Build expedition analytics
- [ ] Create export functionality
- [ ] Optimize database queries

### **Phase 4: Bot Command Integration (1 week)**
- [ ] Create handlers/expedition_handler.py extending BaseHandler
- [ ] Add expedition conversation states and error handling
- [ ] Modify handlers/buy_handler.py for expedition integration
- [ ] Update handlers/handler_migration.py for expedition handler registration
- [ ] Test end-to-end workflows with existing permission system
- [ ] Add expedition commands to handlers/commands_handler.py

---

## **🎯 Expected Backend Outcomes**

### **API Capabilities**
- **RESTful Expedition Management**: Complete CRUD operations
- **Real-time Updates**: WebSocket integration for live data
- **Name Anonymization**: Secure Brambler system
- **Business Integration**: Seamless connection with existing bot operations

### **Performance Targets**
- **Response Time**: <200ms for API endpoints
- **Real-time Latency**: <50ms for WebSocket updates
- **Database Efficiency**: Optimized queries with proper indexing
- **Scalability**: Support for 100+ concurrent expeditions

### **Security Features**
- **Owner-Only Access**: All endpoints protected
- **Data Encryption**: Brambler system for privacy
- **Audit Trail**: Complete operation logging
- **Input Validation**: Comprehensive data sanitization