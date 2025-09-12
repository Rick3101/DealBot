#!/usr/bin/env python3
"""
Database query validation helper for testing.
Provides utilities to validate SQL queries against schema.
"""

import re
import ast
import inspect
from typing import Dict, List, Set, Tuple, Optional
from pathlib import Path


class QueryValidator:
    """Helper class to validate SQL queries in service files."""
    
    # Database schema mapping (from database/schema.py)
    SCHEMA_MAPPING = {
        'usuarios': {
            'columns': {'id', 'username', 'password', 'nivel', 'chat_id'},
            'primary_key': 'id',
            'unique_columns': {'username'}
        },
        'produtos': {
            'columns': {'id', 'nome', 'emoji', 'media_file_id'},
            'primary_key': 'id',
            'unique_columns': set()
        },
        'vendas': {
            'columns': {'id', 'comprador', 'data_venda'},
            'primary_key': 'id', 
            'unique_columns': set()
        },
        'itensvenda': {
            'columns': {'id', 'venda_id', 'produto_id', 'quantidade', 'valor_unitario', 'produto_nome'},
            'primary_key': 'id',
            'unique_columns': set()
        },
        'estoque': {
            'columns': {'id', 'produto_id', 'quantidade', 'preco', 'custo', 'data_adicao', 'quantidade_restante'},
            'primary_key': 'id',
            'unique_columns': set()
        },
        'pagamentos': {
            'columns': {'id', 'venda_id', 'valor_pago', 'data_pagamento'},
            'primary_key': 'id',
            'unique_columns': set()
        },
        'smartcontracts': {
            'columns': {'id', 'codigo', 'criador_chat_id', 'data_criacao', 'ativo'},
            'primary_key': 'id',
            'unique_columns': {'codigo'}
        },
        'transacoes': {
            'columns': {'id', 'contract_id', 'descricao', 'chat_id', 'data_transacao', 'confirmado'},
            'primary_key': 'id',
            'unique_columns': set()
        },
        'configuracoes': {
            'columns': {'id', 'chave', 'valor', 'descricao', 'data_atualizacao'},
            'primary_key': 'id',
            'unique_columns': {'chave'}
        }
    }
    
    @classmethod
    def extract_sql_from_file(cls, file_path: str) -> List[Dict[str, any]]:
        """Extract all SQL queries from a Python file with context."""
        queries = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the AST to find string literals that look like SQL
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Str):
                    sql_text = node.s
                    if cls._is_sql_query(sql_text):
                        # Get line number and context
                        line_num = getattr(node, 'lineno', 0)
                        queries.append({
                            'sql': sql_text,
                            'line': line_num,
                            'file': file_path,
                            'context': cls._extract_function_context(content, line_num)
                        })
                        
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            
        return queries
    
    @classmethod
    def _is_sql_query(cls, text: str) -> bool:
        """Check if a string contains SQL keywords."""
        sql_keywords = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER']
        text_upper = text.upper().strip()
        return any(keyword in text_upper for keyword in sql_keywords)
    
    @classmethod
    def _extract_function_context(cls, content: str, line_num: int) -> str:
        """Extract the function name containing the given line."""
        lines = content.split('\n')
        
        # Look backwards from the line to find the function definition
        for i in range(line_num - 1, -1, -1):
            if i < len(lines):
                line = lines[i].strip()
                if line.startswith('def ') or line.startswith('async def '):
                    func_match = re.match(r'(?:async\s+)?def\s+(\w+)', line)
                    if func_match:
                        return func_match.group(1)
        
        return "unknown_function"
    
    @classmethod
    def validate_query(cls, sql: str) -> List[str]:
        """Validate a single SQL query against the schema."""
        errors = []
        sql_upper = sql.upper()
        
        # Extract table and column references
        tables_columns = cls._extract_table_column_refs(sql)
        
        for table_name, referenced_columns in tables_columns.items():
            table_lower = table_name.lower()
            
            # Check if table exists in schema
            if table_lower not in cls.SCHEMA_MAPPING:
                errors.append(f"Table '{table_name}' does not exist in schema")
                continue
            
            # Check if all referenced columns exist
            schema_columns = cls.SCHEMA_MAPPING[table_lower]['columns']
            invalid_columns = referenced_columns - schema_columns
            
            if invalid_columns:
                errors.append(
                    f"Table '{table_name}' - invalid columns: {invalid_columns}. "
                    f"Valid columns: {schema_columns}"
                )
        
        return errors
    
    @classmethod
    def _extract_table_column_refs(cls, sql: str) -> Dict[str, Set[str]]:
        """Extract table and column references from SQL."""
        tables_columns = {}
        sql_upper = sql.upper()
        
        # Extract table names
        table_patterns = [
            r'FROM\s+(\w+)',
            r'JOIN\s+(\w+)', 
            r'INSERT\s+INTO\s+(\w+)',
            r'UPDATE\s+(\w+)'
        ]
        
        tables = set()
        for pattern in table_patterns:
            matches = re.findall(pattern, sql_upper)
            tables.update(matches)
        
        # For each table, extract column references
        for table in tables:
            columns = set()
            
            # Extract columns from INSERT INTO table (col1, col2, ...)
            insert_pattern = rf'INSERT\s+INTO\s+{re.escape(table)}\s*\(([^)]+)\)'
            insert_match = re.search(insert_pattern, sql_upper)
            if insert_match:
                column_list = insert_match.group(1)
                cols = [col.strip() for col in column_list.split(',')]
                columns.update(cols)
            
            # Extract columns from RETURNING clause
            returning_pattern = r'RETURNING\s+([^;\s]+(?:\s*,\s*[^;\s]+)*)'
            returning_match = re.search(returning_pattern, sql_upper)
            if returning_match:
                returning_cols = returning_match.group(1)
                cols = [col.strip() for col in returning_cols.split(',')]
                columns.update(cols)
            
            # Extract table.column references
            table_col_pattern = rf'{re.escape(table)}\.(\w+)'
            table_col_matches = re.findall(table_col_pattern, sql_upper)
            columns.update(table_col_matches)
            
            # Extract columns from SELECT clause
            if 'SELECT' in sql_upper:
                select_pattern = r'SELECT\s+(.+?)\s+FROM'
                select_match = re.search(select_pattern, sql_upper, re.DOTALL)
                if select_match:
                    select_clause = select_match.group(1)
                    # Look for simple column names (not functions or expressions)
                    simple_cols = re.findall(r'\b(\w+)\b', select_clause)
                    # Filter out SQL keywords
                    sql_keywords = {'DISTINCT', 'AS', 'FROM', 'WHERE', 'GROUP', 'ORDER', 'HAVING'}
                    simple_cols = [col for col in simple_cols if col not in sql_keywords]
                    columns.update(simple_cols)
            
            if columns:
                tables_columns[table.lower()] = {col.lower() for col in columns}
        
        return tables_columns
    
    @classmethod 
    def validate_service_file(cls, file_path: str) -> Dict[str, any]:
        """Validate all SQL queries in a service file."""
        queries = cls.extract_sql_from_file(file_path)
        validation_results = {
            'file': file_path,
            'total_queries': len(queries),
            'errors': [],
            'query_details': []
        }
        
        for query_info in queries:
            errors = cls.validate_query(query_info['sql'])
            
            query_detail = {
                'line': query_info['line'],
                'function': query_info['context'],
                'sql_preview': query_info['sql'][:100] + '...' if len(query_info['sql']) > 100 else query_info['sql'],
                'errors': errors
            }
            
            validation_results['query_details'].append(query_detail)
            
            if errors:
                for error in errors:
                    validation_results['errors'].append(f"Line {query_info['line']} in {query_info['context']}: {error}")
        
        return validation_results
    
    @classmethod
    def validate_all_services(cls, services_dir: str = "services") -> Dict[str, any]:
        """Validate all service files in the services directory."""
        services_path = Path(services_dir)
        results = {
            'total_files': 0,
            'files_with_errors': 0,
            'total_errors': 0,
            'file_results': []
        }
        
        for service_file in services_path.glob("*.py"):
            if service_file.name.startswith('__'):
                continue
                
            file_result = cls.validate_service_file(str(service_file))
            results['file_results'].append(file_result)
            results['total_files'] += 1
            
            if file_result['errors']:
                results['files_with_errors'] += 1
                results['total_errors'] += len(file_result['errors'])
        
        return results
    
    @classmethod
    def generate_validation_report(cls, services_dir: str = "services") -> str:
        """Generate a detailed validation report."""
        results = cls.validate_all_services(services_dir)
        
        report = []
        report.append("=== DATABASE QUERY VALIDATION REPORT ===")
        report.append(f"Total files analyzed: {results['total_files']}")
        report.append(f"Files with errors: {results['files_with_errors']}")
        report.append(f"Total errors found: {results['total_errors']}")
        report.append("")
        
        if results['total_errors'] == 0:
            report.append("✅ All SQL queries are valid!")
        else:
            report.append("❌ Issues found:")
            report.append("")
            
            for file_result in results['file_results']:
                if file_result['errors']:
                    report.append(f"📁 {file_result['file']}:")
                    for error in file_result['errors']:
                        report.append(f"  ❌ {error}")
                    report.append("")
        
        report.append("=== DETAILED QUERY ANALYSIS ===")
        for file_result in results['file_results']:
            report.append(f"\n📁 {file_result['file']} ({file_result['total_queries']} queries)")
            
            for query in file_result['query_details']:
                status = "❌" if query['errors'] else "✅"
                report.append(f"  {status} Line {query['line']} in {query['function']}()")
                if query['errors']:
                    for error in query['errors']:
                        report.append(f"      {error}")
        
        return "\n".join(report)


def validate_current_project():
    """Run validation on the current project and print results."""
    validator = QueryValidator()
    report = validator.generate_validation_report()
    print(report)
    return report


if __name__ == "__main__":
    validate_current_project()