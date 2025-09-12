"""
Product list generation utilities with secret filtering and multiple output formats.
Centralizes product list generation logic for use across multiple handlers.
"""

from typing import List, Optional, Union
from enum import Enum
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from core.config import get_secret_menu_emojis
from models.product import Product, ProductWithStock
from services.handler_business_service import HandlerBusinessService


class ProductListFormat(Enum):
    """Supported output formats for product lists."""
    KEYBOARD = "keyboard"           # InlineKeyboardMarkup for Telegram
    TEXT_LIST = "text_list"        # Plain text list
    TEXT_WITH_STOCK = "text_stock" # Text with stock information
    NAMES_ONLY = "names_only"      # Just product names
    EMOJI_NAMES = "emoji_names"    # Emoji + name format
    TABLE = "table"                # Table format with inventory details


class ProductListGenerator:
    """
    Utility class for generating product lists with secret filtering 
    and multiple output format support.
    """
    
    @staticmethod
    def get_filtered_products(
        business_service: HandlerBusinessService,
        user_level: str,
        include_secret: bool = False
    ) -> List[ProductWithStock]:
        """
        Get products with secret filtering applied.
        
        Args:
            business_service: Business service instance
            user_level: User's permission level  
            include_secret: Whether to include secret products
            
        Returns:
            List of ProductWithStock objects
        """
        return business_service.get_products_for_purchase(user_level, include_secret)
    
    @staticmethod
    def generate_product_list(
        products: List[ProductWithStock],
        format_type: ProductListFormat,
        user_level: str = "user",
        callback_prefix: str = "product",
        include_actions: bool = True,
        max_items: Optional[int] = None
    ) -> Union[InlineKeyboardMarkup, str, List[str]]:
        """
        Generate product list in specified format.
        
        Args:
            products: List of ProductWithStock objects
            format_type: Output format type
            user_level: User's permission level for display customization
            callback_prefix: Prefix for callback data (keyboard format only)
            include_actions: Whether to include action buttons (keyboard format only)
            max_items: Maximum number of items to include (None for all)
            
        Returns:
            Formatted product list based on format_type
        """
        if max_items:
            products = products[:max_items]
            
        if format_type == ProductListFormat.KEYBOARD:
            return ProductListGenerator._generate_keyboard(
                products, user_level, callback_prefix, include_actions
            )
        elif format_type == ProductListFormat.TEXT_LIST:
            return ProductListGenerator._generate_text_list(products)
        elif format_type == ProductListFormat.TEXT_WITH_STOCK:
            return ProductListGenerator._generate_text_with_stock(products, user_level)
        elif format_type == ProductListFormat.TABLE:
            return ProductListGenerator._generate_table(products, user_level)
        elif format_type == ProductListFormat.NAMES_ONLY:
            return ProductListGenerator._generate_names_only(products)
        elif format_type == ProductListFormat.EMOJI_NAMES:
            return ProductListGenerator._generate_emoji_names(products)
        else:
            raise ValueError(f"Unsupported format type: {format_type}")
    
    @staticmethod
    def _generate_keyboard(
        products: List[ProductWithStock],
        user_level: str,
        callback_prefix: str,
        include_actions: bool
    ) -> InlineKeyboardMarkup:
        """Generate InlineKeyboardMarkup for products."""
        keyboard = []
        
        for pws in products:
            product = pws.product
            
            # Customize display based on user level
            if user_level == "owner":
                display_text = f"{product.emoji} {product.nome} — {pws.total_quantity} unidades"
            else:
                display_text = f"{product.emoji} {product.nome}"
            
            keyboard.append([
                InlineKeyboardButton(display_text, callback_data=f"{callback_prefix}:{product.id}")
            ])
        
        # Add action buttons if requested
        if include_actions:
            # Use specific action names for handler compatibility
            if callback_prefix == "buyproduct":
                keyboard.append([
                    InlineKeyboardButton("✅ Finalizar Compra", callback_data="buy_finalizar"),
                    InlineKeyboardButton("❌ Cancelar", callback_data="buy_cancelar")
                ])
            elif callback_prefix.startswith("estoque") or callback_prefix in ["edit_product", "delete_product"]:
                keyboard.append([
                    InlineKeyboardButton("🚫 Cancelar", callback_data="cancel")
                ])
            else:
                keyboard.append([
                    InlineKeyboardButton("✅ Finalizar", callback_data=f"{callback_prefix}_finalizar"),
                    InlineKeyboardButton("❌ Cancelar", callback_data=f"{callback_prefix}_cancelar")
                ])
        
        return InlineKeyboardMarkup(keyboard)
    
    @staticmethod
    def _generate_text_list(products: List[ProductWithStock]) -> str:
        """Generate plain text list of products."""
        if not products:
            return "Nenhum produto disponível."
        
        lines = []
        for i, pws in enumerate(products, 1):
            product = pws.product
            lines.append(f"{i}. {product.emoji} {product.nome}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _generate_text_with_stock(products: List[ProductWithStock], user_level: str) -> str:
        """Generate text list with stock information."""
        if not products:
            return "Nenhum produto disponível."
        
        lines = []
        for i, pws in enumerate(products, 1):
            product = pws.product
            
            if user_level == "owner":
                lines.append(f"{i}. {product.emoji} {product.nome} ({pws.total_quantity} unidades)")
            else:
                # Don't show stock for non-owners
                lines.append(f"{i}. {product.emoji} {product.nome}")
        
        return "\n".join(lines)
    
    @staticmethod
    def _generate_table(products: List[ProductWithStock], user_level: str) -> str:
        """Generate table format with detailed inventory information."""
        if not products:
            return "Nenhum produto disponível."
        
        if user_level != "owner":
            # For non-owners, fall back to simple list
            return ProductListGenerator._generate_text_list(products)
        
        # Filter to only show products with stock > 0 or with value > 0
        products_to_show = [pws for pws in products if pws.total_quantity > 0 or pws.total_value > 0]
        
        if not products_to_show:
            return "Nenhum produto com estoque encontrado."
        
        # Table headers with fixed column positions using HTML pre tags
        lines = [
            "<pre>",
            "PRODUTO    │  QTD │  PRECO │  CUSTO │   VALOR",
            "───────────┼──────┼────────┼────────┼────────"
        ]
        
        total_value = 0.0
        
        for pws in products_to_show:
            product = pws.product
            
            # Format product name without emoji for table alignment
            product_name = product.nome
            # Limit to 10 characters for consistent spacing
            if len(product_name) > 10:
                product_name = product_name[:7] + "..."
            
            # Use fixed-width formatting with padding
            row = f"{product_name:<10} │ {pws.total_quantity:4d} │ {pws.average_price:6.2f} │ {pws.average_cost:6.2f} │ {pws.total_value:7.2f}"
            lines.append(row)
            
            total_value += pws.total_value
        
        # Add separator and total
        lines.extend([
            "───────────┼──────┼────────┼────────┼────────",
            f"{'TOTAL':<10} │      │        │        │ {total_value:7.2f}",
            "</pre>"
        ])
        
        return "\n".join(lines)
    
    @staticmethod
    def _generate_names_only(products: List[ProductWithStock]) -> List[str]:
        """Generate list of product names only."""
        return [pws.product.nome for pws in products]
    
    @staticmethod
    def _generate_emoji_names(products: List[ProductWithStock]) -> List[str]:
        """Generate list of emoji + name combinations."""
        return [f"{pws.product.emoji} {pws.product.nome}" for pws in products]
    
    @staticmethod
    def is_secret_product(product_emoji: str) -> bool:
        """Check if a product emoji is in the secret list."""
        secret_emojis = set(get_secret_menu_emojis())
        return product_emoji in secret_emojis
    
    @staticmethod
    def filter_secret_products(
        products: List[ProductWithStock], 
        include_secret: bool = False
    ) -> List[ProductWithStock]:
        """
        Manually filter secret products from a list.
        
        Args:
            products: List of ProductWithStock objects
            include_secret: Whether to include secret products
            
        Returns:
            Filtered list of ProductWithStock objects
        """
        if include_secret:
            return products
        
        secret_emojis = set(get_secret_menu_emojis())
        filtered_products = []
        
        for pws in products:
            if pws.product.emoji not in secret_emojis:
                filtered_products.append(pws)
        
        return filtered_products


# Convenience functions for common use cases
def create_product_keyboard(
    business_service: HandlerBusinessService,
    user_level: str,
    include_secret: bool = False,
    callback_prefix: str = "product",
    include_actions: bool = True
) -> InlineKeyboardMarkup:
    """
    Convenience function to create a product selection keyboard.
    
    Args:
        business_service: Business service instance
        user_level: User's permission level
        include_secret: Whether to include secret products
        callback_prefix: Prefix for callback data
        include_actions: Whether to include action buttons
        
    Returns:
        InlineKeyboardMarkup for product selection
    """
    products = ProductListGenerator.get_filtered_products(
        business_service, user_level, include_secret
    )
    
    return ProductListGenerator.generate_product_list(
        products, 
        ProductListFormat.KEYBOARD,
        user_level=user_level,
        callback_prefix=callback_prefix,
        include_actions=include_actions
    )


def create_product_text_list(
    business_service: HandlerBusinessService,
    user_level: str,
    include_secret: bool = False,
    include_stock: bool = False
) -> str:
    """
    Convenience function to create a text list of products.
    
    Args:
        business_service: Business service instance
        user_level: User's permission level
        include_secret: Whether to include secret products
        include_stock: Whether to include stock information
        
    Returns:
        Formatted text string with product list
    """
    products = ProductListGenerator.get_filtered_products(
        business_service, user_level, include_secret
    )
    
    format_type = ProductListFormat.TEXT_WITH_STOCK if include_stock else ProductListFormat.TEXT_LIST
    
    return ProductListGenerator.generate_product_list(
        products,
        format_type,
        user_level=user_level
    )


def create_simple_product_keyboard(
    products: List[Product],
    callback_prefix: str,
    include_secret: bool = False,
    include_actions: bool = True
) -> InlineKeyboardMarkup:
    """
    Convenience function to create a keyboard from regular Product objects.
    
    Args:
        products: List of Product objects
        callback_prefix: Prefix for callback data
        include_secret: Whether to include secret products
        include_actions: Whether to include action buttons
        
    Returns:
        InlineKeyboardMarkup for product selection
    """
    # Filter secret products if needed
    if not include_secret:
        secret_emojis = set(get_secret_menu_emojis())
        products = [p for p in products if p.emoji not in secret_emojis]
    
    # Convert Product objects to ProductWithStock format for compatibility
    products_with_stock = []
    for product in products:
        # Create a mock ProductWithStock with no stock info
        class MockProductWithStock:
            def __init__(self, product):
                self.product = product
                self.total_quantity = 0  # No stock info available
        
        products_with_stock.append(MockProductWithStock(product))
    
    return ProductListGenerator.generate_product_list(
        products_with_stock,
        ProductListFormat.KEYBOARD,
        user_level="user",  # Don't show stock since we don't have it
        callback_prefix=callback_prefix,
        include_actions=include_actions
    )