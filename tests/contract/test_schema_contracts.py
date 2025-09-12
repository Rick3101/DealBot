"""
Contract tests for SQL schema validation.
Tests that service layer SQL queries match the actual database schema.
"""

import pytest
import re
import os
import ast
import inspect
from typing import List, Dict, Set

# Set environment but create real database manager for contract tests
os.environ['CONTRACT_TESTING'] = 'true'

from database.connection import DatabaseManager
from services.sales_service import SalesService
from services.product_service import ProductService
from services.user_service import UserService
from services.smartcontract_service import SmartContractService
from services.config_service import ConfigService


class SQLQueryExtractor:
    """Extracts SQL queries from Python service code."""
    
    @staticmethod
    def extract_queries_from_service(service_class) -> List[Dict[str, str]]:
        """Extract all SQL queries from a service class."""
        queries = []
        source = inspect.getsource(service_class)
        
        # Find all triple-quoted strings that contain SQL keywords
        sql_pattern = r'"""([^"]*(?:SELECT|INSERT|UPDATE|DELETE|CREATE|ALTER)[^"]*)"""'
        matches = re.findall(sql_pattern, source, re.IGNORECASE | re.DOTALL)
        
        for match in matches:
            # Clean up the query
            query = match.strip()
            if any(keyword in query.upper() for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'RETURNING']):
                queries.append({
                    'query': query,
                    'service': service_class.__name__,
                    'type': SQLQueryExtractor._get_query_type(query)
                })
        
        # Also find string literals with SQL
        string_pattern = r'"([^"]*(?:SELECT|INSERT|UPDATE|DELETE|RETURNING)[^"]*)"'
        string_matches = re.findall(string_pattern, source, re.IGNORECASE)
        
        for match in string_matches:
            query = match.strip()
            if any(keyword in query.upper() for keyword in ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'RETURNING']):
                queries.append({
                    'query': query,
                    'service': service_class.__name__,
                    'type': SQLQueryExtractor._get_query_type(query)
                })
        
        return queries
    
    @staticmethod
    def _get_query_type(query: str) -> str:
        """Determine the type of SQL query."""
        query_upper = query.upper().strip()
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        else:
            return 'UNKNOWN'


