import html
import re
from typing import Optional, Union


class InputSanitizer:
    """
    Comprehensive input sanitization for Telegram bot.
    Validates and cleans user inputs to prevent security issues.
    """
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 100, min_length: int = 0, allow_html: bool = False) -> str:
        """
        General text sanitization.
        
        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length
            min_length: Minimum required length
            allow_html: Whether to allow HTML characters
            
        Returns:
            Sanitized text
            
        Raises:
            ValueError: If input is invalid
        """
        if not isinstance(text, str):
            raise ValueError("Entrada deve ser texto")
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Check length constraints
        if len(text) < min_length:
            raise ValueError(f"Texto muito curto (mínimo {min_length} caracteres)")
        
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove null bytes and dangerous control characters
        text = ''.join(c for c in text if ord(c) >= 32 or c in '\t\n\r')
        
        # Escape HTML if not allowed
        if not allow_html:
            text = html.escape(text)
        
        return text
    
    @staticmethod
    def sanitize_username(username: str) -> str:
        """
        Username specific sanitization.
        
        Args:
            username: Username to sanitize
            
        Returns:
            Sanitized username
            
        Raises:
            ValueError: If username is invalid
        """
        if not isinstance(username, str):
            raise ValueError("Nome de usuário deve ser texto")
        
        username = username.strip()
        
        # Length validation
        if len(username) < 3:
            raise ValueError("Nome de usuário deve ter pelo menos 3 caracteres")
        if len(username) > 20:
            raise ValueError("Nome de usuário deve ter no máximo 20 caracteres")
        
        # Character validation - only letters, numbers, underscore
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            raise ValueError("Nome de usuário pode conter apenas letras, números e _")
        
        return username
    
    @staticmethod
    def sanitize_password(password: str) -> str:
        """
        Password sanitization (minimal - preserve user intent).
        
        Args:
            password: Password to sanitize
            
        Returns:
            Sanitized password
            
        Raises:
            ValueError: If password is invalid
        """
        if not isinstance(password, str):
            raise ValueError("Senha deve ser texto")
        
        # Don't strip passwords - spaces might be intentional
        if len(password) < 4:
            raise ValueError("Senha deve ter pelo menos 4 caracteres")
        if len(password) > 128:
            raise ValueError("Senha deve ter no máximo 128 caracteres")
        
        # Check for null bytes and dangerous control characters
        if '\x00' in password:
            raise ValueError("Senha contém caracteres inválidos")
        
        # Remove dangerous control characters but keep common whitespace
        if any(ord(c) < 32 for c in password if c not in '\t\n\r '):
            raise ValueError("Senha contém caracteres inválidos")
        
        return password
    
    @staticmethod
    def sanitize_product_name(name: str) -> str:
        """
        Product name sanitization.
        
        Args:
            name: Product name to sanitize
            
        Returns:
            Sanitized product name
            
        Raises:
            ValueError: If product name is invalid
        """
        name = InputSanitizer.sanitize_text(name, max_length=50, min_length=2)
        
        # Additional validation for product names
        if name.isspace():
            raise ValueError("Nome do produto não pode ser apenas espaços")
        
        return name
    
    @staticmethod
    def sanitize_emoji(emoji: str) -> str:
        """
        Emoji sanitization.
        
        Args:
            emoji: Emoji to sanitize
            
        Returns:
            Sanitized emoji
            
        Raises:
            ValueError: If emoji is invalid
        """
        if not isinstance(emoji, str):
            raise ValueError("Emoji deve ser texto")
        
        emoji = emoji.strip()
        
        if len(emoji) == 0:
            raise ValueError("Emoji não pode estar vazio")
        if len(emoji) > 10:
            raise ValueError("Emoji muito longo")
        
        return emoji
    
    @staticmethod
    def sanitize_quantity(text: str) -> int:
        """
        Quantity number sanitization.
        
        Args:
            text: Quantity text to sanitize
            
        Returns:
            Sanitized quantity as integer
            
        Raises:
            ValueError: If quantity is invalid
        """
        if not isinstance(text, str):
            raise ValueError("Quantidade deve ser texto")
        
        text = text.strip()
        
        # Check if it's a valid integer
        if not text.isdigit():
            raise ValueError("Quantidade deve ser um número inteiro positivo")
        
        try:
            quantity = int(text)
        except ValueError:
            raise ValueError("Formato de quantidade inválido")
        
        # Business logic validation
        if quantity <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        if quantity > 10000:
            raise ValueError("Quantidade muito alta (máximo 10.000)")
        
        return quantity
    
    @staticmethod
    def sanitize_price(text: str) -> float:
        """
        Price number sanitization.
        
        Args:
            text: Price text to sanitize
            
        Returns:
            Sanitized price as float
            
        Raises:
            ValueError: If price is invalid
        """
        if not isinstance(text, str):
            raise ValueError("Preço deve ser texto")
        
        # Allow comma as decimal separator (Brazilian format)
        text = text.replace(",", ".").strip()
        
        # Remove currency symbols if present
        text = re.sub(r'[R$\s]', '', text)
        
        try:
            price = float(text)
        except ValueError:
            raise ValueError("Formato de preço inválido")
        
        # Business logic validation
        if price < 0:
            raise ValueError("Preço não pode ser negativo")
        if price > 999999.99:
            raise ValueError("Preço muito alto (máximo R$ 999.999,99)")
        
        # Round to 2 decimal places
        return round(price, 2)
    
    @staticmethod
    def sanitize_description(description: str) -> str:
        """
        Description sanitization for smart contracts and other long text.
        
        Args:
            description: Description to sanitize
            
        Returns:
            Sanitized description
            
        Raises:
            ValueError: If description is invalid
        """
        return InputSanitizer.sanitize_text(
            description, 
            max_length=500, 
            min_length=5,
            allow_html=False
        )
    
    @staticmethod
    def sanitize_buyer_name(name: str) -> str:
        """
        Buyer name sanitization.
        
        Args:
            name: Buyer name to sanitize
            
        Returns:
            Sanitized buyer name
            
        Raises:
            ValueError: If buyer name is invalid
        """
        return InputSanitizer.sanitize_text(
            name,
            max_length=100,
            min_length=2,
            allow_html=False
        )
    
    @staticmethod
    def sanitize_stock_input(text: str) -> tuple[int, float, float]:
        """
        Stock input sanitization (format: quantity / price / cost).
        
        Args:
            text: Stock input text to sanitize
            
        Returns:
            Tuple of (quantity, price, cost)
            
        Raises:
            ValueError: If stock input is invalid
        """
        if not isinstance(text, str):
            raise ValueError("Entrada de estoque deve ser texto")
        
        text = text.strip()
        
        # Expected format: "quantity / price / cost"
        parts = [part.strip() for part in text.split('/')]
        
        if len(parts) != 3:
            raise ValueError("Formato deve ser: quantidade / preço / custo")
        
        try:
            quantity = InputSanitizer.sanitize_quantity(parts[0])
            price = InputSanitizer.sanitize_price(parts[1])
            cost = InputSanitizer.sanitize_price(parts[2])
        except ValueError as e:
            raise ValueError(f"Erro nos dados: {str(e)}")
        
        # Business logic: cost should not be higher than price (warning, not error)
        if cost > price:
            # Don't raise error, but could log a warning
            pass
        
        return quantity, price, cost