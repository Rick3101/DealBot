import os
import logging
import psycopg2
import psycopg2.pool
from contextlib import contextmanager
from typing import Optional
from urllib.parse import urlparse, quote_plus, urlunparse

logger = logging.getLogger(__name__)

class DatabaseManager:
    """
    Database connection manager with connection pooling for PostgreSQL.
    Handles connection lifecycle, error recovery, and proper resource cleanup.
    """
    
    def __init__(self, database_url: str, min_connections: int = 1, max_connections: int = 20):
        """
        Initialize database manager with connection pool.
        
        Args:
            database_url: PostgreSQL connection string
            min_connections: Minimum connections to maintain in pool
            max_connections: Maximum connections allowed in pool
        """
        self.database_url = database_url
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.pool: Optional[psycopg2.pool.ThreadedConnectionPool] = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the connection pool."""
        try:
            # Parse URL into connection parameters to avoid encoding issues
            conn_params = self._parse_database_url(self.database_url)
            
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                self.min_connections,
                self.max_connections,
                # Connection parameters for better reliability
                connect_timeout=10,
                application_name="telegram_bot",
                **conn_params
            )
            logger.info(f"Database pool initialized: {self.min_connections}-{self.max_connections} connections")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    def _parse_database_url(self, url: str) -> dict:
        """
        Parse database URL into connection parameters.
        
        Args:
            url: Database URL
            
        Returns:
            Dictionary of connection parameters
        """
        try:
            # Parse the URL
            parsed = urlparse(url)
            
            # Extract connection parameters
            conn_params = {
                'host': parsed.hostname,
                'port': parsed.port or 5432,
                'database': parsed.path.lstrip('/') if parsed.path else None,
                'user': parsed.username,
                'password': parsed.password
            }
            
            # Remove None values
            conn_params = {k: v for k, v in conn_params.items() if v is not None}
            
            logger.debug(f"Parsed database connection parameters for host: {conn_params.get('host', 'unknown')}")
            return conn_params
            
        except Exception as e:
            logger.error(f"Failed to parse database URL: {e}")
            # Fallback to using the URL string directly
            return {'dsn': url}
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        Automatically handles connection acquisition, return, and error cleanup.
        
        Usage:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM users")
                    return cur.fetchall()
        """
        connection = None
        try:
            if not self.pool:
                raise Exception("Database pool not initialized")
            
            connection = self.pool.getconn()
            if connection is None:
                raise Exception("Unable to get connection from pool")
            
            # Test connection health
            if connection.closed:
                logger.warning("Got closed connection from pool, reconnecting...")
                self.pool.putconn(connection, close=True)
                connection = self.pool.getconn()
            
            logger.debug("Database connection acquired")
            yield connection
            
        except psycopg2.Error as e:
            logger.error(f"Database error: {e}")
            if connection:
                connection.rollback()
            raise
        except Exception as e:
            logger.error(f"Unexpected database error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection:
                try:
                    # Return connection to pool
                    self.pool.putconn(connection)
                    logger.debug("Database connection returned to pool")
                except Exception as e:
                    logger.error(f"Error returning connection to pool: {e}")
    
    def execute_query(self, query: str, params: tuple = None, fetch: str = None):
        """
        Execute a query with automatic connection management.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: 'one', 'all', or None for no fetch
            
        Returns:
            Query results or None
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params or ())
                
                if fetch == 'one':
                    return cur.fetchone()
                elif fetch == 'all':
                    return cur.fetchall()
                elif fetch is None:
                    conn.commit()
                    return cur.rowcount
                else:
                    raise ValueError(f"Invalid fetch parameter: {fetch}")
    
    def execute_many(self, query: str, params_list: list):
        """
        Execute query with multiple parameter sets.
        
        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
            
        Returns:
            Number of affected rows
        """
        with self.get_connection() as conn:
            with conn.cursor() as cur:
                cur.executemany(query, params_list)
                conn.commit()
                return cur.rowcount
    
    def health_check(self) -> bool:
        """
        Check database health by executing a simple query.
        
        Returns:
            True if database is healthy, False otherwise
        """
        try:
            result = self.execute_query("SELECT 1", fetch='one')
            return result is not None and result[0] == 1
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
    
    def get_pool_status(self) -> dict:
        """
        Get current pool status information.
        
        Returns:
            Dictionary with pool statistics
        """
        if not self.pool:
            return {"status": "not_initialized"}
        
        return {
            "status": "active",
            "min_connections": self.min_connections,
            "max_connections": self.max_connections,
            "pool_size": len(self.pool._pool),
            "used_connections": len(self.pool._used)
        }
    
    def close_pool(self):
        """Close all connections in the pool."""
        if self.pool:
            self.pool.closeall()
            logger.info("Database pool closed")

# Global database manager instance
_db_manager: Optional[DatabaseManager] = None

def initialize_database(database_url: str = None, min_connections: int = 1, max_connections: int = 20):
    """
    Initialize the global database manager.
    
    Args:
        database_url: PostgreSQL connection string (defaults to DATABASE_URL env var)
        min_connections: Minimum connections in pool
        max_connections: Maximum connections in pool
    """
    global _db_manager
    
    if database_url is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
    
    _db_manager = DatabaseManager(database_url, min_connections, max_connections)
    logger.info("Global database manager initialized")

def get_db_manager() -> DatabaseManager:
    """
    Get the global database manager instance.
    
    Returns:
        DatabaseManager instance
        
    Raises:
        RuntimeError: If database manager not initialized
    """
    if _db_manager is None:
        raise RuntimeError("Database manager not initialized. Call initialize_database() first.")
    return _db_manager

def close_database():
    """Close the global database manager."""
    global _db_manager
    if _db_manager:
        _db_manager.close_pool()
        _db_manager = None
        logger.info("Global database manager closed")