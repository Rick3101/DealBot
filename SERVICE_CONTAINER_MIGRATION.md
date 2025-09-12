# 🏗️ Service Container Migration Guide

## 🎯 Overview

You now have a **modern dependency injection container** that replaces the old service pattern with proper:
- **Interface-based design**
- **Lifecycle management** (Singleton, Transient, Scoped)
- **Configuration management**
- **Health monitoring**
- **Proper error handling**

## 🔄 Migration Steps

### 1. Switch to New Application Entry Point

**Replace your current app.py with the new version:**

```bash
# Backup current app
mv app.py app_old.py

# Use new app
mv app_new.py app.py
```

### 2. Update Environment Variables (Optional but Recommended)

Add these new optional configuration variables:

```bash
# Environment settings
ENVIRONMENT=production  # or development, testing
DEBUG=false
LOG_LEVEL=INFO

# Service settings  
ENABLE_CACHING=true
ENABLE_HEALTH_CHECKS=true
ENABLE_METRICS=true
```

## 🏛️ Architecture Changes

### **Before (Old Pattern)**
```python
# Direct service imports - tightly coupled
import services.produto_service_pg as produto_service

async def handler(update, context):
    produtos = produto_service.listar_produtos_com_estoque()
```

### **After (New Pattern)**
```python
# Interface-based dependency injection - loosely coupled
from core.modern_service_container import get_product_service

async def handler(update, context):
    product_service = get_product_service()  # Gets IProductService
    produtos = product_service.get_products_with_stock()
```

## 🔧 Key Components

### 1. **Service Interfaces** (`core/interfaces.py`)
- `IUserService` - User management contract
- `IProductService` - Product management contract  
- `ISalesService` - Sales management contract
- `IDatabaseManager` - Database access contract

### 2. **Dependency Injection Container** (`core/di_container.py`)
- `DIContainer` - Main DI container
- `ServiceLifetime` - Singleton, Transient, Scoped
- `ServiceDescriptor` - Service registration metadata

### 3. **Service Registry** (`core/modern_service_container.py`)
- `ServiceRegistry` - Central service configuration
- `initialize_services()` - Bootstrap all services
- `get_*_service()` - Service accessor functions

### 4. **Configuration System** (`core/config.py`)
- `ApplicationConfig` - Centralized configuration
- Environment-based settings
- Validation and error handling

## 🚀 Benefits You Get

### **1. Loose Coupling**
```python
# Easy to switch implementations
class MockUserService(IUserService):
    def authenticate_user(self, username, password, chat_id):
        return User(id=1, username="test", level=UserLevel.ADMIN)

# Register for testing
container.register_singleton(IUserService, instance=MockUserService())
```

### **2. Lifecycle Management**
```python
# Singleton - one instance for entire app
container.register_singleton(IUserService, UserService)

# Transient - new instance every time  
container.register_transient(IEmailService, EmailService)

# Scoped - one instance per request/context
container.register_scoped(ISessionService, SessionService)
```

### **3. Configuration Management**
```python
from core.config import get_config

config = get_config()
print(f"Running in {config.environment.value} mode")
print(f"Database pool: {config.database.pool_max_connections}")
```

### **4. Health Monitoring**
```python
from core.modern_service_container import health_check_services

health = health_check_services()
if not health['container']['healthy']:
    logger.error("Services are unhealthy!")
```

## 📊 New Endpoints

Your app now has enhanced monitoring endpoints:

### **GET /health**
Detailed health check with service status:
```json
{
  "status": "healthy",
  "timestamp": "2025-01-30T12:00:00Z",
  "services": {
    "container": {"healthy": true, "registered_services": 3},
    "services": {
      "IUserService": {"healthy": true, "message": "Service operational"},
      "IProductService": {"healthy": true, "message": "Service operational"}
    }
  },
  "bot": {"bot_ready": true},
  "config": {"environment": "production", "debug": false}
}
```

### **GET /services**
Service diagnostics and registration info:
```json
{
  "health": {"container": {"healthy": true}},
  "service_info": {
    "registered_services": {
      "IUserService": {
        "interface": "IUserService", 
        "implementation": "UserService",
        "lifetime": "singleton",
        "is_singleton_created": true
      }
    }
  }
}
```

### **GET /config**
Configuration information (sensitive data hidden):
```json
{
  "environment": "production",
  "debug": false,
  "database": {"pool_max_connections": 20},
  "services": {"enable_caching": true}
}
```

## 🧪 Testing Your Services

### **Unit Testing with Mocks**
```python
import pytest
from core.di_container import DIContainer
from core.interfaces import IUserService

class MockUserService(IUserService):
    def get_user_by_chat_id(self, chat_id):
        return User(id=1, username="test")

def test_user_handler():
    # Setup test container
    container = DIContainer()
    container.register_singleton(IUserService, instance=MockUserService())
    
    # Test your handler with mock service
    # ...
```

### **Integration Testing**
```python
def test_service_integration():
    from core.modern_service_container import initialize_services, get_user_service
    
    # Initialize with test config
    initialize_services({"environment": "testing"})
    
    user_service = get_user_service()
    assert user_service is not None
```

## ⚡ Performance Benefits

### **1. Lazy Loading**
Services are only created when first accessed:
```python
# UserService only created when first needed
user_service = get_user_service()  # Creates instance
user_service2 = get_user_service() # Returns same instance (singleton)
```

### **2. Connection Pooling**
Database connections are properly managed:
```python
# One database manager for entire app
db_manager = get_database_manager()  # Singleton with connection pool
```

### **3. Memory Management**
Proper cleanup and disposal:
```python
# Automatic cleanup on app shutdown
registry.dispose()  # Closes all services and connections
```

## 🔒 Security Improvements

### **1. Input Validation**
Built into service layer:
```python
# Automatic sanitization and validation
user_service.create_user(CreateUserRequest(
    username="test",  # Will be sanitized
    password="pass"   # Will be validated
))
```

### **2. Configuration Validation**
Environment variables are validated:
```python
config = get_config()
errors = config.validate()
if errors:
    raise ValueError(f"Configuration errors: {errors}")
```

## 🐛 Troubleshooting

### **Service Not Found Error**
```
ValueError: Service IUserService is not registered
```
**Solution:** Make sure `initialize_services()` is called before using services.

### **Database Not Initialized Error**
```
RuntimeError: Database manager not initialized
```
**Solution:** Call `initialize_database()` before initializing services.

### **Configuration Validation Errors**
```
Configuration validation errors: ['BOT_TOKEN environment variable is required']
```
**Solution:** Set required environment variables.

## 🎉 Migration Complete!

You now have a **production-ready service container** with:

✅ **Proper dependency injection**  
✅ **Interface-based design**  
✅ **Lifecycle management**  
✅ **Configuration management**  
✅ **Health monitoring**  
✅ **Error handling**  
✅ **Testing support**  
✅ **Performance optimization**  

Your codebase follows **industry best practices** used by frameworks like **Spring Boot**, **.NET Core**, and **FastAPI**! 🚀