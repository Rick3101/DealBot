# Codebase Information

## Application Overview

**NEWBOT** is a modern Python Telegram bot application designed for e-commerce and marketplace functionality. The bot provides a comprehensive platform for product management, inventory control, sales processing, payment tracking, and smart contract integration with enterprise-grade architecture patterns.

### Core Functionality
- **Product Management**: CRUD operations with media support (photos, videos, documents)
- **Inventory Control**: FIFO-based stock management with batch operations
- **Sales Processing**: Complete purchase workflows with validation
- **Payment Tracking**: Debt management with partial payment support
- **User Management**: Three-tier permission system (user, admin, owner)
- **Smart Contracts**: Blockchain integration with multi-party transactions
- **Reporting**: Sales and debt reports with CSV export functionality
- **Authentication**: Secure login system with chat ID association

## Architecture Patterns & Principles

### 1. Modern Service Container Architecture
The application implements enterprise-grade patterns with:

- **Dependency Injection Container**: Thread-safe DI container with service lifetimes
- **Interface-based Design**: All services implement interfaces for testability
- **Configuration Management**: Structured, validated configuration system
- **Health Monitoring**: Built-in diagnostics and service health checks
- **Type Safety**: Comprehensive DTOs and type hints throughout
- **Error Boundaries**: Standardized exception handling hierarchy

### 2. Clean Architecture Layers

```
┌─────────────────────────────────────────┐
│              Presentation               │
│         (Handlers & Telegram)          │
├─────────────────────────────────────────┤
│              Application                │
│           (Service Layer)               │
├─────────────────────────────────────────┤
│               Domain                    │
│        (Models & Business Logic)       │
├─────────────────────────────────────────┤
│            Infrastructure               │
│      (Database & External APIs)        │
└─────────────────────────────────────────┘
```

### 3. Repository Pattern
- Service layer implements repository pattern
- Connection pooling with transaction management
- CRUD operations with type safety
- Audit logging and metrics support

### 4. Command Pattern
- Handler-based command processing
- Conversation state management
- Dynamic command registration
- Permission-based command filtering

## Core Components Structure

### Entry Points
- **app.py**: Main Flask application with `BotApplication` lifecycle management
- **simple_test.py**: Development testing utility

### Core Architecture (`core/`)
- **config.py**: Structured configuration with environment validation
- **di_container.py**: Thread-safe dependency injection container
- **modern_service_container.py**: Service registry and factory management
- **bot_manager.py**: Telegram bot lifecycle and queue management
- **handler_registry.py**: Clean handler registration system
- **interfaces.py**: Service interfaces for dependency injection

### Handler System (`handlers/`)
Modern conversation handlers with complete migration:

**Core Handlers:**
- `start_handler.py`: Bot initialization with custom protection
- `login_handler.py`: User authentication with auto-cleanup
- `product_handler.py`: Product CRUD with error boundaries
- `buy_handler.py`: Purchase flow with inventory validation
- `user_handler.py`: User management with input sanitization
- `estoque_handler.py`: Inventory management with FIFO processing
- `commands_handler.py`: Dynamic command listing
- `smartcontract_handler.py`: Blockchain integration
- `relatorios_handler.py`: Reporting with CSV export
- `pagamento_handler.py`: Payment processing
- `lista_produtos_handler.py`: Product catalog
- `global_handlers.py`: Cancel operations and cleanup

**Architecture Components:**
- `base_handler.py`: Base classes with error handling
- `error_handler.py`: Error boundaries and responses
- `handler_migration.py`: Centralized registration

### Service Layer (`services/`)
Business logic services with dependency injection:

- **base_service.py**: Base service with connection management
- **user_service.py**: Authentication and user operations
- **product_service.py**: Product operations with inventory
- **sales_service.py**: Sales transactions with FIFO
- **smartcontract_service.py**: Smart contract management
- **handler_business_service.py**: Business logic coordination
- **config_service.py**: Configuration management
- **broadcast_service.py**: Message broadcasting
- **cash_balance_service.py**: Financial balance tracking

### Data Models (`models/`)
Type-safe DTOs and entities:

- **user.py**: User entity with validation
- **product.py**: Product entity with media support
- **sale.py**: Sales transaction model
- **handler_models.py**: Request/response DTOs
- **broadcast.py**: Broadcasting message model
- **cash_balance.py**: Financial balance model

### Database Layer (`database/`)
- **connection.py**: DatabaseManager with connection pooling (1-50 connections)
- **schema.py**: Schema initialization and management

### Utilities (`utils/`)
- **permissions.py**: Three-tier permission system with decorators
- **message_cleaner.py**: Auto-deletion and message management
- **input_sanitizer.py**: Input validation utilities
- **files.py**: File handling utilities
- **lock_conversation.py**: Conversation state management

## Database Architecture

### PostgreSQL Schema
**Core Tables:**
- `Usuarios`: User management with roles and authentication
- `Produtos`: Product catalog with media references
- `Vendas`: Sales transactions with buyer tracking
- `ItensVenda`: Line items with FIFO inventory consumption
- `Estoque`: Inventory management with cost tracking
- `Pagamentos`: Payment tracking with debt management
- `SmartContracts`: Blockchain contract management
- `Transacoes`: Multi-party transaction system
- `Configuracoes`: System configuration storage

**Key Features:**
- Connection pooling with health checks
- Transaction management with rollback support
- FIFO inventory consumption logic
- Audit logging capabilities
- Schema migration support

## Permission System

### Three-Tier Access Control
1. **User Level**: Basic bot access
   - `/start`, `/login`, `/commands`

