"""
Repository Pattern Implementation for SaldoEstoque Entity
"""

from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete

from wms.domain.saldo_estoque import SaldoEstoque
from wms.infrastructure.models.saldo_estoque import SaldoEstoqueModel


class SaldoEstoqueRepository:
    """Repository for SaldoEstoque entity operations"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def create(self, saldo: SaldoEstoque) -> SaldoEstoque:
        """Create a new saldo estoque record"""
        model = SaldoEstoqueModel(
            sku_id=saldo.sku_id,
            endereco_codigo=saldo.endereco_codigo,
            saldo_disponivel=saldo.saldo_disponivel,
            saldo_avariado=saldo.saldo_avariado,
            saldo_bloqueado=saldo.saldo_bloqueado
        )
        
        self.session.add(model)
        await self.session.commit()
        await self.session.refresh(model)
        
        return self._model_to_domain(model)
    
    async def get_by_sku_and_endereco(
        self, 
        sku_id: str, 
        endereco_codigo: str
    ) -> Optional[SaldoEstoque]:
        """Get saldo estoque by SKU and endereço"""
        stmt = select(SaldoEstoqueModel).where(
            SaldoEstoqueModel.sku_id == sku_id,
            SaldoEstoqueModel.endereco_codigo == endereco_codigo
        )
        
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            return self._model_to_domain(model)
        
        return None
    
    async def get_by_sku(self, sku_id: str) -> List[SaldoEstoque]:
        """Get all saldo estoque records for a SKU"""
        stmt = select(SaldoEstoqueModel).where(
            SaldoEstoqueModel.sku_id == sku_id
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_domain(model) for model in models]
    
    async def get_by_endereco(self, endereco_codigo: str) -> List[SaldoEstoque]:
        """Get all saldo estoque records for an endereço"""
        stmt = select(SaldoEstoqueModel).where(
            SaldoEstoqueModel.endereco_codigo == endereco_codigo
        )
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_domain(model) for model in models]
    
    async def update(self, saldo: SaldoEstoque) -> SaldoEstoque:
        """Update an existing saldo estoque record"""
        stmt = update(SaldoEstoqueModel).where(
            SaldoEstoqueModel.sku_id == saldo.sku_id,
            SaldoEstoqueModel.endereco_codigo == saldo.endereco_codigo
        ).values(
            saldo_disponivel=saldo.saldo_disponivel,
            saldo_avariado=saldo.saldo_avariado,
            saldo_bloqueado=saldo.saldo_bloqueado
        )
        
        await self.session.execute(stmt)
        await self.session.commit()
        
        return await self.get_by_sku_and_endereco(saldo.sku_id, saldo.endereco_codigo)
    
    async def delete(self, sku_id: str, endereco_codigo: str) -> bool:
        """Delete a saldo estoque record"""
        stmt = delete(SaldoEstoqueModel).where(
            SaldoEstoqueModel.sku_id == sku_id,
            SaldoEstoqueModel.endereco_codigo == endereco_codigo
        )
        
        result = await self.session.execute(stmt)
        await self.session.commit()
        
        return result.rowcount > 0
    
    async def list_all(self) -> List[SaldoEstoque]:
        """List all saldo estoque records"""
        stmt = select(SaldoEstoqueModel)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        return [self._model_to_domain(model) for model in models]
    
    def _model_to_domain(self, model: SaldoEstoqueModel) -> SaldoEstoque:
        """Convert ORM model to domain entity"""
        return SaldoEstoque(
            sku_id=model.sku_id,
            endereco_codigo=model.endereco_codigo,
            saldo_disponivel=model.saldo_disponivel,
            saldo_avariado=model.saldo_avariado,
            saldo_bloqueado=model.saldo_bloqueado
        )
