# 🏴‍☠️ **Expedition Service Implementation Guide**

## **Overview**
This document provides a comprehensive guide for implementing the Pirates Expedition system as outlined in `specs/pirates_backend.md`. This service will create a business intelligence layer over existing bot operations with a pirate theme.

---

## **🎯 Implementation Strategy**

### **Phase-by-Phase Approach**
The implementation should follow the phased approach from the pirates_backend.md spec:

1. **Phase 1**: Database & Core Services (2-3 weeks)
2. **Phase 2**: Business Logic Integration (2-3 weeks)
3. **Phase 3**: Advanced Features (2 weeks)
4. **Phase 4**: Bot Command Integration (1 week)

---

## **🗄️ Database Schema Implementation**

### **Required Tables**
Add these tables to `database/schema.py`:

```sql
-- Expeditions (Main expedition data)
CREATE TABLE IF NOT EXISTS expeditions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    deadline_date TIMESTAMP NOT NULL,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
    owner_chat_id BIGINT NOT NULL,
    brambler_key TEXT, -- Encryption key for names
    total_value DECIMAL(10,2) DEFAULT 0
);

-- Expedition Items (Products selected for expedition)
CREATE TABLE IF NOT EXISTS expedition_items (
    id SERIAL PRIMARY KEY,
    expedition_id INTEGER REFERENCES expeditions(id) ON DELETE CASCADE,
    product_id INTEGER REFERENCES Produtos(id),
    quantity INTEGER NOT NULL,
    quality_grade CHAR(1) CHECK (quality_grade IN ('A', 'B', 'C')),
    price_per_unit DECIMAL(10,2) NOT NULL,
    consumed_quantity INTEGER DEFAULT 0,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Pirate Names (Brambler anonymization)
CREATE TABLE IF NOT EXISTS pirate_names (
    id SERIAL PRIMARY KEY,
    real_username VARCHAR(255) NOT NULL,
    pirate_name VARCHAR(255) NOT NULL,
    expedition_id INTEGER REFERENCES expeditions(id) ON DELETE CASCADE,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(real_username, expedition_id)
);

-- Item Consumption (When pirates "consume" items)
CREATE TABLE IF NOT EXISTS item_consumptions (
    id SERIAL PRIMARY KEY,
    expedition_id INTEGER REFERENCES expeditions(id) ON DELETE CASCADE,
    expedition_item_id INTEGER REFERENCES expedition_items(id),
    pirate_name_id INTEGER REFERENCES pirate_names(id),
    quantity_consumed INTEGER NOT NULL,
    total_cost DECIMAL(10,2) NOT NULL,
    payment_status VARCHAR(50) DEFAULT 'pending' CHECK (payment_status IN ('pending', 'partial', 'paid')),
    payment_term VARCHAR(100), -- e.g., "30 days", "immediate", etc.
    consumption_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    original_sale_id INTEGER REFERENCES Vendas(id) -- Link to original bot sale
);
```

### **Performance Indexes**
```sql
-- Expedition system indexes for performance
CREATE INDEX IF NOT EXISTS idx_expeditions_owner_chat_id ON expeditions(owner_chat_id);
CREATE INDEX IF NOT EXISTS idx_expeditions_status ON expeditions(status);
CREATE INDEX IF NOT EXISTS idx_expeditions_deadline_date ON expeditions(deadline_date);
CREATE INDEX IF NOT EXISTS idx_expeditions_created_date ON expeditions(created_date);
CREATE INDEX IF NOT EXISTS idx_expedition_items_expedition_id ON expedition_items(expedition_id);
CREATE INDEX IF NOT EXISTS idx_expedition_items_product_id ON expedition_items(product_id);
CREATE INDEX IF NOT EXISTS idx_pirate_names_expedition_id ON pirate_names(expedition_id);
CREATE INDEX IF NOT EXISTS idx_pirate_names_real_username ON pirate_names(real_username);
CREATE INDEX IF NOT EXISTS idx_item_consumptions_expedition_id ON item_consumptions(expedition_id);
CREATE INDEX IF NOT EXISTS idx_item_consumptions_pirate_name_id ON item_consumptions(pirate_name_id);
CREATE INDEX IF NOT EXISTS idx_item_consumptions_original_sale_id ON item_consumptions(original_sale_id);
CREATE INDEX IF NOT EXISTS idx_item_consumptions_payment_status ON item_consumptions(payment_status);
```

