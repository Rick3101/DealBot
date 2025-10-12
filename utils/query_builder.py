"""
Advanced query building utilities for dynamic SQL generation.
Provides safe, parameterized query construction for complex database operations.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import logging
from enum import Enum


class JoinType(Enum):
    """Supported SQL join types."""
    INNER = "INNER JOIN"
    LEFT = "LEFT JOIN"
    RIGHT = "RIGHT JOIN"
    FULL = "FULL OUTER JOIN"


class OrderDirection(Enum):
    """Supported ordering directions."""
    ASC = "ASC"
    DESC = "DESC"


class QueryBuilder:
    """
    Advanced query building utilities for complex SQL generation.
    Provides safe, parameterized query construction with validation.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def build_filtered_query(self, base_query: str, filters: Dict[str, Any]) -> Tuple[str, List]:
        """
        Build filtered queries with proper parameterization.

        Args:
            base_query: Base SQL query (should contain '{where_clause}' placeholder)
            filters: Dictionary of filter conditions

        Returns:
            Tuple of (complete_query, parameters)
        """
        where_conditions = []
        parameters = []

        for field, value in filters.items():
            if value is None:
                continue

            # Handle different filter types
            if isinstance(value, dict):
                # Range filters like {'from': date1, 'to': date2}
                if 'from' in value and value['from'] is not None:
                    where_conditions.append(f"{field} >= %s")
                    parameters.append(value['from'])
                if 'to' in value and value['to'] is not None:
                    where_conditions.append(f"{field} <= %s")
                    parameters.append(value['to'])
            elif isinstance(value, list):
                # IN clause for multiple values
                if value:  # Only add if list is not empty
                    placeholders = ','.join(['%s'] * len(value))
                    where_conditions.append(f"{field} IN ({placeholders})")
                    parameters.extend(value)
            elif isinstance(value, str) and value.startswith('%') and value.endswith('%'):
                # LIKE pattern
                where_conditions.append(f"{field} LIKE %s")
                parameters.append(value)
            else:
                # Exact match
                where_conditions.append(f"{field} = %s")
                parameters.append(value)

        # Build WHERE clause
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"

        # Replace placeholder in base query
        if '{where_clause}' in base_query:
            complete_query = base_query.replace('{where_clause}', where_clause)
        else:
            # If no placeholder, append WHERE clause
            complete_query = f"{base_query} WHERE {where_clause}"

        self.logger.debug(f"Built filtered query with {len(where_conditions)} conditions")
        return complete_query, parameters

    def build_aggregation_query(self, table: str, aggregations: List[str],
                              group_by: List[str], where_clause: Optional[str] = None) -> str:
        """
        Build aggregation queries for analytics.

        Args:
            table: Table name
            aggregations: List of aggregation expressions (e.g., "SUM(amount)", "COUNT(*)")
            group_by: List of columns to group by
            where_clause: Optional WHERE clause

        Returns:
            Complete SQL query string
        """
        # Validate inputs
        if not aggregations:
            raise ValueError("At least one aggregation must be specified")

        # Build SELECT clause
        select_parts = []
        if group_by:
            select_parts.extend(group_by)
        select_parts.extend(aggregations)

        select_clause = ", ".join(select_parts)

        # Build base query
        query = f"SELECT {select_clause} FROM {table}"

        # Add WHERE clause if provided
        if where_clause:
            query += f" WHERE {where_clause}"

        # Add GROUP BY if specified
        if group_by:
            group_clause = ", ".join(group_by)
            query += f" GROUP BY {group_clause}"

        self.logger.debug(f"Built aggregation query for table {table}")
        return query

    def build_join_query(self, base_table: str, joins: List[Dict[str, str]],
                        columns: Optional[List[str]] = None) -> str:
        """
        Build complex join queries.

        Args:
            base_table: Primary table name
            joins: List of join configurations with keys: 'table', 'on', 'type' (optional)
            columns: Columns to select (default: *)

        Returns:
            Complete SQL query string
        """
        # Default columns
        select_columns = ", ".join(columns) if columns else "*"

        # Start with base query
        query = f"SELECT {select_columns} FROM {base_table}"

        # Add joins
        for join_config in joins:
            if 'table' not in join_config or 'on' not in join_config:
                raise ValueError("Each join must specify 'table' and 'on' conditions")

            join_type = join_config.get('type', JoinType.INNER.value)
            table_name = join_config['table']
            join_condition = join_config['on']

            query += f" {join_type} {table_name} ON {join_condition}"

        self.logger.debug(f"Built join query with {len(joins)} joins")
        return query

    def build_pagination_query(self, base_query: str, page: int = 1,
                             page_size: int = 20, order_by: Optional[str] = None) -> Tuple[str, List]:
        """
        Add pagination to a query.

        Args:
            base_query: Base SQL query
            page: Page number (1-based)
            page_size: Number of records per page
            order_by: ORDER BY clause

        Returns:
            Tuple of (paginated_query, parameters)
        """
        if page < 1:
            page = 1
        if page_size < 1:
            page_size = 20

        # Calculate offset
        offset = (page - 1) * page_size

        # Add ORDER BY if specified
        query = base_query
        if order_by:
            query += f" ORDER BY {order_by}"

        # Add LIMIT and OFFSET
        query += " LIMIT %s OFFSET %s"
        parameters = [page_size, offset]

        self.logger.debug(f"Built pagination query: page {page}, size {page_size}")
        return query, parameters

    def build_search_query(self, table: str, search_fields: List[str],
                          search_term: str, additional_conditions: Optional[str] = None) -> Tuple[str, List]:
        """
        Build full-text search query across multiple fields.

        Args:
            table: Table name
            search_fields: List of fields to search
            search_term: Search term
            additional_conditions: Additional WHERE conditions

        Returns:
            Tuple of (search_query, parameters)
        """
        if not search_fields:
            raise ValueError("At least one search field must be specified")

        # Build search conditions (case-insensitive LIKE)
        search_conditions = []
        parameters = []

        search_pattern = f"%{search_term}%"
        for field in search_fields:
            search_conditions.append(f"LOWER({field}) LIKE LOWER(%s)")
            parameters.append(search_pattern)

        # Combine with OR
        search_clause = " OR ".join(search_conditions)

        # Build complete WHERE clause
        where_parts = [f"({search_clause})"]
        if additional_conditions:
            where_parts.append(additional_conditions)

        where_clause = " AND ".join(where_parts)

        # Build complete query
        query = f"SELECT * FROM {table} WHERE {where_clause}"

        self.logger.debug(f"Built search query for term '{search_term}' across {len(search_fields)} fields")
        return query, parameters

    def build_count_query(self, base_query: str) -> str:
        """
        Convert a SELECT query to a COUNT query.

        Args:
            base_query: Original SELECT query

        Returns:
            COUNT query string
        """
        # Remove ORDER BY clause if present (not needed for count)
        query = base_query
        order_by_index = query.upper().rfind("ORDER BY")
        if order_by_index != -1:
            query = query[:order_by_index].strip()

        # Wrap in COUNT subquery
        count_query = f"SELECT COUNT(*) FROM ({query}) AS count_subquery"

        self.logger.debug("Built count query from base query")
        return count_query

    def build_date_range_filter(self, date_field: str, start_date: Optional[Any] = None,
                               end_date: Optional[Any] = None) -> Tuple[str, List]:
        """
        Build date range filter conditions.

        Args:
            date_field: Date column name
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Tuple of (where_condition, parameters)
        """
        conditions = []
        parameters = []

        if start_date is not None:
            conditions.append(f"{date_field} >= %s")
            parameters.append(start_date)

        if end_date is not None:
            conditions.append(f"{date_field} <= %s")
            parameters.append(end_date)

        if not conditions:
            return "1=1", []

        where_condition = " AND ".join(conditions)
        self.logger.debug(f"Built date range filter for {date_field}")
        return where_condition, parameters

    def build_dynamic_insert(self, table: str, data: Dict[str, Any],
                           returning_columns: Optional[List[str]] = None) -> Tuple[str, List]:
        """
        Build dynamic INSERT query from data dictionary.

        Args:
            table: Table name
            data: Dictionary of column names and values
            returning_columns: Columns to return (PostgreSQL)

        Returns:
            Tuple of (insert_query, parameters)
        """
        if not data:
            raise ValueError("Data dictionary cannot be empty")

        columns = list(data.keys())
        placeholders = ["%s"] * len(columns)
        values = list(data.values())

        query = f"INSERT INTO {table} ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

        # Add RETURNING clause if specified (PostgreSQL feature)
        if returning_columns:
            return_clause = ", ".join(returning_columns)
            query += f" RETURNING {return_clause}"

        self.logger.debug(f"Built dynamic insert query for {table} with {len(columns)} columns")
        return query, values

    def build_dynamic_update(self, table: str, data: Dict[str, Any],
                           where_conditions: Dict[str, Any],
                           returning_columns: Optional[List[str]] = None) -> Tuple[str, List]:
        """
        Build dynamic UPDATE query from data dictionary.

        Args:
            table: Table name
            data: Dictionary of column names and new values
            where_conditions: Dictionary of WHERE conditions
            returning_columns: Columns to return (PostgreSQL)

        Returns:
            Tuple of (update_query, parameters)
        """
        if not data:
            raise ValueError("Data dictionary cannot be empty")
        if not where_conditions:
            raise ValueError("WHERE conditions cannot be empty")

        # Build SET clause
        set_clauses = [f"{col} = %s" for col in data.keys()]
        set_clause = ", ".join(set_clauses)

        # Build WHERE clause
        where_clauses = [f"{col} = %s" for col in where_conditions.keys()]
        where_clause = " AND ".join(where_clauses)

        # Combine parameters
        parameters = list(data.values()) + list(where_conditions.values())

        query = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"

        # Add RETURNING clause if specified
        if returning_columns:
            return_clause = ", ".join(returning_columns)
            query += f" RETURNING {return_clause}"

        self.logger.debug(f"Built dynamic update query for {table}")
        return query, parameters

    def validate_column_name(self, column_name: str) -> bool:
        """
        Validate column name to prevent SQL injection.

        Args:
            column_name: Column name to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation: alphanumeric, underscore, and dots (for table.column)
        import re
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)?$'
        return bool(re.match(pattern, column_name))

    def validate_table_name(self, table_name: str) -> bool:
        """
        Validate table name to prevent SQL injection.

        Args:
            table_name: Table name to validate

        Returns:
            True if valid, False otherwise
        """
        import re
        pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*$'
        return bool(re.match(pattern, table_name))

    def escape_identifier(self, identifier: str) -> str:
        """
        Escape SQL identifier (table/column name) for safe usage.

        Args:
            identifier: Identifier to escape

        Returns:
            Escaped identifier
        """
        # Remove any existing quotes and add double quotes
        clean_identifier = identifier.replace('"', '""')
        return f'"{clean_identifier}"'


# Global query builder instance
_query_builder = QueryBuilder()


def get_query_builder() -> QueryBuilder:
    """Get global query builder instance."""
    return _query_builder