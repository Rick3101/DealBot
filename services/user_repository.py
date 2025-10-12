from typing import Optional, List
from services.base_repository import BaseRepository
from models.user import User, UserLevel
from utils.input_sanitizer import InputSanitizer
from services.base_service import ValidationError


class UserRepository(BaseRepository):
    """
    Repository for User entities with specialized operations.
    Extends BaseRepository to provide user-specific database operations.
    """

    def __init__(self):
        super().__init__("Usuarios", User, "id")
        # Define columns for User table
        self._column_mappings = ["id", "username", "password", "nivel", "chat_id"]

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username with input sanitization.

        Args:
            username: Username to search for

        Returns:
            User object if found, None otherwise
        """
        try:
            username = InputSanitizer.sanitize_username(username)
            return self.get_one_by_field("username", username)
        except Exception as e:
            self.logger.error(f"Error getting user by username {username}: {e}")
            return None

    def get_user_by_chat_id(self, chat_id: int) -> Optional[User]:
        """
        Get user by Telegram chat ID.

        Args:
            chat_id: Telegram chat ID

        Returns:
            User object if found, None otherwise
        """
        return self.get_one_by_field("chat_id", chat_id)

    def username_exists(self, username: str, exclude_id: Optional[int] = None) -> bool:
        """
        Check if username already exists.

        Args:
            username: Username to check
            exclude_id: Exclude user with this ID (for updates)

        Returns:
            True if username exists, False otherwise
        """
        try:
            username = InputSanitizer.sanitize_username(username)
            return self.exists("username", username, exclude_id)
        except Exception as e:
            self.logger.error(f"Error checking username existence {username}: {e}")
            return False

    def get_users_by_level(self, level: UserLevel) -> List[User]:
        """
        Get all users with specific permission level.

        Args:
            level: UserLevel to filter by

        Returns:
            List of users with the specified level
        """
        return self.get_by_field("nivel", level.value, order_by="username ASC")

    def update_chat_id(self, username: str, chat_id: int) -> Optional[User]:
        """
        Update user's chat ID by username.

        Args:
            username: Username to update
            chat_id: New chat ID

        Returns:
            Updated user object if successful
        """
        try:
            username = InputSanitizer.sanitize_username(username)

            # Find user by username first
            user = self.get_user_by_username(username)
            if not user:
                return None

            # Update chat_id
            return self.update(user.id, {"chat_id": chat_id})

        except Exception as e:
            self.logger.error(f"Error updating chat_id for user {username}: {e}")
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Authenticate user with username and password.

        Args:
            username: Username to authenticate
            password: Password to verify

        Returns:
            User object if authentication successful, None otherwise
        """
        try:
            # Sanitize inputs
            username = InputSanitizer.sanitize_username(username)
            password = InputSanitizer.sanitize_password(password)

            # Query for user with matching credentials
            query = """
                SELECT id, username, password, nivel, chat_id
                FROM Usuarios
                WHERE username = %s AND password = %s
            """
            row = self._execute_query(query, (username, password), fetch_one=True)

            if row:
                return User.from_db_row(row)

            return None

        except Exception as e:
            self.logger.error(f"Authentication error for user {username}: {e}")
            return None

    def create_user(self, username: str, password: str, level: UserLevel = UserLevel.USER) -> Optional[User]:
        """
        Create a new user with validation.

        Args:
            username: Username for new user
            password: Password for new user
            level: Permission level (default: USER)

        Returns:
            Created user object if successful

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Sanitize inputs
            username = InputSanitizer.sanitize_username(username)
            password = InputSanitizer.sanitize_password(password)

            # Check if username already exists
            if self.username_exists(username):
                raise ValidationError(f"Username '{username}' already exists")

            # Create user data
            user_data = {
                "username": username,
                "password": password,
                "nivel": level.value
            }

            return self.create(user_data)

        except Exception as e:
            self.logger.error(f"Error creating user {username}: {e}")
            if isinstance(e, ValidationError):
                raise
            raise ValidationError(f"Failed to create user: {str(e)}")

    def update_user_password(self, user_id: int, new_password: str) -> Optional[User]:
        """
        Update user's password.

        Args:
            user_id: ID of user to update
            new_password: New password

        Returns:
            Updated user object if successful
        """
        try:
            new_password = InputSanitizer.sanitize_password(new_password)
            return self.update(user_id, {"password": new_password})

        except Exception as e:
            self.logger.error(f"Error updating password for user {user_id}: {e}")
            return None

    def update_user_level(self, user_id: int, new_level: UserLevel) -> Optional[User]:
        """
        Update user's permission level.

        Args:
            user_id: ID of user to update
            new_level: New permission level

        Returns:
            Updated user object if successful
        """
        return self.update(user_id, {"nivel": new_level.value})

    def get_all_users(self, order_by: str = "username ASC") -> List[User]:
        """
        Get all users ordered by username.

        Args:
            order_by: ORDER BY clause (default: "username ASC")

        Returns:
            List of all users
        """
        return self.get_all(order_by=order_by)

    def delete_user_by_username(self, username: str) -> bool:
        """
        Delete user by username.

        Args:
            username: Username to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            username = InputSanitizer.sanitize_username(username)
            user = self.get_user_by_username(username)

            if not user:
                return False

            return self.delete(user.id)

        except Exception as e:
            self.logger.error(f"Error deleting user {username}: {e}")
            return False