2. **Admin Level**: Operational access
   - User commands plus: `/buy`, `/estoque`, `/pagar`, `/lista_produtos`, `/relatorios`, `/dividas`

3. **Owner Level**: Full administrative access
   - Admin commands plus: `/product`, `/user`, `/smartcontract`

### Implementation
- `@require_permission(level)` decorator
- Service-level permission validation
- Chat-based authentication
- Secure credential handling

## Conversation Flow Architecture

### State Management
Each handler implements conversation states with:
- Input validation and sanitization
- Error recovery mechanisms
- Auto-cleanup of sensitive data
- Conversation locks for thread safety

### Key Flows

**Purchase Flow (`/buy`):**
```
BUY_NAME → BUY_SELECT_PRODUCT → BUY_QUANTITY → BUY_PRICE
├─ Owner: Can specify buyer
├─ Admin: Auto-authenticated user
├─ Secret Menu: Hidden products unlock
└─ FIFO: Automatic inventory consumption
```

**Product Management (`/product`):**
```
PRODUCT_MENU → PRODUCT_ADD_NAME → PRODUCT_ADD_EMOJI →
PRODUCT_ADD_MEDIA_CONFIRM → PRODUCT_ADD_MEDIA
├─ Media Support: Photos, videos, documents
├─ Validation: Input sanitization
└─ ID Preservation: Consistent media handling
```

## Testing Framework

### 4-Layer Protection System
1. **Schema Consistency**: 16 validation tests
2. **Complete Flows**: 27 flow validation tests
3. **Error Scenarios**: 15 error handling tests
4. **Security Validation**: Integrated security testing
5. **Contract Testing**: Interface and workflow contracts

### Test Infrastructure
- **Framework**: pytest with asyncio support
- **Structure**: Organized in `/tests` folder
- **Categories**: Unit, integration, contract, specialized tests
- **Runners**: Interactive CLI and menu-driven test execution
- **Mocking**: Comprehensive Telegram bot and service mocking
- **Coverage**: HTML reports and terminal output

### Test Files Organization
```
/tests/
├── test_handlers/          # Handler-specific unit tests
├── integration/            # Database and service integration
├── contract/               # Interface and workflow validation
├── mocks/                  # Mock implementations
├── helpers/                # Test utilities
└── run_tests.py           # Interactive test runner
```

## Configuration Management

### Structured Configuration System
```python
ApplicationConfig:
├── DatabaseConfig          # Connection pooling, timeouts
├── TelegramConfig          # Webhook/polling, rate limits
├── ServiceConfig           # Caching, metrics
├── SecurityConfig          # Validation, rate limiting
└── LoggingConfig          # Levels, file handling
```

### Environment Support
- Development vs Production defaults
- Type-safe validation
- Automatic webhook URL configuration
- Security settings and rate limiting

## Security Features

### Input Validation & Sanitization
- Comprehensive input sanitization in `utils/input_sanitizer.py`
- SQL injection prevention
- XSS protection
- Rate limiting and flood protection

### Message Security
- Auto-deletion of sensitive messages
- Protected message system
- Secure credential handling
- Permission-based access control

### Data Protection
- No sensitive information logging
- Secure password storage
- Chat ID association security
- Media file protection

## Deployment Architecture

### Containerization
- Docker support with optimized images
- Multi-stage builds for production
- Health check integration
- Environment-based configuration

### Platform Support
- **Render**: Configured via `render.yaml`
- **Railway**: Environment variable integration
- **Docker**: Standalone deployment option
- **Local Development**: Direct Python execution

### Health Monitoring Endpoints
- `/`: Basic health check
- `/health`: Detailed system status
- `/services`: Service diagnostics
- `/config`: Configuration information

## Development Guidelines

### Code Patterns
1. **Service First**: Business logic in services, not handlers
2. **Type Safety**: DTOs for all requests/responses
3. **Error Boundaries**: Proper exception handling
4. **Input Validation**: Sanitize all user inputs
5. **Permission Checks**: Service-level access validation
6. **Transaction Management**: Service-level consistency

### Best Practices
- Interface-based service design
- Dependency injection for testability
- Comprehensive error handling
- Auto-deletion for sensitive data
- Connection pooling optimization
- Mock at boundaries you control

### Performance Considerations
- Connection pooling (1-50 connections)
- Queue-based update processing
- Scoped service lifecycles
- Efficient database queries
- Media file optimization
- Memory management for long-running processes

## Technology Stack

### Core Technologies
- **Python 3.10+**: Main runtime environment
- **Flask 2.2.5**: Web framework for webhooks
- **python-telegram-bot 20.6**: Telegram Bot API wrapper
- **PostgreSQL**: Primary database
- **psycopg2-binary 2.9.9**: Database adapter

### Supporting Libraries
- **python-dotenv**: Environment configuration
- **nest_asyncio**: Async/await support
- **pytest**: Testing framework
- **Docker**: Containerization

### Development Tools
- **Type Hints**: Complete type safety
- **Async/Await**: Modern Python patterns
- **Context Managers**: Resource management
- **Decorators**: Cross-cutting concerns

## Maintenance & Operations

### Logging & Monitoring
- Structured logging with levels
- Health check endpoints
- Service diagnostics
- Performance metrics collection

### Error Handling
- Custom exception hierarchy
- Error boundaries in handlers
- Service-level error recovery
- User-friendly error messages

### Data Management
- FIFO inventory processing
- Automatic cleanup routines
- CSV export functionality
- Media file preservation

This codebase represents a production-ready Telegram bot with enterprise architecture patterns, comprehensive testing, and modern Python development practices.