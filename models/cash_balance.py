"""
Models for cash balance and revenue tracking system.
"""

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class CashBalance:
    """Current cash balance state."""
    id: Optional[int]
    saldo_atual: Decimal
    data_atualizacao: datetime

    @staticmethod
    def from_db_row(row: tuple) -> 'CashBalance':
        """Create CashBalance from database row."""
        return CashBalance(
            id=row[0],
            saldo_atual=row[1],
            data_atualizacao=row[2]
        )


@dataclass
class CashTransaction:
    """Cash transaction record for balance history."""
    id: Optional[int]
    tipo: str  # 'receita', 'despesa', 'ajuste'
    valor: Decimal
    descricao: Optional[str]
    venda_id: Optional[int]
    pagamento_id: Optional[int]
    usuario_chat_id: Optional[int]
    saldo_anterior: Decimal
    saldo_novo: Decimal
    data_transacao: datetime

    @staticmethod
    def from_db_row(row: tuple) -> 'CashTransaction':
        """Create CashTransaction from database row."""
        return CashTransaction(
            id=row[0],
            tipo=row[1],
            valor=row[2],
            descricao=row[3],
            venda_id=row[4],
            pagamento_id=row[5],
            usuario_chat_id=row[6],
            saldo_anterior=row[7],
            saldo_novo=row[8],
            data_transacao=row[9]
        )


@dataclass
class CreateCashTransactionRequest:
    """Request to create a cash transaction."""
    tipo: str  # 'receita', 'despesa', 'ajuste'
    valor: Decimal
    descricao: Optional[str] = None
    venda_id: Optional[int] = None
    pagamento_id: Optional[int] = None
    usuario_chat_id: Optional[int] = None

    def validate(self) -> List[str]:
        """Validate the transaction request."""
        errors = []

        # Validate transaction type
        valid_tipos = ['receita', 'despesa', 'ajuste']
        if self.tipo not in valid_tipos:
            errors.append(f"Tipo deve ser um de: {', '.join(valid_tipos)}")

        # Validate amount
        if self.valor <= 0:
            errors.append("Valor deve ser maior que zero")

        return errors


@dataclass
class RevenueReport:
    """Revenue and profit report."""
    periodo_inicio: datetime
    periodo_fim: datetime
    total_vendas: Decimal
    total_pagamentos: Decimal
    total_custos: Decimal
    lucro_bruto: Decimal
    lucro_liquido: Decimal
    saldo_atual: Decimal
    total_despesas: Decimal
    transacoes_count: int
    vendas_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'periodo_inicio': self.periodo_inicio.isoformat(),
            'periodo_fim': self.periodo_fim.isoformat(),
            'total_vendas': float(self.total_vendas),
            'total_pagamentos': float(self.total_pagamentos),
            'total_custos': float(self.total_custos),
            'lucro_bruto': float(self.lucro_bruto),
            'lucro_liquido': float(self.lucro_liquido),
            'saldo_atual': float(self.saldo_atual),
            'total_despesas': float(self.total_despesas),
            'transacoes_count': self.transacoes_count,
            'vendas_count': self.vendas_count
        }


@dataclass
class CashBalanceHistory:
    """Cash balance history for a period."""
    transactions: List[CashTransaction]
    balance_start: Decimal
    balance_end: Decimal
    total_receitas: Decimal
    total_despesas: Decimal
    total_ajustes: Decimal

    def to_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        return {
            'transactions_count': len(self.transactions),
            'balance_start': float(self.balance_start),
            'balance_end': float(self.balance_end),
            'total_receitas': float(self.total_receitas),
            'total_despesas': float(self.total_despesas),
            'total_ajustes': float(self.total_ajustes),
            'net_change': float(self.balance_end - self.balance_start)
        }