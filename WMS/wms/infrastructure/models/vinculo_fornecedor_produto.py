"""
SQLAlchemy ORM Model: VinculoFornecedorProduto
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
from sqlalchemy.dialects.postgresql import UUID, ENUM
from sqlalchemy.orm import relationship, validates

from wms.domain.vinculo_fornecedor_produto import (
    VinculoFornecedorProduto as DomainVinculo,
    StatusVinculo,
    TipoUnidade
)
from wms.infrastructure.database import Base


# SQLAlchemy Enumsa o fluxo xml 
StatusVinculoEnum = ENUM(
    StatusVinculo,
    name='vinculo_status',
    create_type=True
)

TipoUnidadeEnum = ENUM(
    TipoUnidade,
    name='unidade_medida',
    create_type=True
)


class VinculoFornecedorProdutoModel(Base):
    """
    Modelo ORM para VinculoFornecedorProduto
    
    Mapeia a tabela wms.vinculo_fornecedor_produto no PostgreSQL
    """
    
    __tablename__ = 'vinculo_fornecedor_produto'
    __table_args__ = (
        UniqueConstraint('tenant_id', 'fornecedor_id', 'codigo_fornecedor',
                        name='vinculo_fornecedor_produto_unique'),
        CheckConstraint('fator_conversao > 0', 
                       name='vinculo_fornecedor_produto_fator_positivo'),
        CheckConstraint('vezes_utilizado >= 0', 
                       name='vinculo_fornecedor_produto_uso_nao_negativo'),
        CheckConstraint('peso_confianca >= 0 AND peso_confianca <= 10', 
                       name='ck_peso_confianca_range'),
        Index('idx_vinculo_fornecedor_produto_fornecedor_codigo', 
              'fornecedor_id', 'codigo_fornecedor'),
        Index('idx_vinculo_fornecedor_produto_produto', 'produto_id_interno'),
        Index('idx_vinculo_fornecedor_produto_tenant', 'tenant_id'),
        Index('idx_vinculo_fornecedor_produto_status', 'status'),
        Index('idx_vinculo_fornecedor_produto_estatisticas', 
              'tenant_id', 'status', 'vezes_utilizado'),
        Index('idx_vinculo_fornecedor_produto_codigo_parcial', 
              'codigo_fornecedor', postgresql_ops={'codigo_fornecedor': 'varchar_pattern_ops'}),
        {'schema': 'public'}
    )
    
    # Colunas
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)
    fornecedor_id = Column(String(100), nullable=False)  # CNPJ/CPF ou código do fornecedor
    codigo_fornecedor = Column(String(100), nullable=False)
    produto_id_interno = Column(UUID(as_uuid=True), nullable=False)
    
    # Conversão de unidades
    fator_conversao = Column(Numeric(15, 6), nullable=False, default=Decimal('1.0'))
    unidade_origem = Column(TipoUnidadeEnum, nullable=True)
    unidade_destino = Column(TipoUnidadeEnum, nullable=True)
    
    # Controle de status
    status = Column(StatusVinculoEnum, nullable=False, default=StatusVinculo.ATIVO)
    
    # Estatísticas
    vezes_utilizado = Column(Integer, nullable=False, default=0)
    ultima_importacao = Column(DateTime, nullable=True)
    
    # Configuração de aprendizado
    peso_confianca = Column(Numeric(5, 2), nullable=False, default=Decimal('1.0'))
    
    # Auditoria
    criado_em = Column(DateTime, nullable=False, default=datetime.utcnow)
    atualizado_em = Column(DateTime, nullable=False, default=datetime.utcnow)
    criado_por = Column(UUID(as_uuid=True), nullable=True)
    ultima_validacao = Column(DateTime, nullable=True)
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('tenant_id', 'fornecedor_id', 'codigo_fornecedor', 
                       name='vinculo_fornecedor_produto_unique'),
        CheckConstraint('fator_conversao > 0', 
                       name='vinculo_fornecedor_produto_fator_positivo'),
        CheckConstraint('vezes_utilizado >= 0', 
                       name='vinculo_fornecedor_produto_uso_nao_negativo'),
        CheckConstraint('peso_confianca >= 0 AND peso_confianca <= 10', 
                       name='ck_peso_confianca_range'),
        Index('idx_vinculo_fornecedor_produto_fornecedor_codigo', 
              'fornecedor_id', 'codigo_fornecedor'),
        Index('idx_vinculo_fornecedor_produto_produto', 'produto_id_interno'),
        Index('idx_vinculo_fornecedor_produto_tenant', 'tenant_id'),
        Index('idx_vinculo_fornecedor_produto_status', 'status'),
        Index('idx_vinculo_fornecedor_produto_estatisticas', 
              'tenant_id', 'status', 'vezes_utilizado'),
        Index('idx_vinculo_fornecedor_produto_codigo_parcial', 
              'codigo_fornecedor', postgresql_ops={'codigo_fornecedor': 'varchar_pattern_ops'}),
        {'schema': 'public'}
    )
    
    # Relationships (se existirem as tabelas relacionadas)
    # TODO: Implementar quando FornecedorModel e ProdutoModel forem criados
    # fornecedor = relationship("FornecedorModel", back_populates="vinculos")
    # produto = relationship("ProdutoModel", back_populates="vinculos_fornecedores")
    
    @validates('codigo_fornecedor')
    def validate_codigo_fornecedor(self, key, codigo_fornecedor):
        """Valida código do fornecedor"""
        if not codigo_fornecedor or not codigo_fornecedor.strip():
            raise ValueError("Código do fornecedor é obrigatório")
        if len(codigo_fornecedor.strip()) > 100:
            raise ValueError("Código do fornecedor não pode exceder 100 caracteres")
        return codigo_fornecedor.strip()
    
    @validates('fator_conversao')
    def validate_fator_conversao(self, key, fator_conversao):
        """Valida fator de conversão"""
        if fator_conversao <= 0:
            raise ValueError("Fator de conversão deve ser maior que zero")
        return fator_conversao
    
    @validates('vezes_utilizado')
    def validate_vezes_utilizado(self, key, vezes_utilizado):
        """Valida contador de utilizações"""
        if vezes_utilizado < 0:
            raise ValueError("Vezes utilizado não pode ser negativo")
        return vezes_utilizado
    
    @validates('peso_confianca')
    def validate_peso_confianca(self, key, peso_confianca):
        """Valida peso de confiança"""
        if not (0 <= peso_confianca <= 10):
            raise ValueError("Peso de confiança deve estar entre 0 e 10")
        return peso_confianca
    
    def to_domain(self) -> DomainVinculo:
        """
        Converte modelo ORM para entidade de domínio
        
        Returns:
            Instância de VinculoFornecedorProduto (domínio)
        """
        return DomainVinculo(
            id=self.id,
            tenant_id=self.tenant_id,
            fornecedor_id=self.fornecedor_id,
            codigo_fornecedor=self.codigo_fornecedor,
            produto_id_interno=self.produto_id_interno,
            fator_conversao=self.fator_conversao,
            unidade_origem=self.unidade_origem,
            unidade_destino=self.unidade_destino,
            status=self.status,
            vezes_utilizado=self.vezes_utilizado,
            ultima_importacao=self.ultima_importacao,
            peso_confianca=self.peso_confianca,
            criado_em=self.criado_em,
            atualizado_em=self.atualizado_em,
            criado_por=self.criado_por,
            ultima_validacao=self.ultima_validacao
        )
    
    @classmethod
    def from_domain(cls, domain: DomainVinculo) -> "VinculoFornecedorProdutoModel":
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
            fornecedor_id=domain.fornecedor_id,
            codigo_fornecedor=domain.codigo_fornecedor,
            produto_id_interno=domain.produto_id_interno,
            fator_conversao=domain.fator_conversao,
            unidade_origem=domain.unidade_origem,
            unidade_destino=domain.unidade_destino,
            status=domain.status,
            vezes_utilizado=domain.vezes_utilizado,
            ultima_importacao=domain.ultima_importacao,
            peso_confianca=domain.peso_confianca,
            criado_em=domain.criado_em,
            atualizado_em=domain.atualizado_em,
            criado_por=domain.criado_por,
            ultima_validacao=domain.ultima_validacao
        )
    
    def update_from_domain(self, domain: DomainVinculo):
        """
        Atualiza modelo ORM com dados da entidade de domínio
        
        Args:
            domain: Entidade de domínio com dados atualizados
        """
        self.tenant_id = domain.tenant_id
        self.fornecedor_id = domain.fornecedor_id
        self.codigo_fornecedor = domain.codigo_fornecedor
        self.produto_id_interno = domain.produto_id_interno
        self.fator_conversao = domain.fator_conversao
        self.unidade_origem = domain.unidade_origem
        self.unidade_destino = domain.unidade_destino
        self.status = domain.status
        self.vezes_utilizado = domain.vezes_utilizado
        self.ultima_importacao = domain.ultima_importacao
        self.peso_confianca = domain.peso_confianca
        self.atualizado_em = domain.atualizado_em
        self.criado_por = domain.criado_por
        self.ultima_validacao = domain.ultima_validacao
    
    def __repr__(self) -> str:
        """Representação string do modelo"""
        return (
            f"<VinculoFornecedorProdutoModel("
            f"id={self.id}, "
            f"fornecedor_id={self.fornecedor_id}, "
            f"codigo='{self.codigo_fornecedor}', "
            f"produto_id={self.produto_id_interno}, "
            f"status={self.status.value})"
        )
