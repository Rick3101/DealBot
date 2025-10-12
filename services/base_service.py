import logging
from typing import Optional, Dict, Any, Tuple, Callable
from functools import wraps
from database import get_db_manager
from utils.query_cache import get_query_cache


class BaseService:
    """
    Base service class that provides common functionality for all service layers.
    Handles database connections, logging, and error handling.
    Works with current synchronous setup.
    """
    
    def __init__(self):
        self.db_manager = self._get_or_initialize_db_manager()
        self.logger = logging.getLogger(self.__class__.__name__)
        self.query_cache = get_query_cache()

    def _get_or_initialize_db_manager(self) -> 'DatabaseManager':
        """Get database manager, initializing if necessary."""
        import logging
        logger = logging.getLogger(f"{self.__class__.__name__}.database_init")

        try:
            return get_db_manager()
        except RuntimeError as e:
            if "not initialized" in str(e):
                logger.warning("Database manager not initialized in BaseService, attempting to initialize...")
                try:
                    # Load environment variables if not already loaded
                    try:
                        from dotenv import load_dotenv
                        load_dotenv()
                    except ImportError:
                        pass

                    # Initialize database with environment URL
                    import os
                    database_url = os.environ.get('DATABASE_URL')
                    if not database_url:
                        raise RuntimeError("DATABASE_URL environment variable not set. Please check your .env file.")

                    from database import initialize_database
                    from database.schema import initialize_schema

                    initialize_database(database_url)
                    logger.info("Database initialized successfully in BaseService")

                    # Also initialize schema to ensure tables and columns exist
                    try:
                        initialize_schema()
                        logger.info("Database schema initialized successfully in BaseService")
                    except Exception as schema_error:
                        logger.warning(f"Schema initialization failed in BaseService: {schema_error}")
                        # Continue anyway, as basic database functionality might still work

                    return get_db_manager()
                except Exception as init_error:
                    logger.error(f"Failed to initialize database in BaseService: {init_error}")
                    raise RuntimeError(f"Database initialization failed: {init_error}")
            else:
                raise
    
    def _execute_query(self, query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = False) -> Optional[Any]:
        """
        Execute a database query with proper error handling.
        
        Args:
            query: SQL query to execute
            params: Query parameters
            fetch_one: Return single row
            fetch_all: Return all rows
            
        Returns:
            Query result or None
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(query, params)
                    
                    if fetch_one:
                        result = cursor.fetchone()
                        conn.commit()  # Commit even when fetching (for INSERT/UPDATE with RETURNING)
                        return result
                    elif fetch_all:
                        result = cursor.fetchall()
                        conn.commit()  # Commit even when fetching (for INSERT/UPDATE with RETURNING)
                        return result
                    else:
                        conn.commit()
                        return cursor.rowcount
                        
        except Exception as e:
            self.logger.error(f"Database query failed: {query} - Error: {e}", exc_info=True)
            raise ServiceError(f"Database operation failed: {str(e)}")

    def _execute_cached_query(self, query: str, params: tuple = (),
                            fetch_one: bool = False, fetch_all: bool = False,
                            cache_ttl: int = 300) -> Optional[Any]:
        """
        Execute a database query with caching support.

        Args:
            query: SQL query to execute
            params: Query parameters
            fetch_one: Return single row
            fetch_all: Return all rows
            cache_ttl: Cache time-to-live in seconds (default: 5 minutes)

        Returns:
            Query result (from cache or fresh execution)
        """
        # Only cache SELECT queries
        if not query.strip().upper().startswith('SELECT'):
            return self._execute_query(query, params, fetch_one, fetch_all)

        # Check cache first
        cached_result = self.query_cache.get(query, params)
        if cached_result is not None:
            return cached_result

        # Execute query
        result = self._execute_query(query, params, fetch_one, fetch_all)

        # Cache the result if it's not None
        if result is not None:
            self.query_cache.set(query, params, result, cache_ttl)

        return result

    def _invalidate_cache(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cached queries.

        Args:
            pattern: Pattern to match for selective invalidation

        Returns:
            Number of entries invalidated
        """
        return self.query_cache.invalidate(pattern)

    def _execute_transaction(self, operations: list) -> bool:
        """
        Execute multiple operations in a single transaction.
        
        Args:
            operations: List of (query, params) tuples
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    for query, params in operations:
                        cursor.execute(query, params)
                    conn.commit()
                    return True
                    
        except Exception as e:
            self.logger.error(f"Transaction failed: {e}", exc_info=True)
            raise ServiceError(f"Transaction failed: {str(e)}")
    
    def _log_operation(self, operation: str, **kwargs):
        """Log service operations with context."""
        context = " ".join([f"{k}={v}" for k, v in kwargs.items()])
        self.logger.info(f"{operation} - {context}")


class ServiceError(Exception):
    """Custom exception for service layer errors."""
    pass


class ValidationError(ServiceError):
    """Exception for validation errors."""
    pass


class NotFoundError(ServiceError):
    """Exception for when requested resource is not found."""
    pass


class DuplicateError(ServiceError):
    """Exception for duplicate resource errors."""
    pass


def service_operation(operation_name: str):
    """
    Decorator for standardized service operation error handling.

    Automatically handles exceptions and provides consistent error logging.
    Re-raises domain exceptions (ValidationError, NotFoundError, DuplicateError) as-is.
    Wraps other exceptions in ServiceError.

    Args:
        operation_name: Human-readable operation name for logging

    Usage:
        @service_operation("create_user")
        def create_user(self, request):
            # Implementation without try-except
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except (ValidationError, NotFoundError, DuplicateError):
                # Re-raise domain exceptions as-is
                raise
            except Exception as e:
                # Log and wrap other exceptions
                if hasattr(self, 'logger'):
                    self.logger.error(f"Error in {operation_name}: {e}", exc_info=True)
                raise ServiceError(f"{operation_name} failed: {str(e)}")
        return wrapper
    return decorator