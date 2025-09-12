"""
Smart Contract Service - Modern service layer for smart contract operations.
Handles smart contract creation, transaction management, and multi-party confirmations.
"""
import logging
from datetime import datetime
from typing import List, Optional, Tuple
from database import get_db_manager
from core.interfaces import ISmartContractService

logger = logging.getLogger(__name__)

class SmartContractService(ISmartContractService):
    """Service for managing smart contracts and their transactions."""

    def __init__(self, context=None):
        self.db_manager = get_db_manager()
        self.context = context

    def create_smart_contract(self, chat_id: int, codigo: str) -> int:
        """Create a new smart contract."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO SmartContracts (criador_chat_id, codigo, data_criacao)
                        VALUES (%s, %s, %s)
                        RETURNING id
                        """,
                        (chat_id, codigo, datetime.now())
                    )
                    contract_id = cur.fetchone()[0]
                    conn.commit()
                    logger.info(f"Smart contract created: ID={contract_id}, Code={codigo}, Chat={chat_id}")
                    return contract_id
        except Exception as e:
            error_msg = str(e).lower()
            if "duplicate key" in error_msg and "smartcontracts_codigo_key" in error_msg:
                logger.warning(f"Duplicate smart contract code: {codigo}")
                from services.base_service import DuplicateError
                raise DuplicateError(f"Contrato '{codigo}' já existe. Escolha outro código.")
            else:
                logger.error(f"Error creating smart contract: {e}")
                raise

    def get_smart_contract_by_code(self, chat_id: int, codigo: str) -> Optional[Tuple[int, int, str, datetime]]:
        """Get smart contract by code and chat_id."""
        try:
            result = self.db_manager.execute_query(
                "SELECT id, criador_chat_id, codigo, data_criacao FROM SmartContracts WHERE criador_chat_id = %s AND codigo = %s ORDER BY id DESC LIMIT 1",
                (chat_id, codigo),
                fetch='one'
            )
            if result:
                logger.info(f"Smart contract found: ID={result[0]}, Code={codigo}")
            else:
                logger.warning(f"Smart contract not found: Code={codigo}, Chat={chat_id}")
            return result
        except Exception as e:
            logger.error(f"Error getting smart contract: {e}")
            raise

    def add_transaction(self, contrato_id: int, descricao: str, chat_id: int = None) -> int:
        """Add a new transaction to a smart contract."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO Transacoes (contract_id, descricao, chat_id, data_transacao)
                        VALUES (%s, %s, %s, %s)
                        RETURNING id
                        """,
                        (contrato_id, descricao, chat_id or 0, datetime.now())
                    )
                    transaction_id = cur.fetchone()[0]
                    conn.commit()
                    logger.info(f"Transaction added: ID={transaction_id}, Contract={contrato_id}")
                    return transaction_id
        except Exception as e:
            logger.error(f"Error adding transaction: {e}")
            raise

    def list_contract_transactions(self, contrato_id: int) -> List[Tuple[int, str]]:
        """List all transactions for a smart contract."""
        try:
            result = self.db_manager.execute_query(
                "SELECT id, descricao FROM Transacoes WHERE contract_id = %s ORDER BY data_transacao ASC",
                (contrato_id,),
                fetch='all'
            )
            logger.info(f"Listed {len(result)} transactions for contract {contrato_id}")
            return result or []
        except Exception as e:
            logger.error(f"Error listing transactions: {e}")
            raise

    def confirm_transaction(self, transaction_id: int) -> bool:
        """Confirm a transaction (set confirmado = TRUE)."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE Transacoes SET confirmado = TRUE WHERE id = %s",
                        (transaction_id,)
                    )
                    affected = cur.rowcount
                    conn.commit()
                    if affected > 0:
                        logger.info(f"Transaction confirmed: ID={transaction_id}")
                        return True
                    else:
                        logger.warning(f"Transaction not found for confirmation: ID={transaction_id}")
                        return False
        except Exception as e:
            logger.error(f"Error confirming transaction: {e}")
            raise

    def delete_smart_contract(self, contract_id: int) -> bool:
        """Delete a smart contract and all its transactions."""
        try:
            with self.db_manager.get_connection() as conn:
                with conn.cursor() as cur:
                    # First delete all transactions
                    cur.execute(
                        "DELETE FROM Transacoes WHERE contract_id = %s",
                        (contract_id,)
                    )
                    # Then delete the contract
                    cur.execute(
                        "DELETE FROM SmartContracts WHERE id = %s",
                        (contract_id,)
                    )
                    affected = cur.rowcount
                    conn.commit()
                    logger.info(f"Smart contract deleted: ID={contract_id}")
                    return affected > 0
        except Exception as e:
            logger.error(f"Error deleting smart contract: {e}")
            raise

    def get_transaction_details(self, transaction_id: int) -> Optional[Tuple[int, int, str, bool, datetime]]:
        """Get details of a specific transaction."""
        try:
            result = self.db_manager.execute_query(
                "SELECT id, contract_id, descricao, confirmado, data_transacao FROM Transacoes WHERE id = %s",
                (transaction_id,),
                fetch='one'
            )
            return result
        except Exception as e:
            logger.error(f"Error getting transaction details: {e}")
            raise