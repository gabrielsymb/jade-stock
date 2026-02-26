"""
SQLAlchemy Model: HistoricoImportacoes
Representação da tabela historico_importacoes para idempotência
"""

from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID
import uuid

from sqlalchemy import Column, String, Text, DateTime, Numeric, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import validates
from sqlalchemy.ext.declarative import declarative_base

from wms.infrastructure.database import Base

# Base declarativa centralizada - não usar declarative_base() local


class HistoricoImportacoesModel(Base):
    """
    Modelo ORM para Histórico de Importações
    
    Controla idempotência de NF-e e auditoria de processamentos
    """
    
    __tablename__ = 'historico_importacoes'
    
    # Colunas
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chave_acesso = Column(String(44), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    fornecedor_id = Column(UUID(as_uuid=True), nullable=True)
    processamento_id = Column(String(100), nullable=False)
    confirmacao_id = Column(String(100), nullable=True)
    
    # Dados da NF-e
    nota_fiscal = Column(String(20), nullable=True)
    data_emissao = Column(DateTime(timezone=True), nullable=True)
    valor_total = Column(Numeric(precision=18, scale=2), nullable=True)
    
    # Status e Controle
    status = Column(String(20), nullable=False, default='PENDENTE')
    mensagem = Column(Text, nullable=True)
    
    # Auditoria
    criado_em = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    atualizado_em = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    criado_por = Column(UUID(as_uuid=True), nullable=True)
    
    # Dados adicionais
    dados_adicionais = Column(JSONB, nullable=True)
    
    # Constraints e Índices
    __table_args__ = (
        {'schema': 'public'}
    )
    
    @validates('chave_acesso')
    def validate_chave_acesso(self, key, chave_acesso):
        """Valida chave de acesso da NF-e"""
        if not chave_acesso or len(chave_acesso) != 44 or not chave_acesso.isdigit():
            raise ValueError("Chave de acesso deve ter exatos 44 dígitos numéricos")
        return chave_acesso
    
    @validates('status')
    def validate_status(self, key, status):
        """Valida status da importação"""
        statuses_validos = ['PENDENTE', 'PROCESSANDO', 'CONCLUIDO', 'ERRO', 'DUPLICADO']
        if status not in statuses_validos:
            raise ValueError(f"Status deve ser um de: {', '.join(statuses_validos)}")
        return status
    
    @validates('processamento_id')
    def validate_processamento_id(self, key, processamento_id):
        """Valida ID do processamento"""
        if not processamento_id or not processamento_id.strip():
            raise ValueError("ID do processamento é obrigatório")
        return processamento_id.strip()
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte modelo para dicionário"""
        return {
            'id': str(self.id) if self.id else None,
            'chave_acesso': self.chave_acesso,
            'tenant_id': str(self.tenant_id) if self.tenant_id else None,
            'fornecedor_id': str(self.fornecedor_id) if self.fornecedor_id else None,
            'processamento_id': self.processamento_id,
            'confirmacao_id': self.confirmacao_id,
            'nota_fiscal': self.nota_fiscal,
            'data_emissao': self.data_emissao.isoformat() if self.data_emissao else None,
            'valor_total': float(self.valor_total) if self.valor_total else None,
            'status': self.status,
            'mensagem': self.mensagem,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'atualizado_em': self.atualizado_em.isoformat() if self.atualizado_em else None,
            'criado_por': str(self.criado_por) if self.criado_por else None,
            'dados_adicionais': self.dados_adicionais
        }
    
    def __repr__(self) -> str:
        """Representação string do modelo"""
        return (
            f"<HistoricoImportacoesModel("
            f"chave_acesso='{self.chave_acesso}', "
            f"status='{self.status}', "
            f"tenant_id='{self.tenant_id}')>"
        )
