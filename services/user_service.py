from typing import Optional, List
from services.base_service import BaseService, ServiceError, ValidationError, NotFoundError, DuplicateError
from services.user_repository import UserRepository
from services.validation_service import ValidationService
from models.user import User, UserLevel, CreateUserRequest, UpdateUserRequest
from utils.input_sanitizer import InputSanitizer
from core.interfaces import IUserService


class UserService(BaseService, IUserService):
    """
    Service layer for user management.
    Handles authentication, user CRUD operations, and permission management.
    Uses UserRepository for data access operations.
    """

    def __init__(self):
        super().__init__()
        self.user_repository = UserRepository()
        self.validation_service = ValidationService()
    
    def authenticate_user(self, username: str, password: str, chat_id: int) -> Optional[User]:
        """
        Authenticate user and update their chat_id.

        Args:
            username: Username to authenticate
            password: Password to verify
            chat_id: Telegram chat ID to associate

        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            self._log_operation("authenticate_attempt", username=username, chat_id=chat_id)

            # Authenticate user using repository
            user = self.user_repository.authenticate_user(username, password)

            if not user:
                self._log_operation("authenticate_failed", username=username, reason="invalid_credentials")
                return None

            # Update chat_id for the user
            updated_user = self.user_repository.update_chat_id(username, chat_id)

            if updated_user:
                self._log_operation("authenticate_success", username=username, user_id=updated_user.id)
                return updated_user
            else:
                self._log_operation("authenticate_failed", username=username, reason="chat_id_update_failed")
                return None

        except Exception as e:
            self.logger.error(f"Authentication error for user {username}: {e}")
            raise ServiceError(f"Authentication failed: {str(e)}")
    
    def get_user_by_chat_id(self, chat_id: int) -> Optional[User]:
        """
        Get user by their Telegram chat ID.

        Args:
            chat_id: Telegram chat ID

        Returns:
            User object if found, None otherwise
        """
        user = self.user_repository.get_user_by_chat_id(chat_id)

        if user:
            self._log_operation("user_found_by_chat", chat_id=chat_id, username=user.username)

        return user
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.

        Args:
            username: Username to search for

        Returns:
            User object if found, None otherwise
        """
        return self.user_repository.get_user_by_username(username)
    
    def get_user_permission_level(self, chat_id: int) -> Optional[UserLevel]:
        """
        Get user's permission level by chat ID.
        
        Args:
            chat_id: Telegram chat ID
            
        Returns:
            UserLevel if user found, None otherwise
        """
        query = "SELECT nivel FROM Usuarios WHERE chat_id = %s"
        row = self._execute_query(query, (chat_id,), fetch_one=True)
        
        if row:
            return UserLevel.from_string(row[0])
        
        return None
    
    def create_user(self, request: CreateUserRequest) -> User:
        """
        Create a new user.
        
        Args:
            request: User creation request
            
        Returns:
            Created user object
            
        Raises:
            ValidationError: If request is invalid
            DuplicateError: If username already exists
        """
        # Validate request using centralized validation
        errors = self.validation_service.validate_create_request(request, "user")
        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")

        # Additional business rule validation
        business_errors = self.validation_service.validate_business_rules("user", {
            "username": request.username,
            "current_level": None,
            "new_level": request.level
        })
        if business_errors:
            raise ValidationError(f"Business rule validation failed: {', '.join(business_errors)}")

        try:
            user = self.user_repository.create_user(request.username, request.password, request.level)
            self._log_operation("user_created", username=request.username, user_id=user.id, level=request.level.value)
            return user
        except Exception as e:
            self.logger.error(f"Error creating user {request.username}: {e}")
            if isinstance(e, (ValidationError, DuplicateError)):
                raise
            raise ServiceError(f"Failed to create user: {str(e)}")
    
    def update_user(self, request: UpdateUserRequest) -> User:
        """
        Update an existing user.

        Args:
            request: User update request

        Returns:
            Updated user object

        Raises:
            NotFoundError: If user doesn't exist
            ValidationError: If request is invalid
        """
        # Validate request using centralized validation
        errors = self.validation_service.validate_update_request(request, None)  # existing_entity can be None for now
        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")

        # Build update data
        update_data = {}
        update_count = 0

        if request.username is not None:
            try:
                username = InputSanitizer.sanitize_username(request.username)
                # Use centralized validation for business rules
                business_errors = self.validation_service.validate_business_rules("user", {
                    "username": username,
                    "exclude_id": request.user_id
                })
                if business_errors:
                    raise DuplicateError(business_errors[0])  # Take first error

                update_data["username"] = username
                update_count += 1
            except ValueError as e:
                raise ValidationError(f"Invalid username: {str(e)}")

        if request.password is not None:
            try:
                password = InputSanitizer.sanitize_password(request.password)
                # Validate password strength using centralized validation
                password_errors = self.validation_service._validate_password_strength(password)
                if password_errors:
                    raise ValidationError(f"Password validation failed: {', '.join(password_errors)}")

                update_data["password"] = password
                update_count += 1
            except ValueError as e:
                raise ValidationError(f"Invalid password: {str(e)}")

        if request.level is not None:
            # Get current user to validate permission level change
            current_user = self.user_repository.get_by_id(request.user_id)
            if current_user:
                level_errors = self.validation_service._validate_permission_level_change(
                    current_user.level, request.level, None  # requester_level can be passed from context
                )
                if level_errors:
                    raise ValidationError(f"Permission level validation failed: {', '.join(level_errors)}")

            update_data["nivel"] = request.level.value
            update_count += 1

        if request.chat_id is not None:
            update_data["chat_id"] = request.chat_id
            update_count += 1

        try:
            user = self.user_repository.update(request.user_id, update_data)
            self._log_operation("user_updated", user_id=request.user_id, updates=update_count)
            return user
        except Exception as e:
            self.logger.error(f"Error updating user {request.user_id}: {e}")
            if isinstance(e, (NotFoundError, ValidationError, DuplicateError)):
                raise
            raise ServiceError(f"Failed to update user: {str(e)}")
    
    def delete_user(self, user_id: int) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            True if deleted successfully
            
        Raises:
            NotFoundError: If user doesn't exist
        """
        try:
            result = self.user_repository.delete(user_id)
            if result:
                self._log_operation("user_deleted", user_id=user_id)
            return result
        except Exception as e:
            self.logger.error(f"Error deleting user {user_id}: {e}")
            if isinstance(e, NotFoundError):
                raise
            raise ServiceError(f"Failed to delete user: {str(e)}")
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID to search for

        Returns:
            User object if found, None otherwise
        """
        return self.user_repository.get_by_id(user_id)
    
    def get_all_users(self) -> List[User]:
        """
        Get all users.

        Returns:
            List of all users
        """
        users = self.user_repository.get_all_users()
        self._log_operation("users_listed", count=len(users))
        return users

    def get_users_with_stats(self, limit: int = None, offset: int = 0) -> List['UserWithStats']:
        """
        Get all users with purchase statistics.
        Optimized single query for API responses.

        Args:
            limit: Maximum number of users to return (None for all)
            offset: Number of users to skip (for pagination)

        Returns:
            List of UserWithStats objects
        """
        from models.user import UserWithStats

        query = """
            SELECT u.username, u.nivel,
                   COALESCE(SUM(v.preco_total), 0) as total_compras,
                   MAX(v.data_venda) as ultimo_acesso
            FROM Usuarios u
            LEFT JOIN Vendas v ON u.username = v.comprador_nome
            GROUP BY u.username, u.nivel
            ORDER BY total_compras DESC
        """

        params = []
        if limit is not None:
            query += " LIMIT %s OFFSET %s"
            params = [limit, offset]

        results = self._execute_query(query, params if params else None, fetch_all=True)
        return [UserWithStats.from_db_row(row) for row in results or []]

    def username_exists(self, username: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Check if username already exists.

        Args:
            username: Username to check
            exclude_user_id: User ID to exclude from check (for updates)

        Returns:
            True if username exists, False otherwise
        """
        return self.user_repository.username_exists(username, exclude_id=exclude_user_id)
    
    def get_users_by_level(self, level: UserLevel) -> List[User]:
        """
        Get all users with specific permission level.

        Args:
            level: Permission level to filter by

        Returns:
            List of users with the specified level
        """
        return self.user_repository.get_users_by_level(level)