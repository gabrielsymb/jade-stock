"""
SQLAlchemy ORM Model: SaldoEstoque
Representação da entidade no banco de dados PostgreSQL
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID
import uuid

from sqlalchemy import (
    Column, String, Numeric, Integer, DateTime, 
    ForeignKey, CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates
from sqlalchemy.orm import declarative_base

from wms.infrastructure.database import Base
from wms.domain.saldo_estoque import SaldoEstoque as DomainSaldoEstoque

# Base declarativa centralizada - não usar declarative_base() local


class SaldoEstoqueModel(Base):
    """
    Modelo ORM para SaldoEstoque
    
    Mapeia a tabela wms.saldo_estoque no PostgreSQL
    """
    
    __tablename__ = 'saldo_estoque'
    __table_args__ = (
        {'schema': 'public'}
    )
    
    # Colunas
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    sku_id = Column(String(100), nullable=False)
    endereco_codigo = Column(String(50), nullable=False)
    
    # Saldos
    saldo_disponivel = Column(Numeric(15, 3), nullable=False, default=Decimal('0.0'))
    saldo_avariado = Column(Numeric(15, 3), nullable=False, default=Decimal('0.0'))
    saldo_bloqueado = Column(Numeric(15, 3), nullable=False, default=Decimal('0.0'))
    
    # Auditoria
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = Column(DateTime, nullable=False, default=datetime.utcnow)
    criado_por = Column(UUID(as_uuid=True), nullable=True)
    ultima_atualizacao_por = Column(UUID(as_uuid=True), nullable=True)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'sku_id', 'endereco_codigo', 
                       name='saldo_estoque_unique'),
        CheckConstraint('saldo_disponivel >= 0', 
                       name='saldo_disponivel_nao_negativo'),
        CheckConstraint('saldo_avariado >= 0', 
                       name='saldo_avariado_nao_negativo'),
        CheckConstraint('saldo_bloqueado >= 0', 
                       name='saldo_bloqueado_nao_negativo'),
        Index('idx_saldo_estoque_sku', 'sku_id'),
        Index('idx_saldo_estoque_endereco', 'endereco_codigo'),
        Index('idx_saldo_estoque_tenant', 'tenant_id'),
        Index('idx_saldo_estoque_composto', 'tenant_id', 'sku_id', 'endereco_codigo'),
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
    
    @validates('endereco_codigo')
    def validate_endereco_codigo(self, key, endereco_codigo):
        """Valida código do endereço"""
        if not endereco_codigo or not endereco_codigo.strip():
            raise ValueError("Código do endereço é obrigatório")
        if len(endereco_codigo.strip()) > 50:
            raise ValueError("Código do endereço não pode exceder 50 caracteres")
        return endereco_codigo.strip()
    
    @validates('saldo_disponivel')
    def validate_saldo_disponivel(self, key, saldo_disponivel):
        """Valida saldo disponível"""
        if saldo_disponivel < 0:
            raise ValueError("Saldo disponível não pode ser negativo")
        return saldo_disponivel
    
    @validates('saldo_avariado')
    def validate_saldo_avariado(self, key, saldo_avariado):
        """Valida saldo avariado"""
        if saldo_avariado < 0:
            raise ValueError("Saldo avariado não pode ser negativo")
        return saldo_avariado
    
    @validates('saldo_bloqueado')
    def validate_saldo_bloqueado(self, key, saldo_bloqueado):
        """Valida saldo bloqueado"""
        if saldo_bloqueado < 0:
            raise ValueError("Saldo bloqueado não pode ser negativo")
        return saldo_bloqueado
    
    def to_domain(self) -> DomainSaldoEstoque:
        """
        Converte modelo ORM para entidade de domínio
        
        Returns:
            Instância de SaldoEstoque (domínio)
        """
        return DomainSaldoEstoque(
            sku_id=self.sku_id,
            endereco_codigo=self.endereco_codigo,
            saldo_disponivel=float(self.saldo_disponivel),
            saldo_avariado=float(self.saldo_avariado),
            saldo_bloqueado=float(self.saldo_bloqueado)
        )
    
    @classmethod
    def from_domain(cls, domain: DomainSaldoEstoque) -> "SaldoEstoqueModel":
        """
        Cria modelo ORM a partir da entidade de domínio
        
        Args:
            domain: Entidade de domínio
            
        Returns:
            Instância do modelo ORM
        """
        return cls(
            sku_id=domain.sku_id,
            endereco_codigo=domain.endereco_codigo,
            saldo_disponivel=Decimal(str(domain.saldo_disponivel)),
            saldo_avariado=Decimal(str(domain.saldo_avariado)),
            saldo_bloqueado=Decimal(str(domain.saldo_bloqueado))
        )
    
    def update_from_domain(self, domain: DomainSaldoEstoque):
        """
        Atualiza modelo ORM com dados da entidade de domínio
        
        Args:
            domain: Entidade de domínio com dados atualizados
        """
        self.sku_id = domain.sku_id
        self.endereco_codigo = domain.endereco_codigo
        self.saldo_disponivel = Decimal(str(domain.saldo_disponivel))
        self.saldo_avariado = Decimal(str(domain.saldo_avariado))
        self.saldo_bloqueado = Decimal(str(domain.saldo_bloqueado))
        self.atualizado_em = datetime.utcnow()
    
    def __repr__(self) -> str:
        """Representação string do modelo"""
        return (
            f"<SaldoEstoqueModel("
            f"id={self.id}, "
            f"sku_id='{self.sku_id}', "
            f"endereco='{self.endereco_codigo}', "
            f"disponivel={self.saldo_disponivel}, "
            f"avariado={self.saldo_avariado}, "
            f"bloqueado={self.saldo_bloqueado})>"
        )
