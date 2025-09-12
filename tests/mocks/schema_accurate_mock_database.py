"""
Schema-accurate mock database that mirrors the real PostgreSQL schema exactly.
This ensures tests catch schema mismatches before runtime.
"""

from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timezone
import re
import psycopg2
from contextlib import contextmanager


class SchemaAccurateMockConnection:
    """Mock connection that validates SQL queries against the real schema."""
    
    # Real database schema definition matching database/schema.py exactly
    SCHEMA = {
        'usuarios': {
            'id': {'type': 'SERIAL', 'primary_key': True},
            'username': {'type': 'VARCHAR(50)', 'unique': True, 'not_null': True},
            'password': {'type': 'VARCHAR(255)', 'not_null': True},
            'nivel': {'type': 'VARCHAR(20)', 'default': 'user'},
            'chat_id': {'type': 'BIGINT'}
        },
        'produtos': {
            'id': {'type': 'SERIAL', 'primary_key': True},
            'nome': {'type': 'VARCHAR(100)', 'not_null': True},
            'emoji': {'type': 'VARCHAR(10)'},
            'media_file_id': {'type': 'VARCHAR(255)'}
        },
        'vendas': {
            'id': {'type': 'SERIAL', 'primary_key': True},
            'comprador': {'type': 'VARCHAR(100)', 'not_null': True},
            'data_venda': {'type': 'TIMESTAMP', 'default': 'CURRENT_TIMESTAMP'}
        },
        'itensvenda': {
            'id': {'type': 'SERIAL', 'primary_key': True},
            'venda_id': {'type': 'INTEGER', 'references': 'vendas(id)'},
            'produto_id': {'type': 'INTEGER', 'references': 'produtos(id)'},
            'quantidade': {'type': 'INTEGER', 'not_null': True},
            'valor_unitario': {'type': 'DECIMAL(10,2)', 'not_null': True},
            'produto_nome': {'type': 'VARCHAR(100)', 'not_null': True}
        },
        'estoque': {
            'id': {'type': 'SERIAL', 'primary_key': True},
            'produto_id': {'type': 'INTEGER', 'references': 'produtos(id)'},
            'quantidade': {'type': 'INTEGER', 'not_null': True},
            'preco': {'type': 'DECIMAL(10,2)', 'not_null': True},
            'custo': {'type': 'DECIMAL(10,2)'},
            'data_adicao': {'type': 'TIMESTAMP', 'default': 'CURRENT_TIMESTAMP'},
            'quantidade_restante': {'type': 'INTEGER', 'not_null': True, 'default': 0}
        },
        'pagamentos': {
            'id': {'type': 'SERIAL', 'primary_key': True},
            'venda_id': {'type': 'INTEGER', 'references': 'vendas(id)'},
            'valor_pago': {'type': 'DECIMAL(10,2)', 'not_null': True},
            'data_pagamento': {'type': 'TIMESTAMP', 'default': 'CURRENT_TIMESTAMP'}
        },
        'smartcontracts': {
            'id': {'type': 'SERIAL', 'primary_key': True},
            'codigo': {'type': 'VARCHAR(100)', 'unique': True, 'not_null': True},
            'criador_chat_id': {'type': 'BIGINT', 'not_null': True},
            'data_criacao': {'type': 'TIMESTAMP', 'default': 'CURRENT_TIMESTAMP'},
            'ativo': {'type': 'BOOLEAN', 'default': True}
        },
        'transacoes': {
            'id': {'type': 'SERIAL', 'primary_key': True},
            'contract_id': {'type': 'INTEGER', 'references': 'smartcontracts(id)'},
            'descricao': {'type': 'TEXT', 'not_null': True},
            'chat_id': {'type': 'BIGINT', 'not_null': True},
            'data_transacao': {'type': 'TIMESTAMP', 'default': 'CURRENT_TIMESTAMP'},
            'confirmado': {'type': 'BOOLEAN', 'default': False}
        },
        'configuracoes': {
            'id': {'type': 'SERIAL', 'primary_key': True},
            'chave': {'type': 'VARCHAR(100)', 'unique': True, 'not_null': True},
            'valor': {'type': 'TEXT'},
            'descricao': {'type': 'TEXT'},
            'data_atualizacao': {'type': 'TIMESTAMP', 'default': 'CURRENT_TIMESTAMP'}
        }
    }
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.data = db_manager.data
        self.counters = db_manager.counters
        self.in_transaction = False
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def cursor(self):
        """Return a schema-validating cursor."""
        return SchemaAccurateMockCursor(self)
    
    def commit(self):
        """Mock commit."""
        pass
    
    def rollback(self):
        """Mock rollback."""
        pass


