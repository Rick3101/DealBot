#!/usr/bin/env python3
"""
Comprehensive schema validation tests for all handlers and their services.
Validates that all SQL queries across the project match the database schema.
"""

import pytest
from tests.test_schema_validation import SchemaValidator


@pytest.mark.schema_validation
class TestAllHandlersSchemaValidation:
    """Test suite for validating all handlers' database operations."""
    
    @classmethod
    def setup_class(cls):
        """Initialize schema validator."""
        cls.validator = SchemaValidator()
    
    def test_sales_service_schema_consistency(self):
        """Test SalesService SQL queries match schema."""
        errors = self.validator.validate_service_queries('services/sales_service.py')
        
        # Filter for sales-related errors
        sales_errors = [e for e in errors if any(table in e.lower() for table in ['vendas', 'itensvenda', 'pagamentos'])]
        
        if sales_errors:
            pytest.fail(f"SalesService schema validation failed:\n" + "\n".join(sales_errors))
    
    def test_product_service_schema_consistency(self):
        """Test ProductService SQL queries match schema."""
        errors = self.validator.validate_service_queries('services/product_service.py')
        
        # Filter for product-related errors
        product_errors = [e for e in errors if any(table in e.lower() for table in ['produtos', 'estoque'])]
        
        if product_errors:
            pytest.fail(f"ProductService schema validation failed:\n" + "\n".join(product_errors))
    
    def test_user_service_schema_consistency(self):
        """Test UserService SQL queries match schema."""
        errors = self.validator.validate_service_queries('services/user_service.py')
        
        # Filter for user-related errors
        user_errors = [e for e in errors if 'usuarios' in e.lower()]
        
        if user_errors:
            pytest.fail(f"UserService schema validation failed:\n" + "\n".join(user_errors))
    
    def test_smartcontract_service_schema_consistency(self):
        """Test SmartContractService SQL queries match schema."""
        errors = self.validator.validate_service_queries('services/smartcontract_service.py')
        
        # Filter for smartcontract-related errors
        contract_errors = [e for e in errors if any(table in e.lower() for table in ['smartcontracts', 'transacoes'])]
        
        if contract_errors:
            pytest.fail(f"SmartContractService schema validation failed:\n" + "\n".join(contract_errors))
    
    def test_handler_business_service_schema_consistency(self):
        """Test HandlerBusinessService SQL queries match schema."""
        try:
            errors = self.validator.validate_service_queries('services/handler_business_service.py')
            
            if errors:
                pytest.fail(f"HandlerBusinessService schema validation failed:\n" + "\n".join(errors))
        except FileNotFoundError:
            # Skip if service doesn't exist or has no SQL
            pytest.skip("HandlerBusinessService not found or has no SQL queries")
    
    def test_config_service_schema_consistency(self):
        """Test ConfigService SQL queries match schema."""
        try:
            errors = self.validator.validate_service_queries('services/config_service.py')
            
            # Filter for config-related errors
            config_errors = [e for e in errors if 'configuracoes' in e.lower()]
            
            if config_errors:
                pytest.fail(f"ConfigService schema validation failed:\n" + "\n".join(config_errors))
        except FileNotFoundError:
            pytest.skip("ConfigService not found or has no SQL queries")
    
    def test_all_services_comprehensive_validation(self):
        """Comprehensive validation of all service files."""
        service_files = [
            'services/sales_service.py',
            'services/product_service.py',
            'services/user_service.py',
            'services/smartcontract_service.py',
            'services/handler_business_service.py',
            'services/config_service.py'
        ]
        
        all_errors = []
        service_results = {}
        
        for service_file in service_files:
            try:
                errors = self.validator.validate_service_queries(service_file)
                service_results[service_file] = errors
                all_errors.extend(errors)
            except FileNotFoundError:
                # Skip missing service files
                service_results[service_file] = ["File not found"]
                continue
        
        # Create detailed error report
        if all_errors:
            error_report = ["Comprehensive schema validation failed:"]
            for service, errors in service_results.items():
                if errors and "File not found" not in str(errors):
                    error_report.append(f"\n{service}:")
                    for error in errors:
                        error_report.append(f"  - {error}")
            
            pytest.fail("\n".join(error_report))
    
    def test_critical_tables_column_consistency(self):
        """Test critical table column consistency across all services."""
        critical_tests = [
            {
                'table': 'vendas',
                'columns': ['id', 'comprador', 'data_venda'],
                'services': ['services/sales_service.py']
            },
            {
                'table': 'produtos', 
                'columns': ['id', 'nome', 'emoji', 'media_file_id'],
                'services': ['services/product_service.py']
            },
            {
                'table': 'usuarios',
                'columns': ['id', 'username', 'password', 'nivel', 'chat_id'],
                'services': ['services/user_service.py']
            },
            {
                'table': 'estoque',
                'columns': ['id', 'produto_id', 'quantidade', 'preco', 'custo', 'data_adicao', 'quantidade_restante'],
                'services': ['services/product_service.py', 'services/sales_service.py']
            },
            {
                'table': 'itensvenda',
                'columns': ['id', 'venda_id', 'produto_id', 'quantidade', 'valor_unitario', 'produto_nome'],
                'services': ['services/sales_service.py']
            },
            {
                'table': 'pagamentos',
                'columns': ['id', 'venda_id', 'valor_pago', 'data_pagamento'],
                'services': ['services/sales_service.py']
            },
            {
                'table': 'smartcontracts',
                'columns': ['id', 'codigo', 'criador_chat_id', 'data_criacao', 'ativo'],
                'services': ['services/smartcontract_service.py']
            },
            {
                'table': 'transacoes',
                'columns': ['id', 'contract_id', 'descricao', 'chat_id', 'data_transacao', 'confirmado'],
                'services': ['services/smartcontract_service.py']
            }
        ]
        
        errors = []
        
        for test_case in critical_tests:
            table_name = test_case['table']
            expected_columns = set(test_case['columns'])
            services = test_case['services']
            
            # Get actual schema columns
            try:
                actual_columns = self.validator.get_table_columns(table_name)
                
                # Check if expected columns exist
                missing_columns = expected_columns - actual_columns
                if missing_columns:
                    errors.append(f"Table '{table_name}' missing expected columns: {missing_columns}")
                
                # Validate each service that uses this table
                for service_file in services:
                    try:
                        service_errors = self.validator.validate_service_queries(service_file)
                        table_errors = [e for e in service_errors if table_name in e.lower()]
                        if table_errors:
                            errors.extend([f"{service_file}: {err}" for err in table_errors])
                    except FileNotFoundError:
                        continue
                        
            except Exception as e:
                errors.append(f"Error validating table '{table_name}': {e}")
        
        if errors:
            pytest.fail(f"Critical table validation failed:\n" + "\n".join(errors))
    
    def test_foreign_key_consistency(self):
        """Test foreign key references are valid across services."""
        foreign_key_tests = [
            {
                'table': 'itensvenda',
                'fk_column': 'venda_id',
                'referenced_table': 'vendas',
                'referenced_column': 'id'
            },
            {
                'table': 'itensvenda',
                'fk_column': 'produto_id',
                'referenced_table': 'produtos',
                'referenced_column': 'id'
            },
            {
                'table': 'estoque',
                'fk_column': 'produto_id',
                'referenced_table': 'produtos',
                'referenced_column': 'id'
            },
            {
                'table': 'pagamentos',
                'fk_column': 'venda_id',
                'referenced_table': 'vendas',
                'referenced_column': 'id'
            },
            {
                'table': 'transacoes',
                'fk_column': 'contract_id',
                'referenced_table': 'smartcontracts',
                'referenced_column': 'id'
            }
        ]
        
        errors = []
        
        for fk_test in foreign_key_tests:
            table = fk_test['table']
            fk_column = fk_test['fk_column']
            ref_table = fk_test['referenced_table']
            ref_column = fk_test['referenced_column']
            
            try:
                # Check if both tables and columns exist
                table_columns = self.validator.get_table_columns(table)
                ref_table_columns = self.validator.get_table_columns(ref_table)
                
                if fk_column not in table_columns:
                    errors.append(f"Foreign key column '{fk_column}' missing from table '{table}'")
                
                if ref_column not in ref_table_columns:
                    errors.append(f"Referenced column '{ref_column}' missing from table '{ref_table}'")
                    
            except Exception as e:
                errors.append(f"Error validating FK {table}.{fk_column} -> {ref_table}.{ref_column}: {e}")
        
        if errors:
            pytest.fail(f"Foreign key validation failed:\n" + "\n".join(errors))
    
    def test_data_venda_column_fix_validation(self):
        """Specific test to ensure data_venda column fix is working across all services."""
        # Test that no service uses the old 'data' column name for vendas table
        services_to_check = [
            'services/sales_service.py',
            'services/handler_business_service.py'
        ]
        
        errors = []
        
        for service_file in services_to_check:
            try:
                queries = self.validator.extract_sql_queries(service_file)
                
                for query in queries:
                    # Check for problematic patterns
                    if 'vendas' in query.lower():
                        # Look for incorrect 'data' column usage
                        if 'v.data,' in query or 'v.data ' in query or 'v.data\n' in query:
                            if 'v.data_venda' not in query:
                                errors.append(f"{service_file}: Found 'v.data' without 'v.data_venda' in query")
                        
                        # Look for RETURNING data instead of data_venda
                        if 'returning' in query.lower() and ', data' in query.lower():
                            if 'data_venda' not in query.lower():
                                errors.append(f"{service_file}: Found 'RETURNING ...data' without 'data_venda'")
                                
            except FileNotFoundError:
                continue
        
        if errors:
            pytest.fail(f"data_venda column validation failed:\n" + "\n".join(errors))