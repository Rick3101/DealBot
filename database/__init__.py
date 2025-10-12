from .connection import DatabaseManager, get_db_manager, initialize_database, close_database

# Alias for backward compatibility
get_database_manager = get_db_manager

__all__ = ['DatabaseManager', 'get_db_manager', 'get_database_manager', 'initialize_database', 'close_database']