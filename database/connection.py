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
        """Initialize the connection pool with optimized settings."""
        try:
            # Parse URL into connection parameters to avoid encoding issues
            conn_params = self._parse_database_url(self.database_url)

            # Optimize connection parameters for performance
            connection_params = {
                # Connection timeouts
                'connect_timeout': 10,

                # Application identification
                'application_name': 'telegram_bot_expedition_system',

                # Performance optimizations
                'keepalives_idle': 600,  # 10 minutes
                'keepalives_interval': 30,
                'keepalives_count': 3,

                # Connection pooling optimizations
                'tcp_user_timeout': 30000,  # 30 seconds

                # Query execution timeout (30 seconds) - prevents hanging queries
                'options': '-c statement_timeout=30000',

                **conn_params
            }

            self.pool = psycopg2.pool.ThreadedConnectionPool(
                self.min_connections,
                self.max_connections,
                **connection_params
            )

            # Log detailed pool information
            logger.info(
                f"Database pool initialized: {self.min_connections}-{self.max_connections} connections "
                f"with optimized settings (keepalives, timeouts, prepared statements)"
            )

            # Test the connection pool
            self._test_pool()

        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise

    def _test_pool(self):
        """Test the connection pool functionality."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    result = cursor.fetchone()
                    if result[0] != 1:
                        raise Exception("Connection test failed")
            logger.debug("Database pool connection test successful")
        except Exception as e:
            logger.error(f"Database pool connection test failed: {e}")
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
    def get_connection(self, max_retries: int = 3):
        """
        Context manager for database connections with automatic retry on connection failures.
        Automatically handles connection acquisition, return, and error cleanup.

        Args:
            max_retries: Maximum number of connection retry attempts

        Usage:
            with db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM users")
                    return cur.fetchall()
        """
        connection = None
        retry_count = 0

        while retry_count <= max_retries:
            try:
                if not self.pool:
                    raise Exception("Database pool not initialized")

                connection = self.pool.getconn()
                if connection is None:
                    raise Exception("Unable to get connection from pool")

                # Test connection health with a simple query
                if connection.closed:
                    logger.warning("Got closed connection from pool, getting fresh connection...")
                    self.pool.putconn(connection, close=True)
                    connection = self.pool.getconn()

                # Additional health check - test with a simple query
                try:
                    with connection.cursor() as test_cursor:
                        test_cursor.execute("SELECT 1")
                        test_cursor.fetchone()
                except (psycopg2.OperationalError, psycopg2.InterfaceError) as test_error:
                    logger.warning(f"Connection health check failed: {test_error}")
                    self.pool.putconn(connection, close=True)
                    connection = None
                    raise test_error

                logger.debug("Database connection acquired and validated")
                yield connection
                break

            except (psycopg2.OperationalError, psycopg2.InterfaceError) as conn_error:
                retry_count += 1
                if retry_count <= max_retries:
                    logger.warning(f"Connection error (attempt {retry_count}/{max_retries + 1}): {conn_error}")
                    logger.info("Retrying with fresh connection...")

                    # Clean up failed connection
                    if connection:
                        try:
                            self.pool.putconn(connection, close=True)
                        except:
                            pass
                        connection = None

                    # Brief delay before retry
                    import time
                    time.sleep(0.1 * retry_count)
                    continue
                else:
                    logger.error(f"Database connection failed after {max_retries + 1} attempts: {conn_error}")
                    if connection:
                        try:
                            connection.rollback()
                        except:
                            pass
                    raise

            except psycopg2.Error as e:
                logger.error(f"Database error: {e}")
                if connection:
                    try:
                        connection.rollback()
                    except:
                        pass
                raise
            except Exception as e:
                logger.error(f"Unexpected database error: {e}")
                if connection:
                    try:
                        connection.rollback()
                    except:
                        pass
                raise
            finally:
                if connection:
                    try:
                        # Return connection to pool
                        self.pool.putconn(connection)
                        logger.debug("Database connection returned to pool")
                    except Exception as e:
                        logger.error(f"Error returning connection to pool: {e}")
    
    def execute_query(self, query: str, params: tuple = None, fetch: str = None, max_retries: int = 3):
        """
        Execute a query with automatic connection management and retry logic.

        Args:
            query: SQL query to execute
            params: Query parameters
            fetch: 'one', 'all', or None for no fetch
            max_retries: Maximum number of retry attempts

        Returns:
            Query results or None
        """
        with self.get_connection(max_retries=max_retries) as conn:
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
    
    def execute_many(self, query: str, params_list: list, max_retries: int = 3):
        """
        Execute query with multiple parameter sets and retry logic.

        Args:
            query: SQL query to execute
            params_list: List of parameter tuples
            max_retries: Maximum number of retry attempts

        Returns:
            Number of affected rows
        """
        with self.get_connection(max_retries=max_retries) as conn:
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

def initialize_database(database_url: str = None, min_connections: int = None, max_connections: int = None):
    """
    Initialize the global database manager with adaptive pool sizing.

    Args:
        database_url: PostgreSQL connection string (defaults to DATABASE_URL env var)
        min_connections: Minimum connections in pool (auto-determined if None)
        max_connections: Maximum connections in pool (auto-determined if None)
    """
    global _db_manager

    if database_url is None:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")

    # Adaptive connection pool sizing based on environment
    if min_connections is None or max_connections is None:
        environment = os.getenv("ENVIRONMENT", "development").lower()

        if environment == "production":
            # Production: Higher capacity for concurrent users
            default_min = 5
            default_max = 50
        elif environment == "staging":
            # Staging: Moderate capacity for testing
            default_min = 3
            default_max = 25
        else:
            # Development: Lower resource usage
            default_min = 1
            default_max = 10

        # Override with environment variables if available
        default_min = int(os.getenv("DB_MIN_CONNECTIONS", default_min))
        default_max = int(os.getenv("DB_MAX_CONNECTIONS", default_max))

        min_connections = min_connections or default_min
        max_connections = max_connections or default_max

    # Validate connection pool parameters
    if min_connections < 1:
        min_connections = 1
    if max_connections < min_connections:
        max_connections = min_connections * 2

    logger.info(f"Initializing database with adaptive pool sizing: {min_connections}-{max_connections} connections (environment: {os.getenv('ENVIRONMENT', 'development')})")

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