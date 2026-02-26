"""Entidade de dominio Movimentacao de Estoque.

Representa movimentações de estoque entre endereços ou tipos de movimento.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


class TipoMovimentacao(Enum):
    """Tipos de movimentação de estoque"""
    ENTRADA = "entrada"
    SAIDA = "saida"
    TRANSFERENCIA = "transferencia"
    AJUSTE = "ajuste"
    BLOQUEIO = "bloqueio"
    DESBLOQUEIO = "desbloqueio"
    AVARIA = "avaria"


@dataclass
class MovimentacaoEstoque:
    """Entidade que representa uma movimentação de estoque"""
    
    id: Optional[UUID] = None
    tenant_id: UUID = None
    
    # Identificação
    sku_id: str = ""
    endereco_origem: Optional[str] = None
    endereco_destino: Optional[str] = None
    
    # Quantidade e tipo
    quantidade: float = 0.0
    tipo_movimentacao: TipoMovimentacao = TipoMovimentacao.ENTRADA
    
    # Informações adicionais
    motivo: Optional[str] = None
    documento_referencia: Optional[str] = None
    usuario_id: Optional[UUID] = None
    
    # Controle temporal
    data_movimentacao: datetime = None
    
    def __post_init__(self):
        """Validações pós-inicialização"""
        if self.data_movimentacao is None:
            self.data_movimentacao = datetime.utcnow()
        
        # Validações de negócio
        if self.quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        
        # Para transferência, ambos endereços são obrigatórios
        if self.tipo_movimentacao == TipoMovimentacao.TRANSFERENCIA:
            if not self.endereco_origem or not self.endereco_destino:
                raise ValueError("Transferência requer endereço de origem e destino")
        
        # Para entrada/saida, apenas um endereço é necessário
        if self.tipo_movimentacao in [TipoMovimentacao.ENTRADA, TipoMovimentacao.SAIDA]:
            if not self.endereco_destino:
                raise ValueError("Entrada/Saída requer endereço de destino")
    
    @property
    def is_transferencia(self) -> bool:
        """Verifica se é uma movimentação de transferência"""
        return self.tipo_movimentacao == TipoMovimentacao.TRANSFERENCIA
    
    @property
    def is_entrada(self) -> bool:
        """Verifica se é uma movimentação de entrada"""
        return self.tipo_movimentacao == TipoMovimentacao.ENTRADA
    
    @property
    def is_saida(self) -> bool:
        """Verifica se é uma movimentação de saída"""
        return self.tipo_movimentacao == TipoMovimentacao.SAIDA
    
    @property
    def is_ajuste(self) -> bool:
        """Verifica se é uma movimentação de ajuste"""
        return self.tipo_movimentacao == TipoMovimentacao.AJUSTE
    
    def __repr__(self) -> str:
        """Representação string da entidade"""
        return (
            f"<MovimentacaoEstoque("
            f"id={self.id}, "
            f"sku_id='{self.sku_id}', "
            f"tipo={self.tipo_movimentacao.value}, "
            f"quantidade={self.quantidade}, "
            f"origem='{self.endereco_origem}', "
            f"destino='{self.endereco_destino}', "
            f"data={self.data_movimentacao})>"
        )
