from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime


@dataclass
class SaleItem:
    """Sale item domain model."""
    id: int
    venda_id: int
    produto_id: int
    quantidade: int
    valor_unitario: float
    produto_nome: Optional[str] = None
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'SaleItem':
        """Create SaleItem from database row."""
        if not row:
            return None
        
        # Handle both old format (5 fields) and new format (6 fields)
        if len(row) == 5:
            id_, venda_id, produto_id, quantidade, valor_unitario = row
            produto_nome = None
        else:
            id_, venda_id, produto_id, quantidade, valor_unitario, produto_nome = row
            
        return cls(
            id=id_,
            venda_id=venda_id,
            produto_id=produto_id,
            quantidade=quantidade,
            valor_unitario=float(valor_unitario),
            produto_nome=produto_nome
        )
    
    def get_total_value(self) -> float:
        """Get total value for this item."""
        return self.quantidade * self.valor_unitario


@dataclass
class Sale:
    """Sale domain model."""
    id: int
    comprador: str
    data: str  # ISO format datetime string
    items: Optional[List[SaleItem]] = None
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'Sale':
        """Create Sale from database row."""
        if not row:
            return None
        
        id_, comprador, data = row
        return cls(
            id=id_,
            comprador=comprador,
            data=str(data)
        )
    
    def get_total_value(self) -> float:
        """Get total value of the sale."""
        if not self.items:
            return 0.0
        
        return sum(item.get_total_value() for item in self.items)
    
    def get_item_count(self) -> int:
        """Get total number of items in the sale."""
        if not self.items:
            return 0
        
        return sum(item.quantidade for item in self.items)


@dataclass
class Payment:
    """Payment domain model."""
    id: int
    venda_id: int
    valor_pago: float
    data_pagamento: str  # ISO format datetime string
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'Payment':
        """Create Payment from database row."""
        if not row:
            return None
        
        id_, venda_id, valor_pago, data_pagamento = row
        return cls(
            id=id_,
            venda_id=venda_id,
            valor_pago=float(valor_pago),
            data_pagamento=str(data_pagamento)
        )


@dataclass
class SaleWithPayments:
    """Sale with payment information."""
    sale: Sale
    payments: List[Payment]
    total_paid: float
    
    @property
    def balance_due(self) -> float:
        """Calculate remaining balance due."""
        return self.sale.get_total_value() - self.total_paid
    
    @property
    def is_fully_paid(self) -> bool:
        """Check if sale is fully paid."""
        return self.balance_due <= 0.01  # Account for floating point precision
    
    @property
    def is_overpaid(self) -> bool:
        """Check if sale is overpaid."""
        return self.balance_due < -0.01


@dataclass
class CreateSaleRequest:
    """Request model for creating sales."""
    comprador: str
    items: List['CreateSaleItemRequest']
    
    def validate(self) -> list[str]:
        """Validate the create sale request."""
        errors = []
        
        if not self.comprador or len(self.comprador.strip()) < 2:
            errors.append("Buyer name must be at least 2 characters")
        
        if not self.items:
            errors.append("Sale must have at least one item")
        
        for i, item in enumerate(self.items):
            item_errors = item.validate()
            for error in item_errors:
                errors.append(f"Item {i+1}: {error}")
        
        return errors
    
    def get_total_value(self) -> float:
        """Get total value of the sale request."""
        return sum(item.quantidade * item.valor_unitario for item in self.items)


@dataclass
class CreateSaleItemRequest:
    """Request model for creating sale items."""
    produto_id: int
    quantidade: int
    valor_unitario: float
    
    def validate(self) -> list[str]:
        """Validate the create sale item request."""
        errors = []
        
        if self.quantidade <= 0:
            errors.append("Quantity must be greater than 0")
        
        if self.valor_unitario < 0:
            errors.append("Unit price cannot be negative")
        
        if self.quantidade > 10000:
            errors.append("Quantity too high (maximum 10,000)")
        
        if self.valor_unitario > 999999.99:
            errors.append("Unit price too high (maximum R$ 999,999.99)")
        
        return errors


@dataclass
class CreatePaymentRequest:
    """Request model for creating payments."""
    venda_id: int
    valor_pago: float
    
    def validate(self) -> list[str]:
        """Validate the create payment request."""
        errors = []
        
        if self.valor_pago <= 0:
            errors.append("Payment amount must be greater than 0")
        
        if self.valor_pago > 999999.99:
            errors.append("Payment amount too high (maximum R$ 999,999.99)")
        
        return errors