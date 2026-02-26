"""
SQLAlchemy ORM Model: MovimentacaoEstoque
Representação da entidade no banco de dados PostgreSQL
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
import uuid

from sqlalchemy import (
    Column, String, Numeric, Integer, DateTime, 
    ForeignKey, CheckConstraint, Index, Text
)
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship, validates
from sqlalchemy.orm import declarative_base

from wms.infrastructure.database import Base
from wms.domain.movimentacao_estoque import (
    MovimentacaoEstoque as DomainMovimentacaoEstoque,
    TipoMovimentacao,
)

# Base declarativa centralizada - não usar declarative_base() local


# SQLAlchemy Enums
TipoMovimentacaoEnum = ENUM(
    TipoMovimentacao,
    name='movimentacao_tipo',
    create_type=True
)


class MovimentacaoEstoqueModel(Base):
    """
    Modelo ORM para MovimentacaoEstoque
    
    Mapeia a tabela wms.movimentacao_estoque no PostgreSQL
    """
    
    __tablename__ = 'movimentacao_estoque'
    __table_args__ = (
        {'schema': 'public'}
    )
    
    # Colunas
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    
    # Identificação
    sku_id = Column(String(100), nullable=False)
    endereco_origem = Column(String(50), nullable=True)
    endereco_destino = Column(String(50), nullable=True)
    
    # Quantidade e tipo
    quantidade = Column(Numeric(15, 3), nullable=False)
    tipo_movimentacao = Column(TipoMovimentacaoEnum, nullable=False)
    
    # Informações adicionais
    motivo = Column(Text, nullable=True)
    documento_referencia = Column(String(100), nullable=True)
    usuario_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Controle temporal
    data_movimentacao = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Auditoria
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        CheckConstraint('quantidade > 0', 
                       name='movimentacao_quantidade_positiva'),
        CheckConstraint(
            "(tipo_movimentacao = 'transferencia' AND endereco_origem IS NOT NULL AND endereco_destino IS NOT NULL) OR "
            "(tipo_movimentacao != 'transferencia')",
            name='movimentacao_transferencia_enderecos'
        ),
        Index('idx_movimentacao_estoque_sku', 'sku_id'),
        Index('idx_movimentacao_estoque_origem', 'endereco_origem'),
        Index('idx_movimentacao_estoque_destino', 'endereco_destino'),
        Index('idx_movimentacao_estoque_data', 'data_movimentacao'),
        Index('idx_movimentacao_estoque_documento', 'documento_referencia'),
        Index('idx_movimentacao_estoque_tenant', 'tenant_id'),
        Index('idx_movimentacao_estoque_composta', 
              'tenant_id', 'sku_id', 'data_movimentacao'),
        {'schema': 'public'}
    )
    
    @validates('sku_id')
    def validate_sku_id(self, key, sku_id):
        """Valida SKU ID"""
        if not sku_id or not sku_id.strip():
            raise ValueError("SKU ID é obrigatório")
        if len(sku_id.strip()) > 100:
            raise ValueError("SKU ID não pode exceder 100 caracteres")
        return sku_id.strip()
    
    @validates('endereco_origem')
    def validate_endereco_origem(self, key, endereco_origem):
        """Valida código do endereço de origem"""
        if endereco_origem:
            endereco_origem = endereco_origem.strip()
            if len(endereco_origem) > 50:
                raise ValueError("Endereço de origem não pode exceder 50 caracteres")
        return endereco_origem
    
    @validates('endereco_destino')
    def validate_endereco_destino(self, key, endereco_destino):
        """Valida código do endereço de destino"""
        if endereco_destino:
            endereco_destino = endereco_destino.strip()
            if len(endereco_destino) > 50:
                raise ValueError("Endereço de destino não pode exceder 50 caracteres")
        return endereco_destino
    
    @validates('quantidade')
    def validate_quantidade(self, key, quantidade):
        """Valida quantidade"""
        if quantidade <= 0:
            raise ValueError("Quantidade deve ser maior que zero")
        return quantidade
    
    @validates('documento_referencia')
    def validate_documento_referencia(self, key, documento_referencia):
        """Valida documento de referência"""
        if documento_referencia:
            documento_referencia = documento_referencia.strip()
            if len(documento_referencia) > 100:
                raise ValueError("Documento de referência não pode exceder 100 caracteres")
        return documento_referencia
    
    def to_domain(self) -> DomainMovimentacaoEstoque:
        """
        Converte modelo ORM para entidade de domínio
        
        Returns:
            Instância de MovimentacaoEstoque (domínio)
        """
        return DomainMovimentacaoEstoque(
            id=self.id,
            tenant_id=self.tenant_id,
            sku_id=self.sku_id,
            endereco_origem=self.endereco_origem,
            endereco_destino=self.endereco_destino,
            quantidade=float(self.quantidade),
            tipo_movimentacao=self.tipo_movimentacao,
            motivo=self.motivo,
            documento_referencia=self.documento_referencia,
            usuario_id=self.usuario_id,
            data_movimentacao=self.data_movimentacao
        )
    
    @classmethod
    def from_domain(cls, domain: DomainMovimentacaoEstoque) -> "MovimentacaoEstoqueModel":
        """
        Cria modelo ORM a partir da entidade de domínio
        
        Args:
            domain: Entidade de domínio
            
        Returns:
            Instância do modelo ORM
        """
        return cls(
            id=domain.id,
            tenant_id=domain.tenant_id,
            sku_id=domain.sku_id,
            endereco_origem=domain.endereco_origem,
            endereco_destino=domain.endereco_destino,
            quantidade=Decimal(str(domain.quantidade)),
            tipo_movimentacao=domain.tipo_movimentacao,
            motivo=domain.motivo,
            documento_referencia=domain.documento_referencia,
            usuario_id=domain.usuario_id,
            data_movimentacao=domain.data_movimentacao
        )
    
    def update_from_domain(self, domain: DomainMovimentacaoEstoque):
        """
        Atualiza modelo ORM com dados da entidade de domínio
        
        Args:
            domain: Entidade de domínio com dados atualizados
        """
        self.tenant_id = domain.tenant_id
        self.sku_id = domain.sku_id
        self.endereco_origem = domain.endereco_origem
        self.endereco_destino = domain.endereco_destino
        self.quantidade = Decimal(str(domain.quantidade))
        self.tipo_movimentacao = domain.tipo_movimentacao
        self.motivo = domain.motivo
        self.documento_referencia = domain.documento_referencia
        self.usuario_id = domain.usuario_id
        self.data_movimentacao = domain.data_movimentacao
        self.atualizado_em = datetime.utcnow()
    
    def __repr__(self) -> str:
        """Representação string do modelo"""
        return (
            f"<MovimentacaoEstoqueModel("
            f"id={self.id}, "
            f"sku_id='{self.sku_id}', "
            f"tipo={self.tipo_movimentacao.value}, "
            f"quantidade={self.quantidade}, "
            f"origem='{self.endereco_origem}', "
            f"destino='{self.endereco_destino}', "
            f"data={self.data_movimentacao})>"
        )