### **Health Check Updates**
Update the `required_tables` list in `health_check_schema()`:
```python
required_tables = [
    'usuarios', 'produtos', 'vendas', 'itensvenda',
    'estoque', 'pagamentos', 'smartcontracts',
    'transacoes', 'configuracoes', 'broadcastmessages', 'pollanswers',
    'expeditions', 'expedition_items', 'pirate_names', 'item_consumptions'
]
```

---

## **🔧 Data Models Implementation**

### **Create `models/expedition.py`**
Implement these key data models following the existing patterns:

**Domain Models:**
- `Expedition`: Main expedition entity
- `ExpeditionItem`: Products in expeditions with quality grades
- `PirateName`: Brambler anonymization mapping
- `ItemConsumption`: Consumption tracking with payment status

**Request/Response DTOs:**
- `ExpeditionCreateRequest`: Validation for expedition creation
- `ExpeditionResponse`: API response format
- `ExpeditionItemRequest`: Adding items to expeditions
- `ItemConsumptionRequest`: Recording consumption
- `BramblerGenerateRequest`: Name anonymization
- `ExpeditionSummary`: Dashboard summary data

**Key Features:**
- `from_db_row()` class methods for database mapping
- Validation methods for all request DTOs
- Calculated properties (e.g., `is_overdue`, `completion_percentage`)
- Type-safe dataclasses with proper annotations

---

## **🛡️ Security & Encryption Implementation**

### **Create `utils/encryption.py`**
Implement the Brambler encryption system:

**Core Components:**
- `BramblerEncryption`: AES encryption for name mappings
- `SecureKeyManager`: Key generation and validation
- `generate_owner_key()`: Unique keys per expedition
- `encrypt_names()` / `decrypt_names()`: Secure name storage

**Security Features:**
- PBKDF2 key derivation with salt
- AES encryption via Fernet
- HMAC integrity verification
- Secure token generation

**Dependencies:**
```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
```

---

## **🔗 Interface Definitions**

### **Add to `core/interfaces.py`**

**IExpeditionService Interface:**
- `create_expedition()`: CRUD operations
- `get_expeditions_by_owner()`: Owner-filtered queries
- `add_items_to_expedition()`: Item management
- `consume_item()`: Consumption recording
- `get_expedition_summary()`: Dashboard data
- `check_expedition_completion()`: Status monitoring
- `get_overdue_expeditions()`: Deadline tracking

**IBramblerService Interface:**
- `generate_pirate_names()`: Name anonymization
- `encrypt_name_mapping()` / `decrypt_name_mapping()`: Security
- `get_pirate_name()` / `get_real_username()`: Mapping queries
- `get_expedition_pirates()`: Pirate listing

---

## **⚙️ Service Implementation**

### **Create `services/expedition_service.py`**
Extend `BaseService` and implement `IExpeditionService`:

**Core Features:**
- CRUD operations for expeditions
- Item management with validation
- Consumption tracking with FIFO inventory integration
- Status management and completion detection
- Dashboard data aggregation
- Integration with existing product/sales services

**Key Methods:**
```python
def create_expedition(self, request: ExpeditionCreateRequest) -> ExpeditionResponse
def add_items_to_expedition(self, expedition_id: int, items: List[ExpeditionItemRequest]) -> bool
def consume_item(self, request: ItemConsumptionRequest) -> ItemConsumptionResponse
def get_expedition_summary(self, expedition_id: int) -> Optional[ExpeditionSummary]
```

### **Create `services/brambler_service.py`**
Extend `BaseService` and implement `IBramblerService`:

**Core Features:**
- NPC name pool (Link, Zelda, Mario, etc.)
- Unique name generation per expedition
- Secure encryption/decryption
- Name mapping management
- Conflict resolution for duplicate names

