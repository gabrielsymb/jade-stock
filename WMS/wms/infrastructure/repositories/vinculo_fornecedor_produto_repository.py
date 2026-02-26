"""
Repository Pattern: VinculoFornecedorProdutoRepository
Camada de persistência para operações CRUD
"""

from typing import List, Optional, Tuple
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy import select, update, delete, func, and_, or_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from wms.domain.vinculo_fornecedor_produto import (
    VinculoFornecedorProduto,
    StatusVinculo,
    TipoUnidade
)
from wms.infrastructure.models.vinculo_fornecedor_produto import VinculoFornecedorProdutoModel


class VinculoFornecedorProdutoRepository:
    """
    Repository para operações de persistência de VinculoFornecedorProduto
    
    Implementa o padrão Repository, abstraindo detalhes do SQLAlchemy
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session

    @staticmethod
    def _to_fornecedor_id(value: UUID | str) -> str:
        return str(value)
    
    async def create(self, vinculo: VinculoFornecedorProduto) -> VinculoFornecedorProduto:
        """
        Cria um novo vínculo fornecedor-produto
        
        Args:
            vinculo: Entidade de domínio a ser persistida
            
        Returns:
            Entidade persistida com ID gerado
            
        Raises:
            IntegrityError: Se violar constraint de unicidade
        """
        model = VinculoFornecedorProdutoModel.from_domain(vinculo)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        
        return model.to_domain()
    
    async def get_by_id(self, tenant_id: UUID, vinculo_id: UUID) -> Optional[VinculoFornecedorProduto]:
        """
        Busca vínculo por ID
        
        Args:
            tenant_id: ID do tenant
            vinculo_id: ID do vínculo
            
        Returns:
            Entidade encontrada ou None
        """
        stmt = select(VinculoFornecedorProdutoModel).where(
            and_(
                VinculoFornecedorProdutoModel.tenant_id == tenant_id,
                VinculoFornecedorProdutoModel.id == vinculo_id
            )
        )
        
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return model.to_domain() if model else None
    
    async def get_by_codigo_fornecedor(
        self, 
        tenant_id: UUID, 
        fornecedor_id: UUID | str, 
        codigo_fornecedor: str
    ) -> Optional[VinculoFornecedorProduto]:
        """
        Busca vínculo por código do fornecedor (consulta principal de importação)
        
        Args:
            tenant_id: ID do tenant
            fornecedor_id: ID do fornecedor
            codigo_fornecedor: Código do produto no fornecedor
            
        Returns:
            Entidade encontrada ou None
        """
        stmt = select(VinculoFornecedorProdutoModel).where(
            and_(
                VinculoFornecedorProdutoModel.tenant_id == tenant_id,
                VinculoFornecedorProdutoModel.fornecedor_id == self._to_fornecedor_id(fornecedor_id),
                VinculoFornecedorProdutoModel.codigo_fornecedor == codigo_fornecedor,
                VinculoFornecedorProdutoModel.status == StatusVinculo.ATIVO
            )
        )
        
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        return model.to_domain() if model else None
    
    async def list_by_tenant(
        self, 
        tenant_id: UUID,
        status: Optional[StatusVinculo] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[VinculoFornecedorProduto], int]:
        """
        Lista vínculos por tenant com paginação
        
        Args:
            tenant_id: ID do tenant
            status: Filtro por status (opcional)
            limit: Limite de resultados
            offset: Offset para paginação
            
        Returns:
            Tupla (lista de vínculos, total de registros)
        """
        # Query base
        base_query = select(VinculoFornecedorProdutoModel).where(
            VinculoFornecedorProdutoModel.tenant_id == tenant_id
        )
        
        # Aplicar filtro de status se fornecido
        if status:
            base_query = base_query.where(
                VinculoFornecedorProdutoModel.status == status
            )
        
        # Query para contagem
        count_query = select(func.count()).select_from(
            base_query.subquery()
        )
        
        # Query para dados com paginação
        data_query = base_query.order_by(
            VinculoFornecedorProdutoModel.criado_em.desc()
        ).limit(limit).offset(offset)
        
        # Executar queries
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        data_result = await self.session.execute(data_query)
        models = data_result.scalars().all()
        
        vinculos = [model.to_domain() for model in models]
        
        return vinculos, total
    
    async def list_by_fornecedor(
        self, 
        tenant_id: UUID,
        fornecedor_id: UUID | str,
        status: Optional[StatusVinculo] = None
    ) -> List[VinculoFornecedorProduto]:
        """
        Lista vínculos por fornecedor
        
        Args:
            tenant_id: ID do tenant
            fornecedor_id: ID do fornecedor
            status: Filtro por status (opcional)
            
        Returns:
            Lista de vínculos do fornecedor
        """
        stmt = select(VinculoFornecedorProdutoModel).where(
            and_(
                VinculoFornecedorProdutoModel.tenant_id == tenant_id,
                VinculoFornecedorProdutoModel.fornecedor_id == self._to_fornecedor_id(fornecedor_id)
            )
        )
        
        if status:
            stmt = stmt.where(
                VinculoFornecedorProdutoModel.status == status
            )
        
        stmt = stmt.order_by(
            VinculoFornecedorProdutoModel.vezes_utilizado.desc(),
            VinculoFornecedorProdutoModel.codigo_fornecedor
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [model.to_domain() for model in models]
    
    async def list_by_produto(
        self, 
        tenant_id: UUID,
        produto_id: UUID | None = None,
        produto_id_interno: UUID | None = None,
        status: Optional[StatusVinculo] = None
    ) -> List[VinculoFornecedorProduto]:
        """
        Lista vínculos por produto interno
        
        Args:
            tenant_id: ID do tenant
            produto_id: ID do produto
            status: Filtro por status (opcional)
            
        Returns:
            Lista de vínculos do produto
        """
        produto_id_ref = produto_id_interno or produto_id
        if produto_id_ref is None:
            raise ValueError("produto_id ou produto_id_interno é obrigatório")

        stmt = select(VinculoFornecedorProdutoModel).where(
            and_(
                VinculoFornecedorProdutoModel.tenant_id == tenant_id,
                VinculoFornecedorProdutoModel.produto_id_interno == produto_id_ref
            )
        )
        
        if status:
            stmt = stmt.where(
                VinculoFornecedorProdutoModel.status == status
            )
        
        stmt = stmt.order_by(
            VinculoFornecedorProdutoModel.vezes_utilizado.desc(),
            VinculoFornecedorProdutoModel.ultima_importacao.desc().nulls_last()
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [model.to_domain() for model in models]
    
    async def search_by_codigo_parcial(
        self, 
        tenant_id: UUID,
        codigo_parcial: str,
        limite: int = 10
    ) -> List[VinculoFornecedorProduto]:
        """
        Busca vínculos por código parcial (autocomplete)
        
        Args:
            tenant_id: ID do tenant
            codigo_parcial: Parte do código para busca
            limite: Limite de resultados
            
        Returns:
            Lista de vínculos encontrados
        """
        stmt = select(VinculoFornecedorProdutoModel).where(
            and_(
                VinculoFornecedorProdutoModel.tenant_id == tenant_id,
                VinculoFornecedorProdutoModel.status == StatusVinculo.ATIVO,
                VinculoFornecedorProdutoModel.codigo_fornecedor.ilike(f'%{codigo_parcial}%')
            )
        ).order_by(
            VinculoFornecedorProdutoModel.vezes_utilizado.desc(),
            VinculoFornecedorProdutoModel.codigo_fornecedor
        ).limit(limite)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [model.to_domain() for model in models]
    
    async def update(self, vinculo: VinculoFornecedorProduto) -> VinculoFornecedorProduto:
        """
        Atualiza vínculo existente
        
        Args:
            vinculo: Entidade com dados atualizados
            
        Returns:
            Entidade atualizada
            
        Raises:
            ValueError: Se vínculo não existir
        """
        stmt = update(VinculoFornecedorProdutoModel).where(
            and_(
                VinculoFornecedorProdutoModel.tenant_id == vinculo.tenant_id,
                VinculoFornecedorProdutoModel.id == vinculo.id
            )
        ).values(
            fornecedor_id=vinculo.fornecedor_id,
            codigo_fornecedor=vinculo.codigo_fornecedor,
            produto_id_interno=vinculo.produto_id_interno,
            fator_conversao=vinculo.fator_conversao,
            unidade_origem=vinculo.unidade_origem,
            unidade_destino=vinculo.unidade_destino,
            status=vinculo.status,
            vezes_utilizado=vinculo.vezes_utilizado,
            ultima_importacao=vinculo.ultima_importacao,
            peso_confianca=vinculo.peso_confianca,
            atualizado_em=datetime.utcnow(),
            criado_por=vinculo.criado_por,
            ultima_validacao=vinculo.ultima_validacao
        ).returning(VinculoFornecedorProdutoModel)
        
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if not model:
            raise ValueError(f"Vínculo {vinculo.id} não encontrado")
        
        return model.to_domain()
    
    async def registrar_utilizacao(
        self, 
        tenant_id: UUID, 
        vinculo_id: UUID,
        data_utilizacao: Optional[datetime] = None
    ) -> bool:
        """
        Incrementa contador de utilização do vínculo (operação otimizada)
        
        Args:
            tenant_id: ID do tenant
            vinculo_id: ID do vínculo
            data_utilizacao: Data da utilização (padrão: agora)
            
        Returns:
            True se atualizado com sucesso
        """
        data = data_utilizacao or datetime.utcnow()
        
        stmt = update(VinculoFornecedorProdutoModel).where(
            and_(
                VinculoFornecedorProdutoModel.tenant_id == tenant_id,
                VinculoFornecedorProdutoModel.id == vinculo_id,
                VinculoFornecedorProdutoModel.status == StatusVinculo.ATIVO
            )
        ).values(
            vezes_utilizado=VinculoFornecedorProdutoModel.vezes_utilizado + 1,
            ultima_importacao=data,
            atualizado_em=datetime.utcnow()
        )
        
        result = await self.session.execute(stmt)
        return result.rowcount > 0
    
    async def delete(self, tenant_id: UUID, vinculo_id: UUID) -> bool:
        """
        Remove vínculo (soft delete via status)
        
        Args:
            tenant_id: ID do tenant
            vinculo_id: ID do vínculo
            
        Returns:
            True se removido com sucesso
        """
        stmt = update(VinculoFornecedorProdutoModel).where(
            and_(
                VinculoFornecedorProdutoModel.tenant_id == tenant_id,
                VinculoFornecedorProdutoModel.id == vinculo_id
            )
        ).values(
            status=StatusVinculo.INATIVO,
            atualizado_em=datetime.utcnow()
        )
        
        result = await self.session.execute(stmt)
        return result.rowcount > 0
    
    async def get_estatisticas_fornecedor(
        self, 
        tenant_id: UUID,
        fornecedor_id: UUID | str
    ) -> dict:
        """
        Obtém estatísticas de vínculos por fornecedor
        
        Args:
            tenant_id: ID do tenant
            fornecedor_id: ID do fornecedor
            
        Returns:
            Dicionário com estatísticas
        """
        stmt = select(
            func.count().label('total_vinculos'),
            func.sum(VinculoFornecedorProdutoModel.vezes_utilizado).label('total_utilizacoes'),
            func.max(VinculoFornecedorProdutoModel.vezes_utilizado).label('max_utilizacoes'),
            func.avg(VinculoFornecedorProdutoModel.peso_confianca).label('avg_peso_confianca'),
            func.max(VinculoFornecedorProdutoModel.ultima_importacao).label('ultima_importacao'),
            func.sum(
                case(
                    (VinculoFornecedorProdutoModel.status == StatusVinculo.ATIVO, 1),
                    else_=0,
                )
            ).label('vinculos_ativos')
        ).where(
            and_(
                VinculoFornecedorProdutoModel.tenant_id == tenant_id,
                VinculoFornecedorProdutoModel.fornecedor_id == self._to_fornecedor_id(fornecedor_id)
            )
        )
        
        result = await self.session.execute(stmt)
        row = result.first()
        
        return {
            'total_vinculos': row.total_vinculos or 0,
            'vinculos_ativos': row.vinculos_ativos or 0,
            'total_utilizacoes': int(row.total_utilizacoes or 0),
            'max_utilizacoes': row.max_utilizacoes or 0,
            'avg_peso_confianca': float(row.avg_peso_confianca or 0),
            'ultima_importacao': row.ultima_importacao
        }
    
    async def get_vinculos_recentes(
        self, 
        tenant_id: UUID,
        dias: int = 30
    ) -> List[VinculoFornecedorProduto]:
        """
        Lista vínculos criados recentemente
        
        Args:
            tenant_id: ID do tenant
            dias: Número de dias para considerar
            
        Returns:
            Lista de vínculos recentes
        """
        data_limite = datetime.utcnow() - timedelta(days=dias)
        
        stmt = select(VinculoFornecedorProdutoModel).where(
            and_(
                VinculoFornecedorProdutoModel.tenant_id == tenant_id,
                VinculoFornecedorProdutoModel.criado_em >= data_limite
            )
        ).order_by(
            VinculoFornecedorProdutoModel.criado_em.desc()
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [model.to_domain() for model in models]
