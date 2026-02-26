"""
SQLAlchemy Model: ItemMaster
Representação da tabela item_master no PostgreSQL
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.orm import validates
from sqlalchemy.ext.declarative import declarative_base

from wms.infrastructure.database import Base

# Base declarativa centralizada - não usar declarative_base() local


class ItemMasterModel(Base):
    """
    Modelo ORM para ItemMaster
    
    Mapeia a tabela item_master do schema core
    """
    
    __tablename__ = 'item_master'
    
    # Colunas
    item_master_id = Column(String, primary_key=True)
    item_nome = Column(Text, nullable=False)
    categoria_id = Column(String, nullable=True)
    classe_abc = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=True)
    correlation_id = Column(String, nullable=True)
    
    @validates('item_master_id')
    def validate_item_master_id(self, key, item_master_id):
        """Valida ID do item master"""
        if not item_master_id or not item_master_id.strip():
            raise ValueError("ID do item master é obrigatório")
        return item_master_id.strip()
    
    @validates('item_nome')
    def validate_item_nome(self, key, item_nome):
        """Valida nome do item"""
        if not item_nome or not item_nome.strip():
            raise ValueError("Nome do item é obrigatório")
        return item_nome.strip()
    
    def to_dict(self) -> dict:
        """Converte modelo para dicionário"""
        return {
            'item_master_id': self.item_master_id,
            'item_nome': self.item_nome,
            'categoria_id': self.categoria_id,
            'classe_abc': self.classe_abc,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'correlation_id': self.correlation_id
        }
    
    def __repr__(self) -> str:
        """Representação string do modelo"""
        return (
            f"<ItemMasterModel("
            f"id='{self.item_master_id}', "
            f"nome='{self.item_nome}', "
            f"categoria='{self.categoria_id}')"
        )
