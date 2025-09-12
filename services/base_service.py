import logging
from typing import Optional, Dict, Any
from database import get_db_manager


class BaseService:
    """
    Base service class that provides common functionality for all service layers.
    Handles database connections, logging, and error handling.
    Works with current synchronous setup.
    """
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self.logger = logging.getLogger(self.__class__.__name__)
    
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