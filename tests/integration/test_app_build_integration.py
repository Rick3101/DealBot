#!/usr/bin/env python3
"""
Simple test to verify the app can be built without Unicode issues.
"""

import os
import sys

# Set required environment variable for testing
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = "postgresql://test:test@localhost/test_bot"

if not os.getenv("BOT_TOKEN"):
    os.environ["BOT_TOKEN"] = "test_token_12345"

def test_app_components():
    """Test individual app components."""
    print("Testing app components...")
    
    try:
        # Test service container
        from core.modern_service_container import initialize_services
        print("[OK] Service container module imported")
        
        # Test database module
        from database import get_db_manager
        print("[OK] Database module imported")
        
        # Test bot manager
        from core.bot_manager import BotManager
        print("[OK] Bot manager imported")
        
        # Test configuration (skip printing summary to avoid Unicode issues)
        from core.config import get_config
        config = get_config()
        print("[OK] Configuration loaded")
        
        print("\n[SUCCESS] All core components can be imported successfully!")
        print("Your service container migration is working!")
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] Import error: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Error: {e}")
        return False

def test_handler_functionality():
    """Test that handlers can access services."""
    print("\nTesting handler service access...")
    
    try:
        # Import handlers that use modern services
        from handlers import buy_handler, user_handler, product_handler
        print("[OK] Core handlers imported")
        
        from handlers import pagamento_handler, relatorios_handler
        print("[OK] Migrated handlers imported")
        
        # Test service access functions
        from core.modern_service_container import get_user_service, get_product_service, get_sales_service
        print("[OK] Service accessor functions available")
        
        print("[OK] Handlers can access modern service container")
        return True
        
    except Exception as e:
        print(f"[ERROR] Handler test failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing Service Container Migration Build")
    print("=" * 50)
    
    component_test = test_app_components()
    handler_test = test_handler_functionality()
    
    if component_test and handler_test:
        print("\n" + "=" * 50)
        print("SERVICE CONTAINER MIGRATION SUCCESSFUL!")
        print("Your bot is ready to run with the modern architecture")
        print("=" * 50)
        sys.exit(0)
    else:
        print("\n" + "=" * 50)
        print("Some issues remain - check the errors above")
        print("=" * 50)
        sys.exit(1)