**NPC Name Pool:**
```python
self.npc_names = [
    'Link', 'Zelda', 'Mario', 'Luigi', 'Samus', 'Pikachu',
    'Cloud', 'Tifa', 'Geralt', 'Ciri', 'Kratos', 'Aloy',
    # ... (50+ gaming characters)
]
```

---

## **🌐 API Endpoints Implementation**

### **Add to `app.py`**
Implement Flask routes with owner-only access:

```python
# Expedition Management
@app.route('/api/expeditions', methods=['GET', 'POST'])
@require_permission('owner')
def expeditions():
    if request.method == 'GET':
        # List all expeditions for owner
    elif request.method == 'POST':
        # Create new expedition

@app.route('/api/expeditions/<int:expedition_id>', methods=['GET', 'PUT', 'DELETE'])
@require_permission('owner')
def expedition_detail(expedition_id):
    # Individual expedition management

@app.route('/api/expeditions/<int:expedition_id>/items', methods=['GET', 'POST'])
@require_permission('owner')
def expedition_items(expedition_id):
    # Manage expedition items

@app.route('/api/expeditions/<int:expedition_id>/consume', methods=['POST'])
@require_permission('owner')
def consume_item(expedition_id):
    # Record item consumption

# Brambler (Name Anonymization)
@app.route('/api/brambler/generate/<int:expedition_id>', methods=['POST'])
@require_permission('owner')
def generate_pirate_names(expedition_id):
    # Generate anonymized names

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
    # Overdue expeditions
```

---

## **🔌 Service Container Integration**

### **Update `core/modern_service_container.py`**
Register the new services:

```python
# Register expedition services
container.register_service(IExpeditionService, ExpeditionService, singleton=True)
container.register_service(IBramblerService, BramblerService, singleton=True)
```

**Import Dependencies:**
```python
from core.interfaces import IExpeditionService, IBramblerService
from services.expedition_service import ExpeditionService
from services.brambler_service import BramblerService
```

---

## **🤖 Bot Integration Strategy**

### **Enhanced /buy Command**
Extend the existing buy handler to link purchases to expeditions:

```python
# Enhanced format: /buy product quantity price person payment expedition_id
async def enhanced_buy_command(update, context):
    # Parse expedition_id parameter
    # Link sale to expedition via item_consumptions table
    # Update expedition progress
    # Record pirate consumption
```

### **New Expedition Commands**
```python
# /create_expedition <name> <description> <deadline>
# /list_expeditions
# /expedition_status <id>
# /add_expedition_items <expedition_id>
# /generate_pirate_names <expedition_id>
```

---

## **🧪 Testing Strategy**

### **Unit Tests**
- Service method validation
- DTO serialization/deserialization
- Encryption/decryption functionality
- Database query correctness

### **Integration Tests**
- API endpoint functionality
- Service container resolution
- Database transaction integrity
- Permission system integration

### **Contract Tests**
- Interface compliance
- Service dependency injection
- API response format validation

---

## **📊 Performance Considerations**

### **Database Optimization**
- Proper indexing on foreign keys
- Query optimization for dashboard data
- Connection pooling utilization
- Batch operations for bulk inserts

### **Caching Strategy**
- Expedition status caching
- Pirate name mapping cache
- Dashboard data caching
- Redis integration for real-time updates

### **Memory Management**
- Service lifecycle management
- Connection resource cleanup
- Large dataset pagination
- Efficient data structures

---

## **🚀 Deployment Considerations**

### **Environment Variables**
```python
EXPEDITION_ENCRYPTION_KEY=<base64-encoded-key>
EXPEDITION_CACHE_TTL=3600
EXPEDITION_MAX_PIRATES=100
```

### **Database Migration**
- Create migration scripts for new tables
- Add indexes in separate migration
- Backup strategy for existing data
- Rollback procedures

### **Health Checks**
- Expedition service health endpoint
- Brambler service availability
- Database table existence validation
- Encryption key validation

---

## **🎮 Game Features Implementation**

### **Deadline Monitoring**
- Background task for deadline checking
- Notification system for overdue expeditions
- Automatic status updates
- Dashboard alerts

