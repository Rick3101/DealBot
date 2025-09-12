#!/usr/bin/env python3
"""
Schema validation tests to ensure service queries match database schema.
"""

import re
import pytest
from typing import Dict, List, Set
from database.schema import initialize_schema
from database import get_db_manager


class SchemaValidator:
    """Validates that service SQL queries match the actual database schema."""
    
    def __init__(self):
        self.db_manager = get_db_manager()
        self._schema_cache = {}
    
    def get_table_columns(self, table_name: str) -> Set[str]:
        """Get all columns for a table from the database."""
        if table_name in self._schema_cache:
            return self._schema_cache[table_name]
        
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s AND table_schema = 'public'
                """, (table_name.lower(),))
                
                columns = {row[0] for row in cursor.fetchall()}
                self._schema_cache[table_name] = columns
                return columns
    
    def extract_sql_queries(self, file_path: str) -> List[str]:
        """Extract SQL queries from Python service files."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find SQL queries in triple quotes
        sql_pattern = r'"""([^"]*(?:SELECT|INSERT|UPDATE|DELETE)[^"]*)"""'
        queries = re.findall(sql_pattern, content, re.IGNORECASE | re.DOTALL)
        
        # Also find single-line SQL strings
        single_line_pattern = r'"([^"]*(?:SELECT|INSERT|UPDATE|DELETE)[^"]*)"'
        single_queries = re.findall(single_line_pattern, content, re.IGNORECASE)
        
        return queries + single_queries
    
    def extract_table_columns_from_query(self, query: str) -> Dict[str, Set[str]]:
        """Extract table names and referenced columns from SQL query."""
        query = query.upper()
        tables_columns = {}
        
        # Extract table names from FROM, JOIN, INSERT INTO, UPDATE
        table_patterns = [
            r'FROM\s+(\w+)',
            r'JOIN\s+(\w+)',
            r'INSERT\s+INTO\s+(\w+)',
            r'UPDATE\s+(\w+)'
        ]
        
        tables = set()
        for pattern in table_patterns:
            matches = re.findall(pattern, query)
            tables.update(matches)
        
        # Extract column references
        for table in tables:
            # Find columns referenced as table.column
            column_pattern = rf'{table}\.(\w+)'
            columns = set(re.findall(column_pattern, query, re.IGNORECASE))
            
            # Also check for columns in SELECT, INSERT, RETURNING clauses
            if f'INSERT INTO {table}' in query:
                # Extract INSERT column list
                insert_pattern = rf'INSERT INTO {table}\s*\(([^)]+)\)'
                insert_match = re.search(insert_pattern, query, re.IGNORECASE)
                if insert_match:
                    insert_cols = [col.strip() for col in insert_match.group(1).split(',')]
                    columns.update(insert_cols)
            
            # Extract RETURNING columns
            returning_pattern = r'RETURNING\s+([^;\s]+)'
            returning_match = re.search(returning_pattern, query, re.IGNORECASE)
            if returning_match:
                returning_cols = [col.strip() for col in returning_match.group(1).split(',')]
                columns.update(returning_cols)
            
            if columns:
                tables_columns[table.lower()] = {col.lower() for col in columns}
        
        return tables_columns
    
    def validate_service_queries(self, service_file: str) -> List[str]:
        """Validate all SQL queries in a service file against schema."""
        errors = []
        queries = self.extract_sql_queries(service_file)
        
        for query in queries:
            try:
                tables_columns = self.extract_table_columns_from_query(query)
                
                for table_name, query_columns in tables_columns.items():
                    schema_columns = self.get_table_columns(table_name)
                    
                    # Check for missing columns
                    missing_columns = query_columns - schema_columns
                    if missing_columns:
                        errors.append(
                            f"Service file {service_file} references non-existent columns "
                            f"in table '{table_name}': {missing_columns}"
                        )
            except Exception as e:
                errors.append(f"Error validating query in {service_file}: {e}")
        
        return errors


@pytest.mark.schema_validation
class TestSchemaValidation:
    """Test suite for database schema validation."""
    
    @classmethod
    def setup_class(cls):
        """Initialize schema validator."""
        cls.validator = SchemaValidator()
    
    def test_vendas_table_schema_consistency(self):
        """Test that Vendas table queries match schema."""
        errors = self.validator.validate_service_queries('services/sales_service.py')
        
        # Filter for Vendas-specific errors
        vendas_errors = [e for e in errors if 'vendas' in e.lower()]
        
        if vendas_errors:
            pytest.fail(f"Vendas table schema validation failed:\n" + "\n".join(vendas_errors))
    
    def test_produtos_table_schema_consistency(self):
        """Test that Produtos table queries match schema."""
        errors = self.validator.validate_service_queries('services/product_service.py')
        
        produtos_errors = [e for e in errors if 'produtos' in e.lower()]
        
        if produtos_errors:
            pytest.fail(f"Produtos table schema validation failed:\n" + "\n".join(produtos_errors))
    
    def test_usuarios_table_schema_consistency(self):
        """Test that Usuarios table queries match schema."""
        errors = self.validator.validate_service_queries('services/user_service.py')
        
        usuarios_errors = [e for e in errors if 'usuarios' in e.lower()]
        
        if usuarios_errors:
            pytest.fail(f"Usuarios table schema validation failed:\n" + "\n".join(usuarios_errors))
    
    def test_all_services_schema_consistency(self):
        """Test all service files for schema consistency."""
        service_files = [
            'services/sales_service.py',
            'services/product_service.py', 
            'services/user_service.py',
            'services/smartcontract_service.py'
        ]
        
        all_errors = []
        for service_file in service_files:
            try:
                errors = self.validator.validate_service_queries(service_file)
                all_errors.extend(errors)
            except FileNotFoundError:
                # Skip missing service files
                continue
        
        if all_errors:
            pytest.fail(f"Schema validation failed:\n" + "\n".join(all_errors))
    
    def test_database_schema_completeness(self):
        """Test that all required tables exist in database."""
        required_tables = [
            'usuarios', 'produtos', 'vendas', 'itensvenda',
            'estoque', 'pagamentos', 'smartcontracts', 
            'transacoes', 'configuracoes'
        ]
        
        missing_tables = []
        for table in required_tables:
            try:
                columns = self.validator.get_table_columns(table)
                if not columns:
                    missing_tables.append(table)
            except Exception:
                missing_tables.append(table)
        
        if missing_tables:
            pytest.fail(f"Missing required tables: {missing_tables}")
    
    def test_vendas_data_column_fix(self):
        """Specific test for the data/data_venda column issue."""
        # This test validates the fix we just applied
        with self.validator.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Test that data_venda column exists
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'vendas' AND column_name = 'data_venda'
                """)
                
                result = cursor.fetchone()
                assert result is not None, "data_venda column missing from Vendas table"
                
                # Test that 'data' column does NOT exist (it should be data_venda)
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'vendas' AND column_name = 'data'
                """)
                
                result = cursor.fetchone()
                assert result is None, "Found 'data' column in Vendas table - should be 'data_venda'"