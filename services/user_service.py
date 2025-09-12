from typing import Optional, List
from services.base_service import BaseService, ServiceError, ValidationError, NotFoundError, DuplicateError
from models.user import User, UserLevel, CreateUserRequest, UpdateUserRequest
from utils.input_sanitizer import InputSanitizer
from core.interfaces import IUserService


class UserService(BaseService, IUserService):
    """
    Service layer for user management.
    Handles authentication, user CRUD operations, and permission management.
    """
    
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
            # Sanitize inputs
            username = InputSanitizer.sanitize_username(username)
            password = InputSanitizer.sanitize_password(password)
            
            self._log_operation("authenticate_attempt", username=username, chat_id=chat_id)
            
            # Check credentials
            query = "SELECT id, username, password, nivel, chat_id FROM Usuarios WHERE username = %s AND password = %s"
            row = self._execute_query(query, (username, password), fetch_one=True)
            
            if not row:
                self._log_operation("authenticate_failed", username=username, reason="invalid_credentials")
                return None
            
            # Update chat_id for the user
            update_query = "UPDATE Usuarios SET chat_id = %s WHERE username = %s"
            self._execute_query(update_query, (chat_id, username))
            
            user = User.from_db_row(row)
            user.chat_id = chat_id  # Update with new chat_id
            
            self._log_operation("authenticate_success", username=username, user_id=user.id)
            return user
            
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
        query = "SELECT id, username, password, nivel, chat_id FROM Usuarios WHERE chat_id = %s"
        row = self._execute_query(query, (chat_id,), fetch_one=True)
        
        if row:
            user = User.from_db_row(row)
            self._log_operation("user_found_by_chat", chat_id=chat_id, username=user.username)
            return user
        
        return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username.
        
        Args:
            username: Username to search for
            
        Returns:
            User object if found, None otherwise
        """
        try:
            username = InputSanitizer.sanitize_username(username)
            query = "SELECT id, username, password, nivel, chat_id FROM Usuarios WHERE username = %s"
            row = self._execute_query(query, (username,), fetch_one=True)
            
            return User.from_db_row(row) if row else None
            
        except Exception as e:
            self.logger.error(f"Error getting user by username {username}: {e}")
            return None
    
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
        # Validate request
        errors = request.validate()
        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")
        
        # Sanitize inputs
        try:
            username = InputSanitizer.sanitize_username(request.username)
            password = InputSanitizer.sanitize_password(request.password)
        except ValueError as e:
            raise ValidationError(f"Input validation failed: {str(e)}")
        
        # Check if username already exists
        if self.username_exists(username):
            raise DuplicateError(f"Username '{username}' already exists")
        
        # Create user
        query = """
            INSERT INTO Usuarios (username, password, nivel) 
            VALUES (%s, %s, %s) 
            RETURNING id, username, password, nivel, chat_id
        """
        
        try:
            row = self._execute_query(
                query, 
                (username, password, request.level.value), 
                fetch_one=True
            )
            
            if not row:
                raise ServiceError("Failed to create user - no row returned")
            
            user = User.from_db_row(row)
            self._log_operation("user_created", username=username, user_id=user.id, level=request.level.value)
            return user
            
        except Exception as e:
            self.logger.error(f"Error creating user {username}: {e}")
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
        if not request.has_updates():
            raise ValidationError("No updates provided")
        
        # Check if user exists
        existing_user = self.get_user_by_id(request.user_id)
        if not existing_user:
            raise NotFoundError(f"User with ID {request.user_id} not found")
        
        # Build update query dynamically
        updates = []
        params = []
        
        if request.username is not None:
            try:
                username = InputSanitizer.sanitize_username(request.username)
                # Check for duplicate username (excluding current user)
                if self.username_exists(username, exclude_user_id=request.user_id):
                    raise DuplicateError(f"Username '{username}' already exists")
                updates.append("username = %s")
                params.append(username)
            except ValueError as e:
                raise ValidationError(f"Invalid username: {str(e)}")
        
        if request.password is not None:
            try:
                password = InputSanitizer.sanitize_password(request.password)
                updates.append("password = %s")
                params.append(password)
            except ValueError as e:
                raise ValidationError(f"Invalid password: {str(e)}")
        
        if request.level is not None:
            updates.append("nivel = %s")
            params.append(request.level.value)
        
        if request.chat_id is not None:
            updates.append("chat_id = %s")
            params.append(request.chat_id)
        
        # Execute update
        params.append(request.user_id)  # Add user_id for WHERE clause
        query = f"""
            UPDATE Usuarios 
            SET {', '.join(updates)} 
            WHERE id = %s 
            RETURNING id, username, password, nivel, chat_id
        """
        
        try:
            row = self._execute_query(query, tuple(params), fetch_one=True)
            
            if not row:
                raise ServiceError("Failed to update user - no row returned")
            
            user = User.from_db_row(row)
            self._log_operation("user_updated", user_id=request.user_id, updates=len(updates))
            return user
            
        except Exception as e:
            self.logger.error(f"Error updating user {request.user_id}: {e}")
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
        # Check if user exists
        if not self.get_user_by_id(user_id):
            raise NotFoundError(f"User with ID {user_id} not found")
        
        query = "DELETE FROM Usuarios WHERE id = %s"
        rows_affected = self._execute_query(query, (user_id,))
        
        if rows_affected > 0:
            self._log_operation("user_deleted", user_id=user_id)
            return True
        
        return False
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            User object if found, None otherwise
        """
        query = "SELECT id, username, password, nivel, chat_id FROM Usuarios WHERE id = %s"
        row = self._execute_query(query, (user_id,), fetch_one=True)
        
        return User.from_db_row(row) if row else None
    
    def get_all_users(self) -> List[User]:
        """
        Get all users.
        
        Returns:
            List of all users
        """
        query = "SELECT id, username, password, nivel, chat_id FROM Usuarios ORDER BY username"
        rows = self._execute_query(query, fetch_all=True)
        
        users = []
        if rows:
            for row in rows:
                user = User.from_db_row(row)
                if user:
                    users.append(user)
        
        self._log_operation("users_listed", count=len(users))
        return users
    
    def username_exists(self, username: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Check if username already exists.
        
        Args:
            username: Username to check
            exclude_user_id: User ID to exclude from check (for updates)
            
        Returns:
            True if username exists, False otherwise
        """
        if exclude_user_id:
            query = "SELECT 1 FROM Usuarios WHERE username = %s AND id != %s"
            params = (username, exclude_user_id)
        else:
            query = "SELECT 1 FROM Usuarios WHERE username = %s"
            params = (username,)
        
        row = self._execute_query(query, params, fetch_one=True)
        return row is not None
    
    def get_users_by_level(self, level: UserLevel) -> List[User]:
        """
        Get all users with specific permission level.
        
        Args:
            level: Permission level to filter by
            
        Returns:
            List of users with the specified level
        """
        query = "SELECT id, username, password, nivel, chat_id FROM Usuarios WHERE nivel = %s ORDER BY username"
        rows = self._execute_query(query, (level.value,), fetch_all=True)
        
        users = []
        if rows:
            for row in rows:
                user = User.from_db_row(row)
                if user:
                    users.append(user)
        
        return users