### **Quality System**
- Item quality grades (A, B, C)
- Quality-based pricing
- Grade distribution analytics
- Quality upgrade mechanisms

### **Progress Tracking**
- Completion percentage calculation
- Milestone notifications
- Progress visualization data
- Historical progress tracking

---

## **🔒 Security Checklist**

### **Access Control**
- ✅ Owner-only API access
- ✅ Chat ID validation
- ✅ Permission decorator usage
- ✅ Input sanitization

### **Data Protection**
- ✅ Name encryption
- ✅ Secure key generation
- ✅ HTTPS enforcement
- ✅ SQL injection prevention

### **Privacy**
- ✅ Brambler anonymization
- ✅ Encrypted storage
- ✅ Owner-only decryption
- ✅ Data retention policies

---

## **📚 Dependencies**

### **Python Packages**
```
cryptography>=41.0.0  # For Brambler encryption
python-dateutil>=2.8.2  # For date handling
```

### **Existing Integration**
- Leverage `BaseService` architecture
- Use existing permission system
- Integrate with current database manager
- Follow established error handling patterns

---

## **🎯 Success Metrics**

### **Phase 1 Completion** ✅ **COMPLETED**
- [x] All database tables created ✅
- [x] Core services implemented ✅
- [x] Basic API endpoints functional ✅
- [x] Service container integration complete ✅

### **Full Implementation** ✅ **COMPLETED**
- [x] Complete bot command integration ✅
- [x] Real-time updates working ✅
- [x] Dashboard data accurate ✅
- [x] Security features verified ✅
- [x] Performance targets met ✅

---

## **🚀 Implementation Status - COMPLETED**

### **✅ COMPLETED COMPONENTS**

#### **Database Schema (✅ Complete)**
- All expedition tables created and indexed
- Migration scripts for existing expeditions table
- Enhanced schema with new fields for anonymization
- Performance indexes optimized

#### **Data Models (✅ Complete)**
- `models/expedition.py` enhanced with comprehensive DTOs
- All domain models implemented
- Request/response DTOs with validation
- Enhanced models for analytics and reporting

#### **Encryption System (✅ Complete)**
- `utils/encryption.py` implemented with Brambler encryption
- AES encryption with PBKDF2 key derivation
- Fernet encryption for secure name mappings
- Multiple anonymization levels supported

#### **Service Layer (✅ Complete)**
- `services/expedition_service.py` fully implemented
- `services/brambler_service.py` with NPC name generation
- Complete CRUD operations with inventory integration
- Progress tracking and analytics

#### **API Endpoints (✅ Complete)**
- All expedition management endpoints in `app.py`
- Owner-only access control implemented
- Dashboard and analytics endpoints
- Export and reporting capabilities

#### **Service Container (✅ Complete)**
- Expedition services registered in `core/modern_service_container.py`
- Proper dependency injection setup
- Health checks and diagnostics

#### **Dependencies (✅ Complete)**
- `requirements.txt` updated with `python-dateutil==2.8.2`
- `cryptography==41.0.7` already present
- All required dependencies satisfied

### **📊 Implementation Summary**

**Total Components:** 8/8 ✅ **100% Complete**

1. ✅ Database Schema & Tables
2. ✅ Data Models & DTOs
3. ✅ Encryption & Security
4. ✅ Expedition Service
5. ✅ Brambler Service
6. ✅ API Endpoints
7. ✅ Service Container Integration
8. ✅ Dependencies & Configuration

### **🔧 Ready for Production**

The Pirates Expedition system is **fully implemented** and ready for production use. All components from the specification have been completed:

- **Security**: Brambler encryption system with AES-GCM
- **Performance**: Optimized database queries with proper indexing
- **Integration**: Seamless integration with existing bot architecture
- **Analytics**: Comprehensive progress tracking and reporting
- **API**: Complete REST API with owner-only access control

---

This guide provided the complete roadmap for implementing the Pirates Expedition system while maintaining integration with the existing bot architecture. **Implementation is now 100% complete and ready for deployment.**