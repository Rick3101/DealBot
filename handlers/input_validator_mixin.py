"""
Input Validator Mixin - Standardizes input validation patterns across handlers.
Eliminates repetitive validation logic and provides consistent error messages.
"""

from typing import Optional, List, Union, Any, Dict
from abc import ABC
from utils.input_sanitizer import InputSanitizer
from services.validation_service import ValidationService
from decimal import Decimal, InvalidOperation
import re


class InputValidatorMixin(ABC):
    """
    Mixin providing standardized input validation patterns for handlers.
    Eliminates repetitive validation code and ensures consistency.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._validation_service = ValidationService()

    def validate_text_input(self, text: str, field_name: str,
                          min_length: int = 1, max_length: int = 100,
                          sanitizer_method: Optional[str] = None) -> tuple[bool, str, Optional[str]]:
        """
        Validate text input with standardized patterns.

        Args:
            text: Input text to validate
            field_name: Name of the field for error messages
            min_length: Minimum length requirement
            max_length: Maximum length requirement
            sanitizer_method: Method name from InputSanitizer to use

        Returns:
            Tuple of (is_valid: bool, error_message: str, sanitized_value: str)
        """
        if not text or not text.strip():
            return False, f"❌ {field_name} cannot be empty", None

        text = text.strip()

        if len(text) < min_length:
            return False, f"❌ {field_name} must be at least {min_length} characters", None

        if len(text) > max_length:
            return False, f"❌ {field_name} must be less than {max_length} characters", None

        # Apply sanitization if specified
        if sanitizer_method:
            try:
                sanitizer = getattr(InputSanitizer, sanitizer_method)
                sanitized_text = sanitizer(text)
                return True, "", sanitized_text
            except ValueError as e:
                return False, f"❌ Invalid {field_name}: {str(e)}", None
            except AttributeError:
                # Fallback if sanitizer method doesn't exist
                return True, "", text

        return True, "", text

    def validate_username(self, username: str) -> tuple[bool, str, Optional[str]]:
        """Validate username input."""
        return self.validate_text_input(
            username, "username", min_length=3, max_length=50,
            sanitizer_method="sanitize_username"
        )

    def validate_buyer_name(self, buyer_name: str) -> tuple[bool, str, Optional[str]]:
        """Validate buyer name input."""
        return self.validate_text_input(
            buyer_name, "buyer name", min_length=2, max_length=100,
            sanitizer_method="sanitize_buyer_name"
        )

    def validate_product_name(self, product_name: str) -> tuple[bool, str, Optional[str]]:
        """Validate product name input."""
        return self.validate_text_input(
            product_name, "product name", min_length=2, max_length=100,
            sanitizer_method="sanitize_product_name"
        )

    def validate_emoji(self, emoji: str) -> tuple[bool, str, Optional[str]]:
        """Validate emoji input."""
        if not emoji or not emoji.strip():
            return False, "❌ Emoji cannot be empty", None

        try:
            sanitized_emoji = InputSanitizer.sanitize_emoji(emoji.strip())
            return True, "", sanitized_emoji
        except ValueError as e:
            return False, f"❌ Invalid emoji: {str(e)}", None

    def validate_numeric_input(self, value: str, field_name: str,
                             min_value: Optional[float] = None,
                             max_value: Optional[float] = None,
                             allow_decimal: bool = True,
                             decimal_places: int = 2) -> tuple[bool, str, Optional[Union[int, float, Decimal]]]:
        """
        Validate numeric input with standardized patterns.

        Args:
            value: String value to validate
            field_name: Name of the field for error messages
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            allow_decimal: Whether to allow decimal values
            decimal_places: Maximum decimal places if decimals allowed

        Returns:
            Tuple of (is_valid: bool, error_message: str, parsed_value: Union[int, float, Decimal])
        """
        if not value or not value.strip():
            return False, f"❌ {field_name} cannot be empty", None

        value = value.strip().replace(',', '.')  # Handle both comma and dot as decimal separator

        try:
            if allow_decimal:
                # Use Decimal for precise financial calculations
                parsed_value = Decimal(value)

                # Check decimal places
                if abs(parsed_value.as_tuple().exponent) > decimal_places:
                    return False, f"❌ {field_name} cannot have more than {decimal_places} decimal places", None
            else:
                # Integer validation
                if '.' in value or ',' in value:
                    return False, f"❌ {field_name} must be a whole number", None
                parsed_value = int(value)

        except (ValueError, InvalidOperation):
            return False, f"❌ {field_name} must be a valid number", None

        # Range validation
        if min_value is not None and parsed_value < min_value:
            return False, f"❌ {field_name} must be at least {min_value}", None

        if max_value is not None and parsed_value > max_value:
            return False, f"❌ {field_name} must be at most {max_value}", None

        return True, "", parsed_value

    def validate_quantity(self, quantity_str: str) -> tuple[bool, str, Optional[int]]:
        """Validate quantity input (positive integer)."""
        is_valid, error, value = self.validate_numeric_input(
            quantity_str, "quantity", min_value=1, allow_decimal=False
        )
        return is_valid, error, int(value) if value else None

    def validate_price(self, price_str: str) -> tuple[bool, str, Optional[Decimal]]:
        """Validate price input (positive decimal with 2 decimal places)."""
        is_valid, error, value = self.validate_numeric_input(
            price_str, "price", min_value=0.01, allow_decimal=True, decimal_places=2
        )
        return is_valid, error, value

    def validate_cost(self, cost_str: str) -> tuple[bool, str, Optional[Decimal]]:
        """Validate cost input (non-negative decimal with 2 decimal places)."""
        is_valid, error, value = self.validate_numeric_input(
            cost_str, "cost", min_value=0.0, allow_decimal=True, decimal_places=2
        )
        return is_valid, error, value

    def validate_password(self, password: str) -> tuple[bool, str]:
        """Validate password input."""
        if not password:
            return False, "❌ Password cannot be empty"

        if len(password) < 4:
            return False, "❌ Password must be at least 4 characters"

        if len(password) > 100:
            return False, "❌ Password must be less than 100 characters"

        return True, ""

    def validate_selection_input(self, input_text: str, valid_options: List[str],
                                case_sensitive: bool = False) -> tuple[bool, str, Optional[str]]:
        """
        Validate selection input against a list of valid options.

        Args:
            input_text: User input to validate
            valid_options: List of valid option strings
            case_sensitive: Whether validation is case sensitive

        Returns:
            Tuple of (is_valid: bool, error_message: str, matched_option: str)
        """
        if not input_text or not input_text.strip():
            return False, "❌ Selection cannot be empty", None

        input_text = input_text.strip()

        # Direct match
        if case_sensitive:
            if input_text in valid_options:
                return True, "", input_text
        else:
            input_lower = input_text.lower()
            for option in valid_options:
                if option.lower() == input_lower:
                    return True, "", option

        # Partial match
        if not case_sensitive:
            matches = [opt for opt in valid_options if opt.lower().startswith(input_lower)]
            if len(matches) == 1:
                return True, "", matches[0]
            elif len(matches) > 1:
                return False, f"❌ Ambiguous selection. Did you mean: {', '.join(matches[:3])}?", None

        return False, f"❌ Invalid selection. Valid options: {', '.join(valid_options)}", None

    def validate_using_service(self, data: Dict[str, Any], entity_type: str,
                             operation: str = "create") -> tuple[bool, str]:
        """
        Validate using the ValidationService for comprehensive business rule validation.

        Args:
            data: Data to validate
            entity_type: Type of entity (user, product, sale, etc.)
            operation: Type of operation (create, update)

        Returns:
            Tuple of (is_valid: bool, error_message: str)
        """
        try:
            if operation == "create":
                errors = self._validation_service.validate_business_rules(entity_type, data)
            else:
                # For updates, we might need different validation logic
                errors = self._validation_service.validate_business_rules(entity_type, data)

            if errors:
                return False, f"❌ Validation failed: {'; '.join(errors)}"

            return True, ""

        except Exception as e:
            return False, f"❌ Validation error: {str(e)}"

    def create_validation_summary(self, validations: List[tuple[bool, str]]) -> tuple[bool, str]:
        """
        Create a summary of multiple validation results.

        Args:
            validations: List of (is_valid, error_message) tuples

        Returns:
            Tuple of (all_valid: bool, combined_error_message: str)
        """
        errors = [error for is_valid, error in validations if not is_valid and error]

        if errors:
            return False, "\n".join(errors)

        return True, ""