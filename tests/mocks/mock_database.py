"""
Mock database operations for fast testing.
Provides in-memory data structures that simulate database behavior.
"""

from typing import Dict, List, Any, Optional
from unittest.mock import Mock, AsyncMock
from datetime import datetime
import uuid


class MockDatabaseManager:
    """Mock database manager that simulates database operations in memory."""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all data to initial state."""
        # In-memory "tables"
        self.usuarios = {}
        self.produtos = {}
        self.estoque = {}
        self.vendas = {}
        self.itens_venda = {}
        self.pagamentos = {}
        self.smartcontracts = {}
        self.transacoes = {}
        self.configuracoes = {}
        
        # Auto-increment counters
        self._counters = {
            'usuarios': 1,
            'produtos': 1,
            'estoque': 1,
            'vendas': 1,
            'itens_venda': 1,
            'pagamentos': 1,
            'smartcontracts': 1,
            'transacoes': 1,
            'configuracoes': 1
        }
        
        # Connection pool mock
        self.pool = Mock()
        self.pool.acquire = AsyncMock()
        self.pool.release = AsyncMock()
    
    def get_next_id(self, table: str) -> int:
        """Get next auto-increment ID for a table."""
        next_id = self._counters[table]
        self._counters[table] += 1
        return next_id
    
    async def acquire_connection(self):
        """Mock connection acquisition."""
        return MockConnection(self)
    
    async def close(self):
        """Mock database close."""
        pass


class MockConnection:
    """Mock database connection that simulates SQL operations."""
    
    def __init__(self, db_manager: MockDatabaseManager):
        self.db = db_manager
        self.closed = False
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close the mock connection."""
        self.closed = True
    
    async def execute(self, query: str, *args) -> int:
        """Mock SQL execution that returns affected rows."""
        # Simulate different SQL operations
        query_lower = query.lower().strip()
        
        if query_lower.startswith('insert into usuarios'):
            return self._insert_user(args)
        elif query_lower.startswith('insert into produtos'):
            return self._insert_product(args)
        elif query_lower.startswith('insert into estoque'):
            return self._insert_stock(args)
        elif query_lower.startswith('insert into vendas'):
            return self._insert_sale(args)
        elif query_lower.startswith('insert into itens_venda'):
            return self._insert_sale_item(args)
        elif query_lower.startswith('insert into pagamentos'):
            return self._insert_payment(args)
        elif query_lower.startswith('update'):
            return self._update_record(query, args)
        elif query_lower.startswith('delete'):
            return self._delete_record(query, args)
        else:
            return 1  # Default success
    
    async def fetchone(self, query: str, *args) -> Optional[Dict[str, Any]]:
        """Mock fetch one record."""
        query_lower = query.lower().strip()
        
        if 'usuarios' in query_lower:
            return self._fetch_user(query, args)
        elif 'produtos' in query_lower:
            return self._fetch_product(query, args)
        elif 'vendas' in query_lower:
            return self._fetch_sale(query, args)
        elif 'estoque' in query_lower:
            return self._fetch_stock(query, args)
        else:
            return None
    
    async def fetchall(self, query: str, *args) -> List[Dict[str, Any]]:
        """Mock fetch all records."""
        query_lower = query.lower().strip()
        
        if 'usuarios' in query_lower:
            return self._fetch_all_users(query, args)
        elif 'produtos' in query_lower:
            return self._fetch_all_products(query, args)
        elif 'estoque' in query_lower:
            return self._fetch_all_stock(query, args)
        elif 'vendas' in query_lower:
            return self._fetch_all_sales(query, args)
        else:
            return []
    
    # Internal methods to simulate database operations
    
    def _insert_user(self, args) -> int:
        """Insert user record."""
        user_id = self.db.get_next_id('usuarios')
        self.db.usuarios[user_id] = {
            'id': user_id,
            'nome': args[0] if args else 'test_user',
            'senha': args[1] if len(args) > 1 else 'test_pass',
            'nivel': args[2] if len(args) > 2 else 'user',
            'chat_id': args[3] if len(args) > 3 else None,
            'data_criacao': datetime.now()
        }
        return user_id
    
    def _insert_product(self, args) -> int:
        """Insert product record."""
        product_id = self.db.get_next_id('produtos')
        self.db.produtos[product_id] = {
            'id': product_id,
            'nome': args[0] if args else 'test_product',
            'emoji': args[1] if len(args) > 1 else '📦',
            'tipo_midia': args[2] if len(args) > 2 else None,
            'arquivo_midia': args[3] if len(args) > 3 else None,
            'data_criacao': datetime.now()
        }
        return product_id
    
    def _insert_stock(self, args) -> int:
        """Insert stock record."""
        stock_id = self.db.get_next_id('estoque')
        self.db.estoque[stock_id] = {
            'id': stock_id,
            'produto_id': args[0] if args else 1,
            'quantidade': args[1] if len(args) > 1 else 10,
            'preco_custo': args[2] if len(args) > 2 else 10.0,
            'data_adicao': datetime.now()
        }
        return stock_id
    
    def _insert_sale(self, args) -> int:
        """Insert sale record."""
        sale_id = self.db.get_next_id('vendas')
        self.db.vendas[sale_id] = {
            'id': sale_id,
            'nome_comprador': args[0] if args else 'test_buyer',
            'valor_total': args[1] if len(args) > 1 else 100.0,
            'data_venda': datetime.now(),
            'chat_id': args[2] if len(args) > 2 else None
        }
        return sale_id
    
    def _insert_sale_item(self, args) -> int:
        """Insert sale item record."""
        item_id = self.db.get_next_id('itens_venda')
        self.db.itens_venda[item_id] = {
            'id': item_id,
            'venda_id': args[0] if args else 1,
            'produto_id': args[1] if len(args) > 1 else 1,
            'quantidade': args[2] if len(args) > 2 else 1,
            'preco_unitario': args[3] if len(args) > 3 else 10.0
        }
        return item_id
    
    def _insert_payment(self, args) -> int:
        """Insert payment record."""
        payment_id = self.db.get_next_id('pagamentos')
        self.db.pagamentos[payment_id] = {
            'id': payment_id,
            'nome_devedor': args[0] if args else 'test_debtor',
            'valor': args[1] if len(args) > 1 else 50.0,
            'data_pagamento': datetime.now(),
            'chat_id': args[2] if len(args) > 2 else None
        }
        return payment_id
    
    def _fetch_user(self, query: str, args) -> Optional[Dict[str, Any]]:
        """Fetch user by criteria."""
        if args and len(args) > 0:
            # Usually searching by chat_id or username
            for user in self.db.usuarios.values():
                if user.get('chat_id') == args[0] or user.get('nome') == args[0]:
                    return user
        return None
    
    def _fetch_product(self, query: str, args) -> Optional[Dict[str, Any]]:
        """Fetch product by criteria."""
        if args and len(args) > 0:
            product_id = args[0]
            return self.db.produtos.get(product_id)
        return None
    
    def _fetch_sale(self, query: str, args) -> Optional[Dict[str, Any]]:
        """Fetch sale by criteria."""
        if args and len(args) > 0:
            sale_id = args[0]
            return self.db.vendas.get(sale_id)
        return None
    
    def _fetch_stock(self, query: str, args) -> Optional[Dict[str, Any]]:
        """Fetch stock by criteria."""
        if args and len(args) > 0:
            product_id = args[0]
            # Return total available stock for product
            total_qty = sum(
                stock['quantidade'] 
                for stock in self.db.estoque.values() 
                if stock['produto_id'] == product_id
            )
            return {'total_quantity': total_qty} if total_qty > 0 else None
        return None
    
    def _fetch_all_users(self, query: str, args) -> List[Dict[str, Any]]:
        """Fetch all users."""
        return list(self.db.usuarios.values())
    
    def _fetch_all_products(self, query: str, args) -> List[Dict[str, Any]]:
        """Fetch all products."""
        return list(self.db.produtos.values())
    
    def _fetch_all_stock(self, query: str, args) -> List[Dict[str, Any]]:
        """Fetch all stock records."""
        return list(self.db.estoque.values())
    
    def _fetch_all_sales(self, query: str, args) -> List[Dict[str, Any]]:
        """Fetch all sales."""
        return list(self.db.vendas.values())
    
    def _update_record(self, query: str, args) -> int:
        """Mock update operation."""
        return 1  # Assume one record updated
    
    def _delete_record(self, query: str, args) -> int:
        """Mock delete operation."""
        return 1  # Assume one record deleted


def create_mock_database_manager() -> MockDatabaseManager:
    """Factory function to create a mock database manager."""
    return MockDatabaseManager()


# Global mock instance for easy access
_mock_db_manager = None

def get_mock_db_manager() -> MockDatabaseManager:
    """Get the global mock database manager instance."""
    global _mock_db_manager
    if _mock_db_manager is None:
        _mock_db_manager = create_mock_database_manager()
    return _mock_db_manager

def reset_mock_database():
    """Reset the mock database to clean state."""
    global _mock_db_manager
    if _mock_db_manager:
        _mock_db_manager.reset()