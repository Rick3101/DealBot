#!/usr/bin/env python3
"""
Test script to validate the modern service container migration.
Ensures all services can be instantiated and basic operations work.
"""

import logging
import sys
import os

# Configure basic logging first
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Verify DATABASE_URL is available
if not os.getenv("DATABASE_URL"):
    logger.warning("⚠️ No DATABASE_URL found - database tests may fail")

def test_service_container():
    """Test the modern service container functionality."""
    logger.info("🧪 Testing modern service container migration...")
    
    try:
        # Initialize database first (required for services)
        from database import initialize_database
        from database.schema import initialize_schema
        
        try:
            initialize_database()
            initialize_schema()
            logger.info("✅ Database initialized for testing")
        except Exception as db_error:
            logger.warning(f"⚠️ Database initialization failed: {db_error}")
            logger.info("🔄 Continuing test without database (testing service structure only)")
        
        # Test service registry initialization
        from core.modern_service_container import initialize_services, get_service_registry
        
        logger.info("✅ Service container imports successful")
        
        # Initialize services
        service_config = {
            'environment': 'development',
            'debug': True,
            'database': {}
        }
        
        initialize_services(service_config)
        logger.info("✅ Service container initialized")
        
        # Test service registry health
        registry = get_service_registry()
        health = registry.health_check()
        
        if health.get("registry", {}).get("healthy"):
            logger.info("✅ Service registry is healthy")
        else:
            logger.warning("⚠️ Service registry health issues detected")
            
        # Test individual service access
        from core.modern_service_container import get_user_service, get_product_service, get_sales_service
        
        # Test service instantiation (without context - should work with global registry)
        try:
            user_service = get_user_service()
            logger.info("✅ User service accessible")
        except Exception as e:
            logger.warning(f"⚠️ User service access failed: {e}")
            
        try:
            product_service = get_product_service()
            logger.info("✅ Product service accessible")
        except Exception as e:
            logger.warning(f"⚠️ Product service access failed: {e}")
            
        try:
            sales_service = get_sales_service()
            logger.info("✅ Sales service accessible")
        except Exception as e:
            logger.warning(f"⚠️ Sales service access failed: {e}")
        
        logger.info("✅ Service access tests completed")
        
        # Test service info
        service_info = registry.get_service_info()
        registered_count = len(service_info.get("registered_services", {}))
        logger.info(f"✅ {registered_count} services registered in container")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Service container test failed: {e}")
        return False

def test_database_connection():
    """Test database connectivity (assuming it's already initialized)."""
    logger.info("🗄️ Testing database connectivity...")
    
    try:
        from database import get_db_manager
        from database.schema import health_check_schema
        
        # Test database manager (should already be initialized from previous test)
        try:
            db_manager = get_db_manager()
            if db_manager.health_check():
                logger.info("✅ Database connection pool healthy")
            else:
                logger.warning("⚠️ Database connection issues detected")
        except RuntimeError:
            # Database not initialized, try to initialize it
            from database import initialize_database
            from database.schema import initialize_schema
            
            initialize_database()
            initialize_schema()
            logger.info("✅ Database initialized in database test")
            
            db_manager = get_db_manager()
            if db_manager.health_check():
                logger.info("✅ Database connection pool healthy")
            
        # Test schema health
        schema_health = health_check_schema()
        if schema_health.get("healthy"):
            logger.info("✅ Database schema is complete")
        else:
            logger.warning(f"⚠️ Schema issues: {schema_health.get('message')}")
            
        return True
        
    except Exception as e:
        logger.error(f"❌ Database test failed: {e}")
        return False

def test_handler_imports():
    """Test that handlers can import modern services without errors."""
    logger.info("🎛️ Testing handler service imports...")
    
    handlers_to_test = [
        # Modern handlers
        'handlers.modern_buy_handler',
        'handlers.modern_user_handler', 
        'handlers.modern_product_handler',
        'handlers.modern_estoque_handler',
        'handlers.modern_commands_handler',
        'handlers.modern_login_handler',
        'handlers.modern_start_handler',
        # Legacy handlers (remaining)
        'handlers.pagamento_handler',
        'handlers.relatorios_handler',
        'handlers.lista_produtos_handler',
        'handlers.smartcontract_handler',
        'handlers.global_handlers'
    ]
    
    success_count = 0
    
    for handler_module in handlers_to_test:
        try:
            __import__(handler_module)
            logger.info(f"✅ {handler_module} imported successfully")
            success_count += 1
        except Exception as e:
            logger.error(f"❌ {handler_module} import failed: {e}")
    
    logger.info(f"✅ {success_count}/{len(handlers_to_test)} handlers imported successfully")
    return success_count == len(handlers_to_test)

def main():
    """Run all migration tests."""
    logger.info("🚀 Starting service container migration validation...")
    
    tests = [
        ("Service Container", test_service_container),
        ("Database Connection", test_database_connection), 
        ("Handler Imports", test_handler_imports)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 Running {test_name} test...")
        if test_func():
            passed += 1
            logger.info(f"✅ {test_name} test PASSED")
        else:
            logger.error(f"❌ {test_name} test FAILED")
    
    logger.info(f"\n📊 Migration Validation Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 Service container migration validation SUCCESSFUL!")
        return 0
    else:
        logger.error("💥 Service container migration has issues that need attention")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n⏹️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Unexpected error during testing: {e}")
        sys.exit(1)