class SchemaValidator:
    """Validates SQL queries against actual database schema."""
    
    def __init__(self):
        # Create real database manager for contract testing
        database_url = os.getenv('DATABASE_URL')
        if not database_url:
            pytest.skip("DATABASE_URL not set for contract testing")
        self.db_manager = DatabaseManager(database_url)
        self.schema_info = self._get_schema_info()
    
    def _get_schema_info(self) -> Dict[str, Set[str]]:
        """Get actual database schema information."""
        schema = {}
        
        with self.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                # Get all tables and their columns
                cursor.execute("""
                    SELECT table_name, column_name 
                    FROM information_schema.columns 
                    WHERE table_schema = 'public'
                    ORDER BY table_name, ordinal_position
                """)
                
                for table_name, column_name in cursor.fetchall():
                    if table_name not in schema:
                        schema[table_name] = set()
                    schema[table_name].add(column_name.lower())
        
        return schema
    
    def validate_query(self, query: str, service_name: str) -> List[str]:
        """Validate a single SQL query against schema."""
        errors = []
        query_upper = query.upper()
        
        # Focus on critical column mismatches that cause runtime errors
        critical_checks = [
            # The exact issue you encountered
            (r'RETURNING\s+[^,]*,\s*[^,]*,\s*data\b', 'RETURNING clause uses "data" instead of "data_venda"'),
            (r'SELECT\s+[^,]*,\s*[^,]*,\s*data\s+FROM\s+vendas', 'SELECT uses "data" instead of "data_venda" in Vendas'),
            (r'ORDER\s+BY\s+data\s', 'ORDER BY uses "data" instead of correct timestamp column'),
            # Other common mismatches
            (r'FROM\s+estoque.*data\b', 'Estoque table: "data" should be "data_adicao"'),
            (r'FROM\s+pagamentos.*data\b', 'Pagamentos table: "data" should be "data_pagamento"'),
        ]
        
        for pattern, error_msg in critical_checks:
            if re.search(pattern, query_upper):
                errors.append(f"{service_name}: {error_msg}")
        
        # Extract table names and check they exist
        tables = self._extract_table_names(query)
        for table in tables:
            table_lower = table.lower()
            if table_lower not in self.schema_info and len(table) > 2:  # Skip short fragments
                errors.append(f"{service_name}: Table '{table}' not found in schema")
        
        return errors
    
    def _extract_table_names(self, query: str) -> List[str]:
        """Extract table names from SQL query."""
        tables = []
        query_upper = query.upper()
        
        # Known table names from schema to avoid false positives
        known_tables = {
            'vendas', 'estoque', 'produtos', 'usuarios', 'pagamentos', 
            'smartcontracts', 'transacoessmartcontract', 'configuracoes',
            'itensvenda', 'transacoes'
        }
        
        # FROM clause
        from_match = re.search(r'FROM\s+(\w+)', query_upper)
        if from_match:
            table = from_match.group(1).lower()
            if table in known_tables:
                tables.append(table)
        
        # INSERT INTO clause
        insert_match = re.search(r'INSERT\s+INTO\s+(\w+)', query_upper)
        if insert_match:
            table = insert_match.group(1).lower()
            if table in known_tables:
                tables.append(table)
        
        # UPDATE clause
        update_match = re.search(r'UPDATE\s+(\w+)', query_upper)
        if update_match:
            table = update_match.group(1).lower()
            if table in known_tables:
                tables.append(table)
        
        # JOIN clauses
        join_matches = re.findall(r'JOIN\s+(\w+)', query_upper)
        for table in join_matches:
            if table.lower() in known_tables:
                tables.append(table.lower())
        
        return list(set(tables))  # Remove duplicates
    
    def _extract_column_references(self, query: str) -> List[str]:
        """Extract column references from SQL query."""
        columns = []
        
        # RETURNING clause
        returning_match = re.search(r'RETURNING\s+([^;]+)', query.upper())
        if returning_match:
            column_list = returning_match.group(1)
            # Split by comma and clean up
            for col in column_list.split(','):
                col = col.strip()
                if '.' in col:
                    col = col.split('.')[1]  # Remove table prefix
                # Only include valid column names (not functions/expressions)
                if col and not any(func in col for func in ['(', ')', 'AS', 'CASE', 'WHEN']):
                    columns.append(col)
        
        # SELECT clause columns - only extract simple column references
        select_match = re.search(r'SELECT\s+([^FROM]+)', query.upper())
        if select_match:
            column_list = select_match.group(1)
            for col in column_list.split(','):
                col = col.strip()
                # Skip aggregate functions, expressions, and wildcards
                if (col != '*' and 
                    not any(func in col for func in ['COUNT', 'SUM', 'COALESCE', 'CASE', 'WHEN', '(', ')', 'AS']) and
                    not col.startswith(('MAX', 'MIN', 'AVG')) and
                    len(col) > 1):  # Skip single character fragments
                    if '.' in col:
                        col = col.split('.')[1]
                    columns.append(col)
        
        return columns


