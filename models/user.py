from dataclasses import dataclass
from enum import Enum
from typing import Optional


class UserLevel(Enum):
    """User permission levels."""
    USER = "user"
    ADMIN = "admin"
    OWNER = "owner"
    
    @classmethod
    def from_string(cls, level_str: str) -> 'UserLevel':
        """Convert string to UserLevel enum."""
        try:
            return cls(level_str.lower())
        except ValueError:
            return cls.USER  # Default to user level
    
    def get_priority(self) -> int:
        """Get numeric priority for level comparison."""
        priorities = {
            UserLevel.USER: 1,
            UserLevel.ADMIN: 2,
            UserLevel.OWNER: 3
        }
        return priorities[self]
    
    def can_access(self, required_level: 'UserLevel') -> bool:
        """Check if this level can access a required level."""
        return self.get_priority() >= required_level.get_priority()


@dataclass
class User:
    """User domain model."""
    id: int
    username: str
    level: UserLevel
    chat_id: Optional[int] = None
    password: Optional[str] = None  # Only used during creation/updates
    
    @classmethod
    def from_db_row(cls, row: tuple) -> 'User':
        """Create User from database row."""
        if not row:
            return None
        
        id_, username, password, level, chat_id = row
        return cls(
            id=id_,
            username=username,
            level=UserLevel.from_string(level),
            chat_id=chat_id,
            password=password  # Note: password should be handled carefully
        )
    
    def to_dict(self) -> dict:
        """Convert user to dictionary (without password)."""
        return {
            'id': self.id,
            'username': self.username,
            'level': self.level.value,
            'chat_id': self.chat_id
        }
    
    def has_permission(self, required_level: UserLevel) -> bool:
        """Check if user has required permission level."""
        return self.level.can_access(required_level)


@dataclass
class CreateUserRequest:
    """Request model for creating new users."""
    username: str
    password: str
    level: UserLevel = UserLevel.USER
    
    def validate(self) -> list[str]:
        """Validate the create user request."""
        errors = []
        
        if not self.username or len(self.username.strip()) < 3:
            errors.append("Username must be at least 3 characters")
        
        if not self.password or len(self.password) < 4:
            errors.append("Password must be at least 4 characters")
        
        return errors


@dataclass
class UpdateUserRequest:
    """Request model for updating users."""
    user_id: int
    username: Optional[str] = None
    password: Optional[str] = None
    level: Optional[UserLevel] = None
    chat_id: Optional[int] = None
    
    def has_updates(self) -> bool:
        """Check if request contains any updates."""
        return any([
            self.username is not None,
            self.password is not None,
            self.level is not None,
            self.chat_id is not None
        ])