class SchemaAccurateMockCursor:
    """Mock cursor that validates SQL against schema and simulates real database behavior."""
    
    def __init__(self, connection):
        self.connection = connection
        self.data = connection.data
        self.counters = connection.counters
        self.last_result = None
    
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
    
    def execute(self, query: str, params: Tuple = None):
        """Execute SQL with schema validation."""
        if params is None:
            params = ()
            
        # Validate query against schema
        self._validate_query_schema(query)
        
        # Execute the query
        self.last_result = self._execute_query(query, params)
        
    def fetchone(self):
        """Fetch one result."""
        if self.last_result and isinstance(self.last_result, list) and self.last_result:
            return self.last_result[0]
        return self.last_result
    
    def fetchall(self):
        """Fetch all results."""
        if isinstance(self.last_result, list):
            return self.last_result
        elif self.last_result:
            return [self.last_result]
        return []
    
    def _validate_query_schema(self, query: str):
        """Validate SQL query against the known schema."""
        query_upper = query.upper()
        
        # Extract table and column references
        tables_referenced = self._extract_tables_from_query(query)
        
        for table_name in tables_referenced:
            table_lower = table_name.lower()
            if table_lower not in self.connection.SCHEMA:
                raise psycopg2.ProgrammingError(f'relation "{table_name}" does not exist')
            
            # Extract columns referenced for this table
            columns_referenced = self._extract_columns_from_query(query, table_name)
            schema_columns = set(self.connection.SCHEMA[table_lower].keys())
            
            for column in columns_referenced:
                if column.lower() not in schema_columns:
                    raise psycopg2.ProgrammingError(
                        f'column "{column}" does not exist\n'
                        f'LINE 1: ...{column}...'
                    )
    
    def _extract_tables_from_query(self, query: str) -> List[str]:
        """Extract table names referenced in SQL query."""
        tables = []
        
        # Extract from INSERT INTO
        insert_match = re.search(r'INSERT\s+INTO\s+(\w+)', query, re.IGNORECASE)
        if insert_match:
            tables.append(insert_match.group(1))
        
        # Extract from UPDATE
        update_match = re.search(r'UPDATE\s+(\w+)', query, re.IGNORECASE)
        if update_match:
            tables.append(update_match.group(1))
        
        # Extract from FROM
        from_matches = re.findall(r'FROM\s+(\w+)', query, re.IGNORECASE)
        tables.extend(from_matches)
        
        # Extract from JOIN
        join_matches = re.findall(r'JOIN\s+(\w+)', query, re.IGNORECASE)
        tables.extend(join_matches)
        
        return tables
    
    def _extract_columns_from_query(self, query: str, table_name: str) -> List[str]:
        """Extract column names referenced for a specific table."""
        columns = []
        
        # Extract from INSERT column list
        insert_pattern = rf'INSERT\s+INTO\s+{re.escape(table_name)}\s*\(([^)]+)\)'
        insert_match = re.search(insert_pattern, query, re.IGNORECASE)
        if insert_match:
            column_list = insert_match.group(1)
            columns.extend([col.strip() for col in column_list.split(',')])
        
        # Extract from RETURNING clause
        returning_pattern = r'RETURNING\s+([^;$]+)'
        returning_match = re.search(returning_pattern, query, re.IGNORECASE)
        if returning_match:
            returning_list = returning_match.group(1)
            # Handle table.column and plain column references
            for col in returning_list.split(','):
                col = col.strip()
                if '.' in col:
                    table_part, col_part = col.split('.', 1)
                    if table_part.lower() == table_name.lower():
                        columns.append(col_part)
                else:
                    columns.append(col)
        
        # Extract from SELECT clause
        if 'SELECT' in query.upper():
            # Look for table.column references
            table_col_pattern = rf'{re.escape(table_name)}\.(\w+)'
            table_col_matches = re.findall(table_col_pattern, query, re.IGNORECASE)
            columns.extend(table_col_matches)
        
        return columns
    
    def _execute_query(self, query: str, params: Tuple):
        """Execute the validated query and return mock results."""
        query_upper = query.upper().strip()
        
        if query_upper.startswith('INSERT'):
            return self._handle_insert(query, params)
        elif query_upper.startswith('SELECT'):
            return self._handle_select(query, params)
        elif query_upper.startswith('UPDATE'):
            return self._handle_update(query, params)
        elif query_upper.startswith('DELETE'):
            return self._handle_delete(query, params)
        else:
            return None
    
    def _handle_insert(self, query: str, params: Tuple):
        """Handle INSERT queries with schema-accurate results."""
        # Extract table name
        table_match = re.search(r'INSERT\s+INTO\s+(\w+)', query, re.IGNORECASE)
        if not table_match:
            return None
            
        table_name = table_match.group(1).lower()
        
        # Generate new ID
        new_id = self.counters.get(table_name, 1)
        self.counters[table_name] = new_id + 1
        
        # Create record based on schema
        record = {'id': new_id}
        
        # Handle specific table inserts with proper column mapping
        if table_name == 'vendas':
            record.update({
                'comprador': params[0] if params else 'test_buyer',
                'data_venda': datetime.now(timezone.utc)
            })
        elif table_name == 'produtos':
            record.update({
                'nome': params[0] if params else 'test_product',
                'emoji': params[1] if len(params) > 1 else '📦',
                'media_file_id': params[2] if len(params) > 2 else None
            })
        elif table_name == 'usuarios':
            record.update({
                'username': params[0] if params else 'test_user',
                'password': params[1] if len(params) > 1 else 'test_pass',
                'nivel': params[2] if len(params) > 2 else 'user',
                'chat_id': params[3] if len(params) > 3 else None
            })
        elif table_name == 'itensvenda':
            record.update({
                'venda_id': params[0] if params else 1,
                'produto_id': params[1] if len(params) > 1 else 1,
                'quantidade': params[2] if len(params) > 2 else 1,
                'valor_unitario': params[3] if len(params) > 3 else 10.0,
                'produto_nome': 'test_product'
            })
        elif table_name == 'estoque':
            record.update({
                'produto_id': params[0] if params else 1,
                'quantidade': params[1] if len(params) > 1 else 10,
                'preco': params[2] if len(params) > 2 else 15.0,
                'custo': params[3] if len(params) > 3 else 10.0,
                'data_adicao': datetime.now(timezone.utc),
                'quantidade_restante': params[1] if len(params) > 1 else 10
            })
        
        # Store in mock data
        if table_name not in self.data:
            self.data[table_name] = {}
        self.data[table_name][new_id] = record
        
        # Return the record for RETURNING clause
        return record
    
    def _handle_select(self, query: str, params: Tuple):
        """Handle SELECT queries."""
        # Simple mock - return empty results for most queries
        # You can enhance this to handle specific queries your tests need
        return []
    
    def _handle_update(self, query: str, params: Tuple):
        """Handle UPDATE queries."""
        return None
    
    def _handle_delete(self, query: str, params: Tuple):
        """Handle DELETE queries.""" 
        return None


class SchemaAccurateMockDatabase:
    """Mock database manager that maintains schema accuracy."""
    
    def __init__(self):
        self.data = {}
        self.counters = {}
        self.reset()
    
    def reset(self):
        """Reset to clean state."""
        self.data.clear()
        self.counters = {table: 1 for table in SchemaAccurateMockConnection.SCHEMA.keys()}
    
    def get_connection(self):
        """Get a schema-validating mock connection."""
        return SchemaAccurateMockConnection(self)
    
    @contextmanager
    def get_connection_context(self):
        """Context manager for connection."""
        conn = self.get_connection()
        try:
            yield conn
        finally:
            pass


# Global instance
_schema_mock_db = None

def get_schema_accurate_mock_db():
    """Get the global schema-accurate mock database."""
    global _schema_mock_db
    if _schema_mock_db is None:
        _schema_mock_db = SchemaAccurateMockDatabase()
    return _schema_mock_db

def reset_schema_mock_db():
    """Reset the schema mock database."""
    global _schema_mock_db
    if _schema_mock_db:
        _schema_mock_db.reset()