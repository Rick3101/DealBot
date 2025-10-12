from typing import Any, List, Dict, Optional, Union
from services.base_service import BaseService, ValidationError
from services.product_repository import StockRepository
from models.user import UserLevel, CreateUserRequest, UpdateUserRequest
from models.product import CreateProductRequest, UpdateProductRequest
from models.sale import CreateSaleRequest
from utils.input_sanitizer import InputSanitizer
import re


class ValidationService(BaseService):
    """
    Centralized validation logic for all entities.
    Provides unified validation patterns and business rule checking.
    """

    def __init__(self):
        super().__init__()
        self._stock_repository = StockRepository()

    def validate_create_request(self, request: Any, entity_type: str) -> List[str]:
        """
        Generic create validation.

        Args:
            request: Request object to validate
            entity_type: Type of entity being created

        Returns:
            List of validation error messages
        """
        errors = []

        # Delegate to specific validation methods based on entity type
        if entity_type == "user":
            errors.extend(self._validate_user_create_request(request))
        elif entity_type == "product":
            errors.extend(self._validate_product_create_request(request))
        elif entity_type == "sale":
            errors.extend(self._validate_sale_create_request(request))
        else:
            errors.append(f"Unknown entity type: {entity_type}")

        return errors

    def validate_update_request(self, request: Any, existing_entity: Any) -> List[str]:
        """
        Generic update validation.

        Args:
            request: Update request object
            existing_entity: Current entity state

        Returns:
            List of validation error messages
        """
        errors = []

        # Determine entity type and validate accordingly
        if isinstance(request, UpdateUserRequest):
            errors.extend(self._validate_user_update_request(request, existing_entity))
        elif isinstance(request, UpdateProductRequest):
            errors.extend(self._validate_product_update_request(request, existing_entity))
        else:
            errors.append("Unknown update request type")

        return errors

    def check_duplicate(self, table: str, field: str, value: Any, exclude_id: Optional[int] = None) -> bool:
        """
        Generic duplicate checking.

        Args:
            table: Database table name
            field: Field name to check
            value: Value to check for duplicates
            exclude_id: ID to exclude from check (for updates)

        Returns:
            True if duplicate exists, False otherwise
        """
        try:
            where_clause = f"{field} = %s"
            params = [value]

            if exclude_id is not None:
                where_clause += " AND id != %s"
                params.append(exclude_id)

            query = f"SELECT 1 FROM {table} WHERE {where_clause} LIMIT 1"
            result = self._execute_query(query, tuple(params), fetch_one=True)

            return result is not None

        except Exception as e:
            self.logger.error(f"Error checking duplicate in {table}.{field}: {e}")
            return False

    def validate_business_rules(self, entity_type: str, data: Dict) -> List[str]:
        """
        Entity-specific business rule validation.

        Args:
            entity_type: Type of entity
            data: Entity data to validate

        Returns:
            List of validation error messages
        """
        errors = []

        if entity_type == "user":
            errors.extend(self._validate_user_business_rules(data))
        elif entity_type == "product":
            errors.extend(self._validate_product_business_rules(data))
        elif entity_type == "sale":
            errors.extend(self._validate_sale_business_rules(data))

        return errors

    # User-specific validation methods
    def _validate_user_create_request(self, request: CreateUserRequest) -> List[str]:
        """Validate user creation request."""
        errors = []

        # Use the request's built-in validation
        errors.extend(request.validate())

        # Additional business rules
        if request.username:
            errors.extend(self._validate_username_format(request.username))

        if request.password:
            errors.extend(self._validate_password_strength(request.password))

        return errors

    def _validate_user_update_request(self, request: UpdateUserRequest, existing_user: Any) -> List[str]:
        """Validate user update request."""
        errors = []

        if not request.has_updates():
            errors.append("No updates provided")

        if request.username:
            errors.extend(self._validate_username_format(request.username))

        if request.password:
            errors.extend(self._validate_password_strength(request.password))

        return errors

    def _validate_user_business_rules(self, data: Dict) -> List[str]:
        """Validate user business rules."""
        errors = []

        # Check username uniqueness if provided
        if "username" in data and data["username"]:
            if self.check_duplicate("Usuarios", "username", data["username"], data.get("exclude_id")):
                errors.append(f"Username '{data['username']}' already exists")

        # Validate permission level transitions
        if "current_level" in data and "new_level" in data:
            errors.extend(self._validate_permission_level_change(
                data["current_level"], data["new_level"], data.get("requester_level")
            ))

        return errors

    def _validate_username_format(self, username: str) -> List[str]:
        """Validate username format."""
        errors = []

        try:
            sanitized = InputSanitizer.sanitize_username(username)
            if sanitized != username:
                errors.append("Username contains invalid characters")
        except ValueError as e:
            errors.append(f"Invalid username: {str(e)}")

        # Additional format checks
        if len(username) < 3:
            errors.append("Username must be at least 3 characters")
        elif len(username) > 50:
            errors.append("Username must be less than 50 characters")

        if not re.match("^[a-zA-Z0-9_-]+$", username):
            errors.append("Username can only contain letters, numbers, underscores, and hyphens")

        return errors

    def _validate_password_strength(self, password: str) -> List[str]:
        """Validate password strength."""
        errors = []

        if len(password) < 4:
            errors.append("Password must be at least 4 characters")
        elif len(password) > 100:
            errors.append("Password must be less than 100 characters")

        # Additional strength checks for stronger passwords (optional)
        if len(password) >= 8:
            has_upper = any(c.isupper() for c in password)
            has_lower = any(c.islower() for c in password)
            has_digit = any(c.isdigit() for c in password)

            if not (has_upper and has_lower and has_digit):
                # This is a warning, not an error
                self.logger.info("Password could be stronger with uppercase, lowercase, and numbers")

        return errors

    def _validate_permission_level_change(self, current_level: UserLevel, new_level: UserLevel,
                                        requester_level: Optional[UserLevel]) -> List[str]:
        """Validate permission level changes."""
        errors = []

        # Only owners can promote users to owner level
        if new_level == UserLevel.OWNER and requester_level != UserLevel.OWNER:
            errors.append("Only owners can grant owner permissions")

        # Users cannot promote themselves beyond their current level
        if requester_level and new_level.get_priority() > requester_level.get_priority():
            errors.append("Cannot grant higher permissions than your own level")

        return errors

    # Product-specific validation methods
    def _validate_product_create_request(self, request: CreateProductRequest) -> List[str]:
        """Validate product creation request."""
        errors = []

        # Use the request's built-in validation if available
        if hasattr(request, 'validate'):
            errors.extend(request.validate())

        if request.nome:
            errors.extend(self._validate_product_name_format(request.nome))

        if request.emoji:
            errors.extend(self._validate_emoji_format(request.emoji))

        return errors

    def _validate_product_update_request(self, request: UpdateProductRequest, existing_product: Any) -> List[str]:
        """Validate product update request."""
        errors = []

        if hasattr(request, 'nome') and request.nome:
            errors.extend(self._validate_product_name_format(request.nome))

        if hasattr(request, 'emoji') and request.emoji:
            errors.extend(self._validate_emoji_format(request.emoji))

        return errors

    def _validate_product_business_rules(self, data: Dict) -> List[str]:
        """Validate product business rules."""
        errors = []

        # Check product name uniqueness
        if "nome" in data and data["nome"]:
            if self.check_duplicate("Produtos", "nome", data["nome"], data.get("exclude_id")):
                errors.append(f"Product name '{data['nome']}' already exists")

        return errors

    def _validate_product_name_format(self, name: str) -> List[str]:
        """Validate product name format."""
        errors = []

        try:
            sanitized = InputSanitizer.sanitize_product_name(name)
            if sanitized != name:
                errors.append("Product name contains invalid characters")
        except ValueError as e:
            errors.append(f"Invalid product name: {str(e)}")

        if len(name.strip()) < 2:
            errors.append("Product name must be at least 2 characters")
        elif len(name) > 100:
            errors.append("Product name must be less than 100 characters")

        return errors

    def _validate_emoji_format(self, emoji: str) -> List[str]:
        """Validate emoji format."""
        errors = []

        if len(emoji.strip()) == 0:
            errors.append("Emoji cannot be empty")
        elif len(emoji) > 10:
            errors.append("Emoji must be less than 10 characters")

        # Check if it's a valid emoji (basic check)
        if not any(ord(char) > 127 for char in emoji):
            # If no unicode characters, might not be an emoji
            self.logger.warning(f"Emoji might not be valid unicode: {emoji}")

        return errors

    # Sale-specific validation methods
    def _validate_sale_create_request(self, request: CreateSaleRequest) -> List[str]:
        """Validate sale creation request."""
        errors = []

        # Use the request's built-in validation
        if hasattr(request, 'validate'):
            errors.extend(request.validate())

        if request.comprador:
            errors.extend(self._validate_buyer_name_format(request.comprador))

        if hasattr(request, 'items') and request.items:
            for item in request.items:
                errors.extend(self._validate_sale_item(item))

        return errors

    def _validate_sale_business_rules(self, data: Dict) -> List[str]:
        """Validate sale business rules."""
        errors = []

        # Validate buyer name format
        if "comprador" in data:
            errors.extend(self._validate_buyer_name_format(data["comprador"]))

        # Validate stock availability (requires additional context)
        if "items" in data and "check_stock" in data and data["check_stock"]:
            errors.extend(self._validate_stock_availability(data["items"]))

        return errors

    def _validate_buyer_name_format(self, buyer_name: str) -> List[str]:
        """Validate buyer name format."""
        errors = []

        try:
            sanitized = InputSanitizer.sanitize_buyer_name(buyer_name)
            if sanitized != buyer_name:
                errors.append("Buyer name contains invalid characters")
        except ValueError as e:
            errors.append(f"Invalid buyer name: {str(e)}")

        if len(buyer_name.strip()) < 2:
            errors.append("Buyer name must be at least 2 characters")
        elif len(buyer_name) > 100:
            errors.append("Buyer name must be less than 100 characters")

        return errors

    def _validate_sale_item(self, item: Any) -> List[str]:
        """Validate individual sale item."""
        errors = []

        if hasattr(item, 'quantidade') and item.quantidade <= 0:
            errors.append("Item quantity must be greater than 0")

        if hasattr(item, 'valor_unitario') and item.valor_unitario <= 0:
            errors.append("Item unit price must be greater than 0")

        if hasattr(item, 'produto_id') and not item.produto_id:
            errors.append("Item must have a valid product ID")

        return errors

    def _validate_stock_availability(self, items: List[Any]) -> List[str]:
        """Validate stock availability for sale items."""
        errors = []

        for item in items:
            if hasattr(item, 'produto_id') and hasattr(item, 'quantidade'):
                # Use StockRepository to get available stock
                try:
                    available_stock = self._stock_repository.get_available_quantity(item.produto_id)

                    if available_stock < item.quantidade:
                        # Get product name for better error message
                        product_query = "SELECT nome FROM Produtos WHERE id = %s"
                        product_row = self._execute_query(product_query, (item.produto_id,), fetch_one=True)
                        product_name = product_row[0] if product_row else f"Product {item.produto_id}"

                        errors.append(
                            f"Insufficient stock for {product_name}. "
                            f"Available: {available_stock}, Requested: {item.quantidade}"
                        )

                except Exception as e:
                    self.logger.error(f"Error checking stock for product {item.produto_id}: {e}")
                    errors.append(f"Unable to verify stock for product {item.produto_id}")

        return errors

    # Utility validation methods
    def validate_email_format(self, email: str) -> List[str]:
        """Validate email format (if needed for future features)."""
        errors = []

        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            errors.append("Invalid email format")

        return errors

    def validate_phone_format(self, phone: str) -> List[str]:
        """Validate phone format (if needed for future features)."""
        errors = []

        # Basic phone validation - can be enhanced based on requirements
        phone_clean = re.sub(r'[^\d+]', '', phone)
        if len(phone_clean) < 10:
            errors.append("Phone number too short")
        elif len(phone_clean) > 15:
            errors.append("Phone number too long")

        return errors

    def validate_decimal_precision(self, value: Union[float, str], max_precision: int = 2) -> List[str]:
        """Validate decimal precision for monetary values."""
        errors = []

        try:
            from decimal import Decimal, InvalidOperation
            decimal_value = Decimal(str(value))

            # Check precision
            if abs(decimal_value.as_tuple().exponent) > max_precision:
                errors.append(f"Value cannot have more than {max_precision} decimal places")

        except (InvalidOperation, ValueError):
            errors.append("Invalid decimal value")

        return errors