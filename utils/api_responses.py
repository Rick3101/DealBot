"""
Standardized API response utilities for consistent error and success responses.

This module provides helper functions to ensure all API endpoints return
consistent response formats, particularly for error handling.
"""

from typing import Any, Dict, Optional, Tuple
from flask import jsonify, Response


class ErrorCode:
    """Standard error codes for API responses."""
    # Authentication & Authorization (401, 403)
    AUTH_REQUIRED = "AUTH_REQUIRED"
    AUTH_INVALID = "AUTH_INVALID"
    PERMISSION_DENIED = "PERMISSION_DENIED"

    # Validation Errors (400)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"
    MISSING_FIELD = "MISSING_FIELD"
    INVALID_FORMAT = "INVALID_FORMAT"

    # Resource Errors (404, 409)
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"

    # Business Logic Errors (422)
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE_VIOLATION"
    INSUFFICIENT_STOCK = "INSUFFICIENT_STOCK"
    INVALID_STATE = "INVALID_STATE"

    # Server Errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"


def error_response(
    message: str,
    status_code: int = 400,
    error_code: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
) -> Tuple[Response, int]:
    """
    Create a standardized error response.

    Args:
        message: Human-readable error description
        status_code: HTTP status code (default: 400)
        error_code: Machine-readable error code (optional)
        details: Additional error details (optional)

    Returns:
        Tuple of (Response, status_code)

    Example:
        return error_response(
            "User not found",
            404,
            ErrorCode.NOT_FOUND,
            {"user_id": user_id}
        )
    """
    error_data = {
        "error": {
            "message": message
        }
    }

    if error_code:
        error_data["error"]["code"] = error_code

    if details:
        error_data["error"]["details"] = details

    return jsonify(error_data), status_code


def success_response(
    data: Any = None,
    message: Optional[str] = None,
    status_code: int = 200
) -> Tuple[Response, int]:
    """
    Create a standardized success response.

    Args:
        data: Response data (dict, list, or any JSON-serializable type)
        message: Optional success message
        status_code: HTTP status code (default: 200)

    Returns:
        Tuple of (Response, status_code)

    Example:
        return success_response(
            {"user": user.to_dict()},
            "User created successfully",
            201
        )
    """
    response_data = {}

    if message:
        response_data["message"] = message

    if data is not None:
        if isinstance(data, dict):
            response_data.update(data)
        else:
            response_data["data"] = data

    return jsonify(response_data), status_code


# Convenience functions for common error types

def auth_required_error(message: str = "Authentication required") -> Tuple[Response, int]:
    """Return 401 authentication required error."""
    return error_response(message, 401, ErrorCode.AUTH_REQUIRED)


def permission_denied_error(message: str = "Permission denied") -> Tuple[Response, int]:
    """Return 403 permission denied error."""
    return error_response(message, 403, ErrorCode.PERMISSION_DENIED)


def not_found_error(resource: str, identifier: Any = None) -> Tuple[Response, int]:
    """Return 404 not found error."""
    message = f"{resource} not found"
    details = {"resource": resource}
    if identifier is not None:
        details["identifier"] = identifier
    return error_response(message, 404, ErrorCode.NOT_FOUND, details)


def validation_error(message: str, details: Optional[Dict[str, Any]] = None) -> Tuple[Response, int]:
    """Return 400 validation error."""
    return error_response(message, 400, ErrorCode.VALIDATION_ERROR, details)


def internal_error(message: str = "Internal server error") -> Tuple[Response, int]:
    """Return 500 internal server error."""
    return error_response(message, 500, ErrorCode.INTERNAL_ERROR)


def business_error(message: str, details: Optional[Dict[str, Any]] = None) -> Tuple[Response, int]:
    """Return 422 business logic violation error."""
    return error_response(message, 422, ErrorCode.BUSINESS_RULE_VIOLATION, details)


# Response wrapper for paginated data
def paginated_response(
    items: list,
    total: int,
    page: int = 1,
    per_page: int = 20,
    status_code: int = 200
) -> Tuple[Response, int]:
    """
    Create a standardized paginated response.

    Args:
        items: List of items for current page
        total: Total number of items
        page: Current page number
        per_page: Items per page
        status_code: HTTP status code (default: 200)

    Returns:
        Tuple of (Response, status_code)

    Example:
        return paginated_response(
            items=[item.to_dict() for item in items],
            total=100,
            page=2,
            per_page=20
        )
    """
    response_data = {
        "items": items,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page  # Ceiling division
        }
    }

    return jsonify(response_data), status_code
