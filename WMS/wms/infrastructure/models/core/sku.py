"""
SQLAlchemy Model: SKU
Representação da tabela sku no PostgreSQL
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.declarative import declarative_base

from wms.infrastructure.database import Base

# Base declarativa centralizada - não usar declarative_base() local
from .item_master import ItemMasterModel


class SKUModel(Base):
    """
    Modelo ORM para SKU
    
    Mapeia a tabela sku do schema core
    """
    
    __tablename__ = 'sku'
    
    # Colunas
    sku_id = Column(String, primary_key=True)
    sku_codigo = Column(String, nullable=False, unique=True)
    sku_nome = Column(Text, nullable=False)
    item_master_id = Column(String, ForeignKey('item_master.item_master_id'), nullable=True)
    ean = Column(String, nullable=True)
    unidade_medida = Column(String, nullable=True)
    status_ativo = Column(Boolean, nullable=False, default=True)
    variacao_volume = Column(String, nullable=True)
    variacao_cor = Column(String, nullable=True)
    variacao_tamanho = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=True)
    correlation_id = Column(String, nullable=True)
    
    # Relationships
    item_master = relationship("ItemMasterModel", backref="skus")
    
    # Constraints e Índices
    __table_args__ = (
        Index('uq_sku_ean_not_null', 'ean', unique=True, postgresql_where="ean IS NOT NULL"),
        Index('ix_sku_item_master', 'item_master_id'),
        Index('ix_sku_status', 'status_ativo'),
    )
    
    @validates('sku_id')
    def validate_sku_id(self, key, sku_id):
        """Valida ID do SKU"""
        if not sku_id or not sku_id.strip():
            raise ValueError("ID do SKU é obrigatório")
        return sku_id.strip()
    
    @validates('sku_codigo')
    def validate_sku_codigo(self, key, sku_codigo):
        """Valida código do SKU"""
        if not sku_codigo or not sku_codigo.strip():
            raise ValueError("Código do SKU é obrigatório")
        return sku_codigo.strip()
    
    @validates('sku_nome')
    def validate_sku_nome(self, key, sku_nome):
        """Valida nome do SKU"""
        if not sku_nome or not sku_nome.strip():
            raise ValueError("Nome do SKU é obrigatório")
        return sku_nome.strip()
    
    @validates('ean')
    def validate_ean(self, key, ean):
        """Valida código EAN/GTIN"""
        if ean:
            ean = ean.strip()
            # Validação básica de EAN (8, 12, 13 ou 14 dígitos)
            if ean and not ean.isdigit():
                raise ValueError("EAN deve conter apenas dígitos")
            if ean and len(ean) not in [8, 12, 13, 14]:
                raise ValueError("EAN deve ter 8, 12, 13 ou 14 dígitos")
        return ean
    
    def to_dict(self) -> dict:
        """Converte modelo para dicionário"""
        return {
            'sku_id': self.sku_id,
            'sku_codigo': self.sku_codigo,
            'sku_nome': self.sku_nome,
            'item_master_id': self.item_master_id,
            'ean': self.ean,
            'unidade_medida': self.unidade_medida,
            'status_ativo': self.status_ativo,
            'variacao_volume': self.variacao_volume,
            'variacao_cor': self.variacao_cor,
            'variacao_tamanho': self.variacao_tamanho,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'correlation_id': self.correlation_id
        }
    
    def __repr__(self) -> str:
        """Representação string do modelo"""
        return (
            f"<SKUModel("
            f"id='{self.sku_id}', "
            f"codigo='{self.sku_codigo}', "
            f"nome='{self.sku_nome}', "
            f"ean='{self.ean}', "
            f"ativo={self.status_ativo})>"
        )
