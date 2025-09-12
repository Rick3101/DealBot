# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modern Python Telegram bot application for e-commerce/marketplace functionality built with Flask and python-telegram-bot. The bot implements enterprise-grade architecture with dependency injection, service containers, comprehensive configuration management, and type-safe operations for product management, inventory, purchases, payments, smart contracts, and user authentication with PostgreSQL database integration.

## Development Commands

### Running the Application
- **Primary entry point**: `python app.py` (production-ready with webhook)
- **Docker**: `docker build -t bot . && docker run -p 5000:5000 bot`

### Dependencies
- Install: `pip install -r requirements.txt`
- Key dependencies: Flask 2.2.5, python-telegram-bot 20.6, psycopg2-binary 2.9.9, python-dotenv 1.0.1, nest_asyncio 1.6.0

### Environment Variables
- `BOT_TOKEN`: Telegram bot token (required)
- `RAILWAY_URL`: Base webhook URL for deployment (e.g., https://your-app.render.com)
- `DATABASE_URL`: PostgreSQL connection string (required)
- `ENVIRONMENT`: App environment (development/production, defaults to development)
- `PORT`: Flask port (defaults to 5000)

## Modern Architecture Overview

### Core Architecture Principles
This project implements a **modern service container architecture** with the following enterprise patterns:

1. **Dependency Injection Container**: Thread-safe DI container with service lifetimes (singleton, transient, scoped)
2. **Interface-based Design**: All services implement interfaces for testability and modularity
3. **Configuration Management**: Structured, validated configuration with environment-specific defaults
4. **Health Monitoring**: Built-in health checks and service diagnostics
5. **Type Safety**: Comprehensive DTOs, validation, and type hints throughout
6. **Error Boundaries**: Standardized error handling with custom exception hierarchy

### Core Structure
- **app.py**: Main Flask application with `BotApplication` class managing lifecycle
- **core/**: Modern architecture components
  - `config.py`: Structured configuration management with validation
  - `di_container.py`: Thread-safe dependency injection container
  - `modern_service_container.py`: Service registry and factory management
  - `bot_manager.py`: Telegram bot lifecycle and queue management
  - `handler_registry.py`: Clean handler registration system
  - `interfaces.py`: Service interfaces for dependency injection
- **handlers/**: Modern conversation handlers with error boundaries
- **services/**: Business logic services with transaction management
- **models/**: Type-safe DTOs and data models
  - `user.py`: User entity model with validation
  - `product.py`: Product entity model with media support
  - `sale.py`: Sales transaction model
  - `handler_models.py`: Request/response DTOs for handlers
- **database/**: Connection pooling and schema management
  - `connection.py`: DatabaseManager with connection pooling and health checks
  - `schema.py`: Database schema initialization and management
- **utils/**: Utility modules
  - `permissions.py`: Three-tier permission system with decorators
  - `message_cleaner.py`: Auto-deletion and protected message management
  - `input_sanitizer.py`: Input validation and sanitization utilities
  - `files.py`: File handling utilities
  - `lock_conversation.py`: Conversation state management

### Handler System
All handlers use modern architecture with full migration completed:

**Core Handlers (all modern):**
- `start_handler.py`: Bot initialization with protection
- `login_handler.py`: User authentication with type-safe forms
- `product_handler.py`: Product CRUD with error boundaries
- `buy_handler.py`: Purchase flow with inventory validation
- `user_handler.py`: User management with input sanitization
- `estoque_handler.py`: Inventory management with FIFO processing
- `commands_handler.py`: Dynamic command listing
- `smartcontract_handler.py`: Blockchain integration
- `relatorios_handler.py`: Reporting with CSV export
- `pagamento_handler.py`: Payment processing with debt tracking
- `lista_produtos_handler.py`: Product catalog with media support
- `global_handlers.py`: Cancel operations and user deletion

**Architecture Components:**
- `handlers/base_handler.py`: Base classes with error handling, logging, permissions
- `handlers/error_handler.py`: Error boundaries and standardized responses
- `models/handler_models.py`: Type-safe request/response DTOs
- `handlers/handler_migration.py`: Centralized handler registration

### Modern Service Layer
The service layer implements repository pattern with dependency injection:

**Core Services:**
- `services/base_service.py`: Base service with connection management and transactions
- `services/user_service.py`: User authentication and management with security
- `services/product_service.py`: Product operations with inventory integration
- `services/sales_service.py`: Sales transactions with FIFO consumption
- `services/smartcontract_service.py`: Smart contract and transaction management
- `services/handler_business_service.py`: High-level business logic coordinator
- `services/config_service.py`: Configuration management service

**Service Features:**
- Interface-based design (`IUserService`, `IProductService`, etc.)
- Connection pooling (1-50 connections based on environment)
- Transaction management with rollback support
- Comprehensive error handling with custom exceptions
- Input validation and sanitization
- Audit logging and metrics support

### Database Architecture
- **PostgreSQL** with connection pooling
- **Schema management**: `database/schema.py` with comprehensive table structure
- **Migration support**: Clean initialization and upgrades
- **Tables**: Usuarios, Produtos, Vendas, ItensVenda, Estoque, Pagamentos, SmartContracts, Transacoes, Configuracoes

### Permission System
- Three-tier access control: 'user', 'admin', 'owner'
- `@require_permission(level)` decorator in utils/permissions.py
- Service-level permission validation
- Chat-based authentication with secure credential handling

### Configuration Management
Structured configuration with environment-aware defaults:

```python
ApplicationConfig:
├── DatabaseConfig (pooling, timeouts)
├── TelegramConfig (webhook/polling, rate limits)
├── ServiceConfig (caching, metrics)
├── SecurityConfig (validation, rate limiting)
└── LoggingConfig (levels, file handling)
```

Features:
- Type-safe configuration with validation
- Environment-specific defaults (dev vs prod)
- Automatic webhook URL configuration
- Security settings and rate limiting

## Commands & Conversation Flows

### Core Commands by Permission Level

**User Level:**
- `/start` - Bot initialization with custom protection phrase
- `/login` - User authentication flow with auto-cleanup
- `/commands` - Dynamic command listing based on permissions

**Admin Level (includes user commands):**
- `/buy` - Purchase flow with inventory validation and FIFO processing
- `/estoque` - Inventory management with batch operations
- `/pagar` - Payment processing with debt tracking
- `/lista_produtos` - Product catalog with media display
- `/relatorios` - Sales/debt reports with CSV export
- `/dividas` - Personal debt report for authenticated user with CSV export

**Owner Level (includes admin commands):**
- `/product` - Product CRUD with media management
- `/user` - User management with role assignment
- `/smartcontract` - Smart contract creation and transaction management

### Detailed Conversation Flows

#### Login Flow (`/login`)
**States:** `LOGIN_USERNAME` → `LOGIN_PASSWORD`
- Input validation and sanitization
- Secure credential verification
- Chat ID association
- Auto-deletion of sensitive messages

#### Product Management (`/product`) - Owner only
**States:** `PRODUCT_MENU` → `PRODUCT_ADD_NAME` → `PRODUCT_ADD_EMOJI` → `PRODUCT_ADD_MEDIA_CONFIRM` → `PRODUCT_ADD_MEDIA`
- **Add Product:** Name → Emoji → Optional media (photo/video/document)
- **Edit Product:** Select product → Choose property → Update with validation
- **Media Management:** Protected files with ID preservation

#### Purchase Flow (`/buy`) - Admin+
**States:** `BUY_NAME` → `BUY_SELECT_PRODUCT` → `BUY_QUANTITY` → `BUY_PRICE`
- **Owner:** Can specify buyer name
- **Admin:** Auto-uses authenticated username
- **Secret Menu:** "wubba lubba dub dub" unlocks hidden products (🧪💀 emojis)
- **Inventory Validation:** Real-time stock checking
- **FIFO Processing:** Automatic stock consumption

#### User Management (`/user`) - Owner only
**States:** `MENU` → `ADD_USERNAME`/`REMOVE_USER`/`EDIT_SELECT_USER` → `ADD_PASSWORD`/`EDIT_ACTION` → `EDIT_NEW_VALUE`/`EDIT_NIVEL`
- **Security:** Password validation, secure storage
- **Role Management:** user, admin, owner levels
- **Input Sanitization:** Comprehensive validation

#### Inventory Management (`/estoque`)
**States:** `ESTOQUE_MENU` → `ESTOQUE_ADD_SELECT` → `ESTOQUE_ADD_VALUES`
- **Format:** `quantity / price / cost`
- **Batch Operations:** Multiple product updates
- **Validation:** Strict input format checking

#### Smart Contracts (`/smartcontract`) - Owner only
**States:** `TRANSACTION_MENU` → `TRANSACTION_DESCRICAO`
- **Creation:** `/smartcontract <code>` creates contract
- **Management:** Multi-party transaction system
- **Features:** Confirmation workflow, history tracking

#### Payment Processing (`/pagar`) - Admin+
**States:** `PAGAMENTO_VALOR`
- **Debt Tracking:** Comprehensive payment history
- **Partial Payments:** Flexible payment amounts
- **Auto-completion:** Automatic status updates

#### Reports (`/relatorios`) - Admin+
**States:** `RELATORIO_MENU` → `RELATORIO_DIVIDA_NOME`
- **Sales Reports:** Complete transaction history
- **Debt Reports:** By buyer with filtering
- **CSV Export:** Temporary file generation with auto-cleanup

#### Personal Debts (`/dividas`) - Admin+
**Direct Command:** No conversation states - immediate response
- **Auto-Authentication:** Uses authenticated user's chat_id to get username
- **Personal Report:** Shows only the user's own purchases/debts
- **Total Calculation:** Displays running total of all debts
- **CSV Export:** Personal debt export with filename `minhas_dividas_{username}.csv`
- **Auto-Cleanup:** Message auto-deletes after 30 seconds

### Advanced Features

**Message Management:**
- Auto-deletion with configurable delays
- Protected message system for important content
- Conversation state management with locks

**Security Features:**
- Input sanitization and validation
- Rate limiting and flood protection
- Secure credential handling
- Permission-based access control

**Data Processing:**
- FIFO inventory consumption
- Complex debt calculations
- Media file preservation
- CSV generation with proper cleanup

## Deployment

### Docker Support
```dockerfile
FROM python:3.10-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
EXPOSE 5000
CMD ["python", "app.py"]
```

### Platform Support
- **Render**: Configured via `render.yaml` with automatic deployment
- **Environment Variables**: Structured configuration with validation
- **Health Checks**: Multiple endpoints for monitoring
- **Webhook Integration**: Automatic setup based on environment

### Health Monitoring
Available endpoints:
- `/` - Basic health check
- `/health` - Detailed system status
- `/services` - Service diagnostics
- `/config` - Configuration information

## Code Guidance

### Development Patterns
1. **Service First**: Always implement business logic in services, not handlers
2. **Type Safety**: Use DTOs for all requests/responses
3. **Error Handling**: Implement proper exception boundaries
4. **Input Validation**: Sanitize all user inputs
5. **Permission Checks**: Validate access at service level
6. **Transaction Management**: Use service-level transactions for consistency

### Testing Approach
- **Primary Framework**: pytest with asyncio support and comprehensive configuration
- **Test Location**: All tests are organized in `/tests` folder with proper structure
- **Test Categories**: 
  - Unit tests (`/tests/test_handlers/`): Handler-specific functionality tests
  - Integration tests (`/tests/integration/`): Database and service integration tests
  - Contract tests (`/tests/contract/`): Interface and workflow validation
  - Specialized tests: Schema validation, error scenarios, complete flows
- **Test Runners**: 
  - `tests/run_tests.py`: Interactive test runner with CLI and menu options
  - `run_contract_tests.py`: Contract test runner for interface validation
  - `run_improved_tests.py`: Enhanced test runner with additional features
  - `validate_test_architecture.py`: Test architecture validation utility
- **Mock System**: Comprehensive Telegram bot mocking with service container support
  - `conftest.py`: Primary test configuration and fixtures
  - `tests/mocks/`: Specialized mock implementations for services and handlers
  - `tests/helpers/query_validator.py`: Database query validation utilities
- **Coverage**: HTML reports (`htmlcov/index.html`) and terminal output available
- **Infrastructure Tests**: `test_simple_validation.py` verifies test framework functionality

## Test Reliability Framework 🛡️

### 4-Layer Protection System:

#### Layer 1: Schema Consistency ✅
- 10 tests in `test_all_handlers_schema_validation.py`
- 6 tests in `test_schema_validation.py`
- Total: 16 schema validation tests

#### Layer 2: Complete Flow Tests ✅
- 20 tests in `test_all_handlers_flows.py`
- 7 tests in `test_complete_handler_flows.py`
- Total: 27 flow validation tests

#### Layer 3: Error Scenarios ✅
- 15 tests in `test_handlers_error_scenarios.py`
- Covers: Input validation, boundary conditions, error recovery

#### Layer 4: Security Validation ✅
- Integrated in `test_handlers_error_scenarios.py`
- Covers: SQL injection, XSS, permission escalation, input sanitization

#### Layer 5: Contract Testing ✅
- Interface contracts (`test_interface_contracts.py`): Service interface validation
- Schema contracts (`test_schema_contracts.py`): Database schema consistency
- Workflow contracts (`test_workflow_contracts.py`): End-to-end workflow validation
- Integration contracts (`test_integration_contracts.py`): Cross-service integration testing

### Security Guidelines
- Never log sensitive information
- Implement proper input sanitization
- Use permission decorators consistently
- Auto-delete sensitive messages
- Validate all configuration

### Performance Considerations
- Connection pooling (1-50 connections)
- Queue-based update processing
- Scoped service lifecycles
- Efficient database queries
- Media file optimization

### Emoji Usage
- Emojis should be used only for user conversations via Telegram
- All other messages (logs, system messages, etc.) should not contain emojis

## Testing Notes
- I have a mock handler to handle my tests scenarios

## Testing Best Practices
- Mock at the boundary you control, not your own business logic. make this a directive for next tests creation
```