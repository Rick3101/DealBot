"""
Configuration management for the service container and application.
Handles environment variables, service configuration, and application settings.
"""

import os
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum


class Environment(Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    url: str = field(default_factory=lambda: os.getenv("DATABASE_URL"))
    pool_min_connections: int = field(default=1)
    pool_max_connections: int = field(default=20)
    connection_timeout: int = field(default=30)
    query_timeout: int = field(default=60)
    enable_logging: bool = field(default=False)
    
    def __post_init__(self):
        # Set defaults based on environment
        env = os.getenv("ENVIRONMENT", "development").lower()
        if env == "production":
            self.pool_max_connections = 50
            self.enable_logging = False
        elif env == "development":
            self.enable_logging = True


@dataclass
class TelegramConfig:
    """Telegram bot configuration settings."""
    bot_token: str = field(default_factory=lambda: os.getenv("BOT_TOKEN"))
    webhook_url: str = field(default_factory=lambda: os.getenv("RAILWAY_URL", ""))
    webhook_path: str = field(default="")
    use_webhook: bool = field(default=True)
    polling_timeout: int = field(default=10)
    
    def __post_init__(self):
        if self.bot_token:
            self.webhook_path = f"/{self.bot_token}"
        
        # Use polling in development, webhooks in production
        env = os.getenv("ENVIRONMENT", "development").lower()
        self.use_webhook = env == "production" and bool(self.webhook_url)


@dataclass
class ServiceConfig:
    """Service layer configuration settings."""
    enable_caching: bool = field(default=True)
    cache_ttl_seconds: int = field(default=300)  # 5 minutes
    enable_metrics: bool = field(default=True)
    enable_health_checks: bool = field(default=True)
    max_retry_attempts: int = field(default=3)
    retry_delay_seconds: float = field(default=1.0)
    enable_audit_logging: bool = field(default=True)
    secret_menu_phrase: str = field(default_factory=lambda: os.getenv("SECRET_MENU_PHRASE", "wubba lubba dub dub"))
    secret_menu_emojis: list[str] = field(default_factory=lambda: os.getenv("SECRET_MENU_EMOJIS", "🧪,💀").split(","))


@dataclass
class SecurityConfig:
    """Security and authentication configuration."""
    enable_rate_limiting: bool = field(default=True)
    max_requests_per_minute: int = field(default=60)
    session_timeout_minutes: int = field(default=60)
    enable_input_validation: bool = field(default=True)
    enable_sql_injection_protection: bool = field(default=True)
    min_password_length: int = field(default=4)
    max_username_length: int = field(default=50)


@dataclass
class LoggingConfig:
    """Logging configuration settings."""
    level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    format: str = field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    enable_file_logging: bool = field(default=False)
    log_file_path: str = field(default="bot.log")
    max_file_size_mb: int = field(default=10)
    backup_count: int = field(default=5)
    enable_telegram_logging: bool = field(default=False)
    
    def get_log_level(self) -> int:
        """Get numeric log level."""
        level_map = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        return level_map.get(self.level.upper(), logging.INFO)


@dataclass
class ApplicationConfig:
    """Main application configuration."""
    environment: Environment = field(default_factory=lambda: Environment(os.getenv("ENVIRONMENT", "development")))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    port: int = field(default_factory=lambda: int(os.getenv("PORT", "5000")))
    host: str = field(default="0.0.0.0")
    
    # Service configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    telegram: TelegramConfig = field(default_factory=TelegramConfig)
    services: ServiceConfig = field(default_factory=ServiceConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    
    def __post_init__(self):
        # Adjust settings based on environment
        if self.environment == Environment.PRODUCTION:
            self.debug = False
            self.logging.level = "WARNING"
            self.services.enable_caching = True
        elif self.environment == Environment.DEVELOPMENT:
            self.debug = True
            self.logging.level = "DEBUG"
            self.logging.enable_file_logging = True
        elif self.environment == Environment.TESTING:
            self.debug = True
            self.logging.level = "ERROR"
            self.services.enable_caching = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "environment": self.environment.value,
            "debug": self.debug,
            "port": self.port,
            "host": self.host,
            "database": {
                "url": "***HIDDEN***" if self.database.url else "",
                "pool_min_connections": self.database.pool_min_connections,
                "pool_max_connections": self.database.pool_max_connections,
                "connection_timeout": self.database.connection_timeout,
                "query_timeout": self.database.query_timeout,
                "enable_logging": self.database.enable_logging
            },
            "telegram": {
                "bot_token": "***HIDDEN***" if self.telegram.bot_token else "",
                "webhook_url": "***HIDDEN***" if self.telegram.webhook_url else "",
                "use_webhook": self.telegram.use_webhook,
                "polling_timeout": self.telegram.polling_timeout
            },
            "services": {
                "enable_caching": self.services.enable_caching,
                "cache_ttl_seconds": self.services.cache_ttl_seconds,
                "enable_metrics": self.services.enable_metrics,
                "enable_health_checks": self.services.enable_health_checks,
                "max_retry_attempts": self.services.max_retry_attempts,
                "enable_audit_logging": self.services.enable_audit_logging,
                "secret_menu_phrase": "***HIDDEN***" if self.services.secret_menu_phrase else "",
                "secret_menu_emojis": "***HIDDEN***" if self.services.secret_menu_emojis else ""
            },
            "security": {
                "enable_rate_limiting": self.security.enable_rate_limiting,
                "max_requests_per_minute": self.security.max_requests_per_minute,
                "session_timeout_minutes": self.security.session_timeout_minutes,
                "min_password_length": self.security.min_password_length,
                "max_username_length": self.security.max_username_length
            },
            "logging": {
                "level": self.logging.level,
                "enable_file_logging": self.logging.enable_file_logging,
                "enable_telegram_logging": self.logging.enable_telegram_logging
            }
        }
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Validate required settings
        if not self.telegram.bot_token:
            errors.append("BOT_TOKEN environment variable is required")
        
        if not self.database.url:
            errors.append("DATABASE_URL environment variable is required")
        
        if self.port < 1 or self.port > 65535:
            errors.append(f"Invalid port number: {self.port}")
        
        # Validate telegram settings
        if self.telegram.use_webhook and not self.telegram.webhook_url:
            errors.append("RAILWAY_URL required when using webhooks")
        
        # Validate database settings
        if self.database.pool_min_connections < 1:
            errors.append("Database pool_min_connections must be at least 1")
        
        if self.database.pool_max_connections < self.database.pool_min_connections:
            errors.append("Database pool_max_connections must be >= pool_min_connections")
        
        # Validate service settings
        if self.services.cache_ttl_seconds < 1:
            errors.append("Service cache_ttl_seconds must be at least 1")
        
        if self.services.max_retry_attempts < 0:
            errors.append("Service max_retry_attempts cannot be negative")
        
        # Validate security settings
        if self.security.min_password_length < 1:
            errors.append("Security min_password_length must be at least 1")
        
        if self.security.max_username_length < 3:
            errors.append("Security max_username_length must be at least 3")
        
        return errors


# Global configuration instance
_config: Optional[ApplicationConfig] = None


def get_config() -> ApplicationConfig:
    """
    Get the global application configuration.
    
    Returns:
        ApplicationConfig instance
    """
    global _config
    
    if _config is None:
        _config = ApplicationConfig()
        
        # Validate configuration
        errors = _config.validate()
        if errors:
            logger = logging.getLogger(__name__)
            logger.warning(f"Configuration validation errors: {errors}")
    
    return _config


def reload_config() -> ApplicationConfig:
    """
    Reload configuration from environment variables.
    
    Returns:
        New ApplicationConfig instance
    """
    global _config
    _config = None
    return get_config()


def configure_logging(config: Optional[LoggingConfig] = None):
    """
    Configure application logging based on configuration.
    
    Args:
        config: Optional logging configuration, uses global config if None
    """
    if config is None:
        config = get_config().logging
    
    # Configure root logger with UTF-8 encoding for Windows compatibility
    import sys
    
    # Create console handler with UTF-8 encoding 
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(config.get_log_level())
    
    # Set encoding to UTF-8 to handle emojis
    if hasattr(console_handler.stream, 'reconfigure'):
        try:
            console_handler.stream.reconfigure(encoding='utf-8')
        except:
            pass  # Fallback to default if reconfigure fails
    
    formatter = logging.Formatter(config.format)
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(config.get_log_level())
    
    # Clear existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    root_logger.addHandler(console_handler)
    
    # Add file handler if enabled
    if config.enable_file_logging:
        try:
            from logging.handlers import RotatingFileHandler
            
            file_handler = RotatingFileHandler(
                config.log_file_path,
                maxBytes=config.max_file_size_mb * 1024 * 1024,
                backupCount=config.backup_count,
                encoding='utf-8'  # Ensure UTF-8 encoding for file logs
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
            
        except Exception as e:
            logging.getLogger(__name__).warning(f"Failed to setup file logging: {e}")
    
    logging.getLogger(__name__).info(f"Logging configured at {config.level} level")


def print_config_summary():
    """Print a summary of the current configuration."""
    config = get_config()
    
    print("Application Configuration Summary:")
    print(f"   Environment: {config.environment.value}")
    print(f"   Debug Mode: {config.debug}")
    print(f"   Port: {config.port}")
    print(f"   Database Pool: {config.database.pool_min_connections}-{config.database.pool_max_connections}")
    print(f"   Telegram: {'Webhook' if config.telegram.use_webhook else 'Polling'}")
    print(f"   Caching: {'Enabled' if config.services.enable_caching else 'Disabled'}")
    print(f"   Log Level: {config.logging.level}")
    print(f"   Health Checks: {'Enabled' if config.services.enable_health_checks else 'Disabled'}")


# Utility functions for common configuration access
def is_development() -> bool:
    """Check if running in development environment."""
    return get_config().environment == Environment.DEVELOPMENT


def is_production() -> bool:
    """Check if running in production environment."""
    return get_config().environment == Environment.PRODUCTION


def is_testing() -> bool:
    """Check if running in testing environment."""
    return get_config().environment == Environment.TESTING


def get_database_url() -> str:
    """Get database URL from configuration."""
    return get_config().database.url


def get_bot_token() -> str:
    """Get bot token from configuration."""
    return get_config().telegram.bot_token


def get_secret_menu_phrase() -> str:
    """Get secret menu phrase from configuration."""
    return get_config().services.secret_menu_phrase


def get_secret_menu_emojis() -> list[str]:
    """Get secret menu emojis from configuration."""
    return get_config().services.secret_menu_emojis