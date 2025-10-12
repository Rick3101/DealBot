from typing import Optional, List, Dict, Any, Tuple, Union, Type, TypeVar
from services.base_service import BaseService, ServiceError, ValidationError, NotFoundError, DuplicateError

T = TypeVar('T')


class BaseRepository(BaseService):
    """
    Generic repository for common CRUD operations.
    Reduces code duplication across services by providing standardized database operations.
    """

    def __init__(self, table_name: str, model_class: Type[T], primary_key: str = "id"):
        """
        Initialize repository with table and model configuration.

        Args:
            table_name: Database table name
            model_class: Model class with from_db_row method
            primary_key: Primary key column name (default: "id")
        """
        super().__init__()
        self.table_name = table_name
        self.model_class = model_class
        self.primary_key = primary_key

        # Define default column mappings (can be overridden by subclasses)
        self._column_mappings = self._get_default_columns()

    def _get_default_columns(self) -> List[str]:
        """
        Get default columns for the table.
        Override in subclasses to customize column selection.

        Returns:
            List of column names
        """
        # Default columns - subclasses should override this
        return [self.primary_key]

    def _build_select_query(self, columns: Optional[List[str]] = None,
                           where_clause: Optional[str] = None,
                           order_by: Optional[str] = None,
                           limit: Optional[int] = None) -> str:
        """
        Build SELECT query with optional clauses.

        Args:
            columns: Columns to select (default: all mapped columns)
            where_clause: WHERE clause without the WHERE keyword
            order_by: ORDER BY clause without the ORDER BY keyword
            limit: LIMIT value

        Returns:
            Complete SQL query string
        """
        cols = columns or self._column_mappings
        query = f"SELECT {', '.join(cols)} FROM {self.table_name}"

        if where_clause:
            query += f" WHERE {where_clause}"

        if order_by:
            query += f" ORDER BY {order_by}"

        if limit:
            query += f" LIMIT {limit}"

        return query

    def get_by_id(self, entity_id: Union[int, str]) -> Optional[T]:
        """
        Get entity by primary key.

        Args:
            entity_id: Primary key value

        Returns:
            Entity object if found, None otherwise
        """
        query = self._build_select_query(where_clause=f"{self.primary_key} = %s")
        row = self._execute_query(query, (entity_id,), fetch_one=True)

        if row and hasattr(self.model_class, 'from_db_row'):
            return self.model_class.from_db_row(row)

        return None

    def get_all(self, order_by: Optional[str] = None, limit: Optional[int] = None) -> List[T]:
        """
        Get all entities from the table.

        Args:
            order_by: ORDER BY clause (e.g., "name ASC")
            limit: Maximum number of records to return

        Returns:
            List of entity objects
        """
        query = self._build_select_query(order_by=order_by, limit=limit)
        rows = self._execute_query(query, fetch_all=True)

        entities = []
        if rows and hasattr(self.model_class, 'from_db_row'):
            for row in rows:
                entity = self.model_class.from_db_row(row)
                if entity:
                    entities.append(entity)

        self._log_operation(f"get_all_{self.table_name}", count=len(entities))
        return entities

    def get_by_field(self, field_name: str, value: Any,
                     order_by: Optional[str] = None,
                     limit: Optional[int] = None) -> List[T]:
        """
        Get entities by a specific field value.

        Args:
            field_name: Column name to search
            value: Value to search for
            order_by: ORDER BY clause
            limit: Maximum number of records

        Returns:
            List of matching entities
        """
        query = self._build_select_query(
            where_clause=f"{field_name} = %s",
            order_by=order_by,
            limit=limit
        )
        rows = self._execute_query(query, (value,), fetch_all=True)

        entities = []
        if rows and hasattr(self.model_class, 'from_db_row'):
            for row in rows:
                entity = self.model_class.from_db_row(row)
                if entity:
                    entities.append(entity)

        return entities

    def get_one_by_field(self, field_name: str, value: Any) -> Optional[T]:
        """
        Get single entity by field value.

        Args:
            field_name: Column name to search
            value: Value to search for

        Returns:
            Entity object if found, None otherwise
        """
        results = self.get_by_field(field_name, value, limit=1)
        return results[0] if results else None

    def exists(self, field_name: str, value: Any, exclude_id: Optional[Union[int, str]] = None) -> bool:
        """
        Check if entity exists with given field value.

        Args:
            field_name: Column name to check
            value: Value to check for
            exclude_id: Exclude entity with this ID (for update operations)

        Returns:
            True if entity exists, False otherwise
        """
        where_clause = f"{field_name} = %s"
        params = [value]

        if exclude_id is not None:
            where_clause += f" AND {self.primary_key} != %s"
            params.append(exclude_id)

        query = f"SELECT 1 FROM {self.table_name} WHERE {where_clause} LIMIT 1"
        result = self._execute_query(query, tuple(params), fetch_one=True)

        return result is not None

    def count(self, where_clause: Optional[str] = None, params: Tuple = ()) -> int:
        """
        Count entities in the table.

        Args:
            where_clause: WHERE clause without the WHERE keyword
            params: Parameters for the WHERE clause

        Returns:
            Number of matching entities
        """
        query = f"SELECT COUNT(*) FROM {self.table_name}"

        if where_clause:
            query += f" WHERE {where_clause}"

        row = self._execute_query(query, params, fetch_one=True)
        return row[0] if row else 0

    def create(self, data: Dict[str, Any], returning_columns: Optional[List[str]] = None) -> Optional[T]:
        """
        Create new entity.

        Args:
            data: Dictionary of column names and values
            returning_columns: Columns to return (default: all mapped columns)

        Returns:
            Created entity object if successful

        Raises:
            ServiceError: If creation fails
        """
        if not data:
            raise ValidationError("No data provided for creation")

        columns = list(data.keys())
        placeholders = ["%s"] * len(columns)
        values = list(data.values())

        query = f"INSERT INTO {self.table_name} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

        # Add RETURNING clause if supported
        return_cols = returning_columns or self._column_mappings
        if return_cols:
            query += f" RETURNING {', '.join(return_cols)}"

            row = self._execute_query(query, tuple(values), fetch_one=True)
            if row and hasattr(self.model_class, 'from_db_row'):
                entity = self.model_class.from_db_row(row)
                self._log_operation(f"create_{self.table_name}", entity_id=getattr(entity, self.primary_key, None))
                return entity
        else:
            # Fallback for databases that don't support RETURNING
            result = self._execute_query(query, tuple(values))
            if result:
                self._log_operation(f"create_{self.table_name}", affected_rows=result)
                return True

        return None

    def update(self, entity_id: Union[int, str], data: Dict[str, Any],
               returning_columns: Optional[List[str]] = None) -> Optional[T]:
        """
        Update entity by ID.

        Args:
            entity_id: Primary key value
            data: Dictionary of column names and new values
            returning_columns: Columns to return (default: all mapped columns)

        Returns:
            Updated entity object if successful

        Raises:
            ServiceError: If update fails
            NotFoundError: If entity doesn't exist
        """
        if not data:
            raise ValidationError("No data provided for update")

        # Check if entity exists
        if not self.exists(self.primary_key, entity_id):
            raise NotFoundError(f"{self.table_name} with {self.primary_key}={entity_id} not found")

        set_clauses = [f"{col} = %s" for col in data.keys()]
        values = list(data.values()) + [entity_id]

        query = f"UPDATE {self.table_name} SET {', '.join(set_clauses)} WHERE {self.primary_key} = %s"

        # Add RETURNING clause if supported
        return_cols = returning_columns or self._column_mappings
        if return_cols:
            query += f" RETURNING {', '.join(return_cols)}"

            row = self._execute_query(query, tuple(values), fetch_one=True)
            if row and hasattr(self.model_class, 'from_db_row'):
                entity = self.model_class.from_db_row(row)
                self._log_operation(f"update_{self.table_name}", entity_id=entity_id)
                return entity
        else:
            # Fallback for databases that don't support RETURNING
            result = self._execute_query(query, tuple(values))
            if result:
                self._log_operation(f"update_{self.table_name}", entity_id=entity_id, affected_rows=result)
                return self.get_by_id(entity_id)

        return None

    def delete(self, entity_id: Union[int, str]) -> bool:
        """
        Delete entity by ID.

        Args:
            entity_id: Primary key value

        Returns:
            True if deleted successfully, False otherwise

        Raises:
            NotFoundError: If entity doesn't exist
        """
        # Check if entity exists
        if not self.exists(self.primary_key, entity_id):
            raise NotFoundError(f"{self.table_name} with {self.primary_key}={entity_id} not found")

        query = f"DELETE FROM {self.table_name} WHERE {self.primary_key} = %s"
        result = self._execute_query(query, (entity_id,))

        success = result > 0
        if success:
            self._log_operation(f"delete_{self.table_name}", entity_id=entity_id)

        return success

    def delete_by_field(self, field_name: str, value: Any) -> int:
        """
        Delete entities by field value.

        Args:
            field_name: Column name
            value: Value to match

        Returns:
            Number of entities deleted
        """
        query = f"DELETE FROM {self.table_name} WHERE {field_name} = %s"
        result = self._execute_query(query, (value,))

        count = result if result else 0
        if count > 0:
            self._log_operation(f"delete_by_field_{self.table_name}", field=field_name, value=value, count=count)

        return count

    def execute_custom_query(self, query: str, params: Tuple = (),
                           fetch_one: bool = False, fetch_all: bool = False) -> Any:
        """
        Execute custom query on this repository's table.
        Use with caution - prefer the standard CRUD methods when possible.

        Args:
            query: SQL query to execute
            params: Query parameters
            fetch_one: Return single row
            fetch_all: Return all rows

        Returns:
            Query result
        """
        self._log_operation(f"custom_query_{self.table_name}", query_type=query.split()[0].upper())
        return self._execute_query(query, params, fetch_one, fetch_all)