#!/usr/bin/env python3
"""
Integration tests for database connection manager.
Tests database connection pooling and basic operations.
"""

import os
import pytest
from database import initialize_database, get_db_manager


@pytest.mark.integration
def test_database_initialization():
    """Test database connection and basic operations."""
    
    # Check if DATABASE_URL is set
    if not os.getenv('DATABASE_URL'):
        print("ERROR: DATABASE_URL environment variable not set!")
        print("Please set it with your PostgreSQL connection string:")
        print("export DATABASE_URL='postgresql://user:password@host:port/database'")
        return False
    
    try:
        # Import database components
        from database import initialize_database, get_db_manager
        
        # Initialize database
        print("Initializing database...")
        initialize_database()
        print("SUCCESS: Database manager initialized")
        
        # Get database manager
        db_manager = get_db_manager()
        
        # Test basic connection
        print("Testing database connection...")
        healthy = db_manager.health_check()
        if healthy:
            print("SUCCESS: Database connection healthy")
        else:
            print("ERROR: Database connection failed")
            return False
        
        # Test pool status
        print("Checking pool status...")
        pool_status = db_manager.get_pool_status()
        print(f"Pool Status: {pool_status}")
        
        # Test query execution
        print("Testing query execution...")
        result = db_manager.execute_query("SELECT 1 as test", fetch='one')
        if result and result[0] == 1:
            print("SUCCESS: Query execution successful")
        else:
            print("ERROR: Query execution failed")
            return False
        
        # Test database initialization
        print("Testing database table initialization...")
        from database.schema import initialize_schema
        initialize_schema()
        print("SUCCESS: Database tables initialized")
        
        # Test connection context manager
        print("Testing connection context manager...")
        with db_manager.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                version = cur.fetchone()[0]
                print(f"SUCCESS: PostgreSQL Version: {version[:50]}...")
        
        print("\nAll database tests passed!")
        return True
        
    except Exception as e:
        print(f"ERROR: Database test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database()
    sys.exit(0 if success else 1)