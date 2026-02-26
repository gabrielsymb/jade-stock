"""
SQLAlchemy Model: Endereco
Representação da tabela endereco no PostgreSQL
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import Column, String, Text, Boolean, DateTime, Numeric
from sqlalchemy.orm import validates
from sqlalchemy.ext.declarative import declarative_base

from wms.infrastructure.database import Base

# Base declarativa centralizada - não usar declarative_base() local


class EnderecoModel(Base):
    """
    Modelo ORM para Endereco
    
    Mapeia a tabela endereco do schema core
    """
    
    __tablename__ = 'endereco'
    
    # Colunas
    endereco_codigo = Column(String, primary_key=True)
    zona_codigo = Column(String, nullable=False)
    prateleira_codigo = Column(String, nullable=True)
    posicao_codigo = Column(String, nullable=True)
    tipo_endereco = Column(String, nullable=False)
    ativo = Column(Boolean, nullable=False, default=True)
    capacidade_maxima = Column(Numeric(precision=18, scale=4), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=True)
    correlation_id = Column(String, nullable=True)
    
    @validates('endereco_codigo')
    def validate_endereco_codigo(self, key, endereco_codigo):
        """Valida código do endereço"""
        if not endereco_codigo or not endereco_codigo.strip():
            raise ValueError("Código do endereço é obrigatório")
        return endereco_codigo.strip()
    
    @validates('zona_codigo')
    def validate_zona_codigo(self, key, zona_codigo):
        """Valida código da zona"""
        if not zona_codigo or not zona_codigo.strip():
            raise ValueError("Código da zona é obrigatório")
        return zona_codigo.strip()
    
    @validates('tipo_endereco')
    def validate_tipo_endereco(self, key, tipo_endereco):
        """Valida tipo do endereço"""
        tipos_validos = ['reserva', 'deposito', 'expedição', 'devolução', 'quarentena']
        if tipo_endereco and tipo_endereco not in tipos_validos:
            raise ValueError(f"Tipo de endereço deve ser um de: {', '.join(tipos_validos)}")
        return tipo_endereco
    
    @validates('capacidade_maxima')
    def validate_capacidade_maxima(self, key, capacidade_maxima):
        """Valida capacidade máxima"""
        if capacidade_maxima is not None and capacidade_maxima <= 0:
            raise ValueError("Capacidade máxima deve ser maior que zero")
        return capacidade_maxima
    
    def to_dict(self) -> dict:
        """Converte modelo para dicionário"""
        return {
            'endereco_codigo': self.endereco_codigo,
            'zona_codigo': self.zona_codigo,
            'prateleira_codigo': self.prateleira_codigo,
            'posicao_codigo': self.posicao_codigo,
            'tipo_endereco': self.tipo_endereco,
            'ativo': self.ativo,
            'capacidade_maxima': float(self.capacidade_maxima) if self.capacidade_maxima else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'created_by': self.created_by,
            'correlation_id': self.correlation_id
        }
    
    def __repr__(self) -> str:
        """Representação string do modelo"""
        return (
            f"<EnderecoModel("
            f"codigo='{self.endereco_codigo}', "
            f"zona='{self.zona_codigo}', "
            f"tipo='{self.tipo_endereco}', "
            f"ativo={self.ativo})>"
        )
