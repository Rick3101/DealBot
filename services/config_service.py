"""
Configuration service for accessing application settings from Configuracoes table.
"""

import logging
import random
from typing import Optional, List
from database import get_db_manager
from services.base_service import BaseService

logger = logging.getLogger(__name__)


class ConfigService(BaseService):
    """Service for managing application configuration."""
    
    def __init__(self):
        super().__init__()
    
    def get_config_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get a configuration value by key.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT valor FROM Configuracoes WHERE chave = %s",
                        (key,)
                    )
                    result = cursor.fetchone()
                    
                    if result:
                        return result[0]
                    else:
                        logger.warning(f"Configuration key '{key}' not found, using default: {default}")
                        return default
                        
        except Exception as e:
            logger.error(f"Error getting configuration value for key '{key}': {e}")
            return default
    
    def get_start_messages(self) -> List[str]:
        """
        Get all start messages from database.
        
        Returns:
            List of start message values
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        "SELECT valor FROM Configuracoes WHERE chave = %s",
                        ('frase_start',)
                    )
                    results = cursor.fetchall()
                    
                    if results:
                        return [result[0] for result in results]
                    else:
                        logger.warning("No start messages found in database, using default")
                        return ["Bot inicializado com sucesso!"]
                        
        except Exception as e:
            logger.error(f"Error getting start messages: {e}")
            return ["Bot inicializado com sucesso!"]
    
    def get_random_start_message(self) -> str:
        """
        Get a random start message from database.
        
        Returns:
            Random start message or default if none found
        """
        messages = self.get_start_messages()
        if messages:
            return random.choice(messages)
        return "Bot inicializado com sucesso!"
    
    def get_start_message(self) -> str:
        """Get the start message configuration (legacy method)."""
        return self.get_random_start_message()
    
    def set_config_value(self, key: str, value: str, description: Optional[str] = None) -> bool:
        """
        Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
            description: Optional description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO Configuracoes (chave, valor, descricao, data_atualizacao) 
                        VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
                        ON CONFLICT (chave) 
                        DO UPDATE SET 
                            valor = EXCLUDED.valor,
                            descricao = COALESCE(EXCLUDED.descricao, Configuracoes.descricao),
                            data_atualizacao = CURRENT_TIMESTAMP
                    """, (key, value, description))
                    
                    conn.commit()
                    logger.info(f"Configuration updated: {key} = {value}")
                    return True
                    
        except Exception as e:
            logger.error(f"Error setting configuration value for key '{key}': {e}")
            return False


def get_config_service() -> ConfigService:
    """Get configuration service instance."""
    return ConfigService()