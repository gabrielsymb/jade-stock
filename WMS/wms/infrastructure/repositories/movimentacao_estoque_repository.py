"""
Repository Pattern Implementation for MovimentacaoEstoque Entity
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from wms.domain.movimentacao_estoque import MovimentacaoEstoque
from wms.infrastructure.models.movimentacao_estoque import MovimentacaoEstoqueModel


class MovimentacaoEstoqueRepository:
    """Repository for MovimentacaoEstoque entity operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, movimentacao: MovimentacaoEstoque) -> MovimentacaoEstoque:
        """Create a new movimentacao estoque record"""
        model = MovimentacaoEstoqueModel(
            tenant_id=movimentacao.tenant_id,
            sku_id=movimentacao.sku_id,
            endereco_origem=movimentacao.endereco_origem,
            endereco_destino=movimentacao.endereco_destino,
            quantidade=movimentacao.quantidade,
            tipo_movimentacao=movimentacao.tipo_movimentacao,
            motivo=movimentacao.motivo,
            documento_referencia=movimentacao.documento_referencia,
            usuario_id=movimentacao.usuario_id,
            data_movimentacao=movimentacao.data_movimentacao
        )
        
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        
        return self._model_to_domain(model)
    
    async def get_by_id(self, movimentacao_id: UUID) -> Optional[MovimentacaoEstoque]:
        """Get movimentacao estoque by ID"""
        stmt = select(MovimentacaoEstoqueModel).where(
            MovimentacaoEstoqueModel.id == movimentacao_id
        )
        
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            return self._model_to_domain(model)
        
        return None
    
    async def get_by_sku(self, sku_id: str) -> List[MovimentacaoEstoque]:
        """Get all movimentacoes for a SKU"""
        stmt = select(MovimentacaoEstoqueModel).where(
            MovimentacaoEstoqueModel.sku_id == sku_id
        ).order_by(MovimentacaoEstoqueModel.data_movimentacao.desc())
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_domain(model) for model in models]
    
    async def get_by_endereco(self, endereco_codigo: str) -> List[MovimentacaoEstoque]:
        """Get all movimentacoes for an endereço"""
        stmt = select(MovimentacaoEstoqueModel).where(
            (MovimentacaoEstoqueModel.endereco_origem == endereco_codigo) |
            (MovimentacaoEstoqueModel.endereco_destino == endereco_codigo)
        ).order_by(MovimentacaoEstoqueModel.data_movimentacao.desc())
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_domain(model) for model in models]
    
    async def get_by_documento(self, documento_referencia: str) -> List[MovimentacaoEstoque]:
        """Get all movimentacoes for a documento referencia"""
        stmt = select(MovimentacaoEstoqueModel).where(
            MovimentacaoEstoqueModel.documento_referencia == documento_referencia
        ).order_by(MovimentacaoEstoqueModel.data_movimentacao.desc())
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_domain(model) for model in models]
    
    async def list_by_periodo(
        self, 
        data_inicio: datetime, 
        data_fim: datetime
    ) -> List[MovimentacaoEstoque]:
        """List movimentacoes por período"""
        stmt = select(MovimentacaoEstoqueModel).where(
            MovimentacaoEstoqueModel.data_movimentacao >= data_inicio,
            MovimentacaoEstoqueModel.data_movimentacao <= data_fim
        ).order_by(MovimentacaoEstoqueModel.data_movimentacao.desc())
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_domain(model) for model in models]
    
    async def update(self, movimentacao: MovimentacaoEstoque) -> MovimentacaoEstoque:
        """Update an existing movimentacao estoque record"""
        stmt = update(MovimentacaoEstoqueModel).where(
            MovimentacaoEstoqueModel.id == movimentacao.id
        ).values(
            tenant_id=movimentacao.tenant_id,
            sku_id=movimentacao.sku_id,
            endereco_origem=movimentacao.endereco_origem,
            endereco_destino=movimentacao.endereco_destino,
            quantidade=movimentacao.quantidade,
            tipo_movimentacao=movimentacao.tipo_movimentacao,
            motivo=movimentacao.motivo,
            documento_referencia=movimentacao.documento_referencia,
            usuario_id=movimentacao.usuario_id,
            data_movimentacao=movimentacao.data_movimentacao
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return await self.get_by_id(movimentacao.id)
    
    async def delete(self, movimentacao_id: UUID) -> bool:
        """Delete a movimentacao estoque record"""
        stmt = delete(MovimentacaoEstoqueModel).where(
            MovimentacaoEstoqueModel.id == movimentacao_id
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
    
    def _model_to_domain(self, model: MovimentacaoEstoqueModel) -> MovimentacaoEstoque:
        """Convert ORM model to domain entity"""
        return MovimentacaoEstoque(
            id=model.id,
            tenant_id=model.tenant_id,
            sku_id=model.sku_id,
            endereco_origem=model.endereco_origem,
            endereco_destino=model.endereco_destino,
            quantidade=model.quantidade,
            tipo_movimentacao=model.tipo_movimentacao,
            motivo=model.motivo,
            documento_referencia=model.documento_referencia,
            usuario_id=model.usuario_id,
            data_movimentacao=model.data_movimentacao
        )
