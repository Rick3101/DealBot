from dataclasses import dataclass
from typing import Optional


@dataclass
class Product:
    """Product domain model."""
    id: int
    nome: str
    emoji: Optional[str] = None
    media_file_id: Optional[str] = None
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'Product':
        """Create Product from database row."""
        if not row:
            return None
        
        id_, nome, emoji, media_file_id = row
        return cls(
            id=id_,
            nome=nome,
            emoji=emoji,
            media_file_id=media_file_id
        )
    
    def to_dict(self) -> dict:
        """Convert product to dictionary."""
        return {
            'id': self.id,
            'nome': self.nome,
            'emoji': self.emoji,
            'media_file_id': self.media_file_id
        }
    
    def get_display_name(self) -> str:
        """Get formatted display name with emoji."""
        if self.emoji:
            return f"{self.emoji} {self.nome}"
        return self.nome
    
    def has_media(self) -> bool:
        """Check if product has associated media."""
        return bool(self.media_file_id and self.media_file_id.strip())


@dataclass
class CreateProductRequest:
    """Request model for creating new products."""
    nome: str
    emoji: Optional[str] = None
    media_file_id: Optional[str] = None
    
    def validate(self) -> list[str]:
        """Validate the create product request."""
        errors = []
        
        if not self.nome or len(self.nome.strip()) < 2:
            errors.append("Product name must be at least 2 characters")
        
        if self.emoji and len(self.emoji) > 10:
            errors.append("Emoji must be 10 characters or less")
        
        return errors


@dataclass
class UpdateProductRequest:
    """Request model for updating products."""
    product_id: int
    nome: Optional[str] = None
    emoji: Optional[str] = None
    media_file_id: Optional[str] = None
    
    def has_updates(self) -> bool:
        """Check if request contains any updates."""
        return any([
            self.nome is not None,
            self.emoji is not None,
            self.media_file_id is not None
        ])


@dataclass
class StockItem:
    """Stock item domain model."""
    id: int
    produto_id: int
    quantidade: int
    valor: float
    custo: float
    data: str  # ISO format datetime string (matches database column name)
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'StockItem':
        """Create StockItem from database row."""
        if not row:
            return None
        
        id_, produto_id, quantidade, preco, custo, data_adicao = row
        return cls(
            id=id_,
            produto_id=produto_id,
            quantidade=quantidade,
            valor=float(preco),  # Map preco to valor
            custo=float(custo),
            data=str(data_adicao) if data_adicao is not None else None  # Map data_adicao to data
        )
    
    def to_dict(self) -> dict:
        """Convert stock item to dictionary."""
        return {
            'id': self.id,
            'produto_id': self.produto_id,
            'quantidade': self.quantidade,
            'valor': self.valor,
            'custo': self.custo,
            'data': self.data
        }
    
    def get_total_value(self) -> float:
        """Get total value (quantidade * valor)."""
        return self.quantidade * self.valor
    
    def get_total_cost(self) -> float:
        """Get total cost (quantidade * custo)."""
        return self.quantidade * self.custo
    
    def get_profit_per_unit(self) -> float:
        """Get profit per unit (valor - custo)."""
        return self.valor - self.custo
    
    def get_total_profit(self) -> float:
        """Get total profit for this stock item."""
        return self.get_profit_per_unit() * self.quantidade


@dataclass
class AddStockRequest:
    """Request model for adding stock."""
    produto_id: int
    quantidade: int
    valor: float
    custo: float
    
    def validate(self) -> list[str]:
        """Validate the add stock request."""
        errors = []
        
        if self.quantidade <= 0:
            errors.append("Quantity must be greater than 0")
        
        if self.valor < 0:
            errors.append("Price cannot be negative")
        
        if self.custo < 0:
            errors.append("Cost cannot be negative")
        
        if self.quantidade > 10000:
            errors.append("Quantity too high (maximum 10,000)")
        
        if self.valor > 999999.99:
            errors.append("Price too high (maximum R$ 999,999.99)")
        
        return errors


@dataclass
class ProductWithStock:
    """Product with current stock information."""
    product: Product
    total_quantity: int
    average_cost: float
    average_price: float
    total_value: float

    @property
    def is_in_stock(self) -> bool:
        """Check if product has stock available."""
        return self.total_quantity > 0

    def get_display_info(self) -> str:
        """Get formatted display information."""
        return f"{self.product.get_display_name()} - Estoque: {self.total_quantity}"

    def to_dict(self) -> dict:
        """Convert product with stock to dictionary for API responses."""
        return {
            "id": self.product.id,
            "name": self.product.nome,
            "emoji": self.product.emoji or "",
            "price": float(self.average_price),
            "stock": self.total_quantity,
            "status": "Ativo" if self.total_quantity > 0 else "Inativo"
        }