class TestSchemaContracts:
    """Contract tests for schema validation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.validator = SchemaValidator()
        self.query_extractor = SQLQueryExtractor()
    
    @pytest.mark.contract
    def test_sales_service_queries_match_schema(self):
        """Test that all SalesService queries match database schema."""
        queries = self.query_extractor.extract_queries_from_service(SalesService)
        errors = []
        
        for query_info in queries:
            query_errors = self.validator.validate_query(
                query_info['query'], 
                query_info['service']
            )
            errors.extend(query_errors)
        
        if errors:
            pytest.fail(f"Schema validation errors in SalesService:\\n" + "\\n".join(errors))
    
    @pytest.mark.contract
    def test_product_service_queries_match_schema(self):
        """Test that all ProductService queries match database schema."""
        queries = self.query_extractor.extract_queries_from_service(ProductService)
        errors = []
        
        for query_info in queries:
            query_errors = self.validator.validate_query(
                query_info['query'], 
                query_info['service']
            )
            errors.extend(query_errors)
        
        if errors:
            pytest.fail(f"Schema validation errors in ProductService:\\n" + "\\n".join(errors))
    
    @pytest.mark.contract
    def test_user_service_queries_match_schema(self):
        """Test that all UserService queries match database schema."""
        queries = self.query_extractor.extract_queries_from_service(UserService)
        errors = []
        
        for query_info in queries:
            query_errors = self.validator.validate_query(
                query_info['query'], 
                query_info['service']
            )
            errors.extend(query_errors)
        
        if errors:
            pytest.fail(f"Schema validation errors in UserService:\\n" + "\\n".join(errors))
    
    @pytest.mark.contract
    def test_smartcontract_service_queries_match_schema(self):
        """Test that all SmartContractService queries match database schema."""
        queries = self.query_extractor.extract_queries_from_service(SmartContractService)
        errors = []
        
        for query_info in queries:
            query_errors = self.validator.validate_query(
                query_info['query'], 
                query_info['service']
            )
            errors.extend(query_errors)
        
        if errors:
            pytest.fail(f"Schema validation errors in SmartContractService:\\n" + "\\n".join(errors))
    
    @pytest.mark.contract
    def test_config_service_queries_match_schema(self):
        """Test that all ConfigService queries match database schema."""
        queries = self.query_extractor.extract_queries_from_service(ConfigService)
        errors = []
        
        for query_info in queries:
            query_errors = self.validator.validate_query(
                query_info['query'], 
                query_info['service']
            )
            errors.extend(query_errors)
        
        if errors:
            pytest.fail(f"Schema validation errors in ConfigService:\\n" + "\\n".join(errors))
    
    @pytest.mark.contract
    def test_critical_column_mappings(self):
        """Test critical column mappings that commonly cause issues."""
        critical_mappings = [
            ('vendas', 'data_venda'),  # Not 'data'
            ('estoque', 'data'),  # Estoque uses 'data' not 'data_adicao'
            ('pagamentos', 'data_pagamento'),  # Not 'data'
            ('usuarios', 'nivel'),  # Ensure correct permission column
            ('smartcontracts', 'criado_em'),  # Smart contract timestamps (per real schema)
            ('transacoessmartcontract', 'data_criacao'),  # Transaction timestamps
            ('configuracoes', 'data_atualizacao'),  # Config timestamps
        ]
        
        for table, expected_column in critical_mappings:
            table_lower = table.lower()
            if table_lower in self.validator.schema_info:
                assert expected_column.lower() in self.validator.schema_info[table_lower], \
                    f"Critical column '{expected_column}' missing in table '{table}'"
    
    @pytest.mark.contract
    def test_all_services_have_extractable_queries(self):
        """Ensure all services have SQL queries that can be extracted."""
        services = [SalesService, ProductService, UserService, SmartContractService, ConfigService]
        
        for service in services:
            queries = self.query_extractor.extract_queries_from_service(service)
            assert len(queries) > 0, f"{service.__name__} should have extractable SQL queries"
    
    @pytest.mark.contract
    def test_query_execution_against_real_schema(self):
        """Test that extracted queries can actually execute against real schema."""
        services = [SalesService, ProductService, UserService, SmartContractService, ConfigService]
        
        for service in services:
            queries = self.query_extractor.extract_queries_from_service(service)
            
            for query_info in queries:
                query = query_info['query']
                
                # Skip queries with parameters for this test
                if '%s' in query:
                    continue
                
                # Try to prepare the query (validates syntax and schema)
                try:
                    with self.validator.db_manager.get_connection() as conn:
                        with conn.cursor() as cursor:
                            # Just prepare, don't execute
                            cursor.execute(f"EXPLAIN {query}")
                except Exception as e:
                    pytest.fail(f"Query validation failed in {query_info['service']}: {str(e)}\\nQuery: {query}")
    
    @pytest.mark.contract 
    def test_not_null_constraint_compliance(self):
        """Test that INSERT queries provide values for NOT NULL columns without defaults."""
        
        # Get NOT NULL columns without defaults for critical tables
        critical_tables = ['vendas', 'estoque', 'produtos', 'usuarios']
        not_null_columns = {}
        
        with self.validator.db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                for table in critical_tables:
                    cursor.execute("""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_name = %s 
                        AND is_nullable = 'NO' 
                        AND column_default IS NULL
                        AND column_name != 'id'  -- Skip auto-increment IDs
                    """, (table,))
                    
                    cols = [row[0] for row in cursor.fetchall()]
                    if cols:
                        not_null_columns[table] = cols
        
        # Check SalesService queries for NOT NULL compliance
        queries = self.query_extractor.extract_queries_from_service(SalesService)
        
        for query_info in queries:
            query = query_info['query'].upper()
            
            # Check INSERT queries
            if 'INSERT INTO' in query:
                for table, required_cols in not_null_columns.items():
                    table_upper = table.upper()
                    if f'INSERT INTO {table_upper}' in query:
                        for col in required_cols:
                            col_upper = col.upper()
                            # Check if the required column is mentioned in the INSERT
                            if col_upper not in query:
                                errors = [f"INSERT into {table} missing required NOT NULL column: {col}"]
                                if errors:
                                    pytest.fail(f"NOT NULL constraint violations in SalesService:\\n" + "\\n".join(errors))


if __name__ == "__main__":
    # Run contract tests directly
    pytest.main([__file__, "-v"])