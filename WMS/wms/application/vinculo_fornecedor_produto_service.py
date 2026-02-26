"""
Service Layer: VinculoFornecedorProdutoService
Lógica de negócio e orquestração de operações CRUD
"""

from typing import List, Optional, Tuple
from uuid import UUID, uuid4
from datetime import datetime

from wms.domain.vinculo_fornecedor_produto import (
    VinculoFornecedorProduto,
    StatusVinculo,
    TipoUnidade
)
from wms.infrastructure.repositories.vinculo_fornecedor_produto_repository import (
    VinculoFornecedorProdutoRepository
)


class VinculoFornecedorProdutoService:
    """
    Service para operações de negócio com VinculoFornecedorProduto
    
    Orquestra as operações CRUD aplicando regras de negócio
    """
    
    def __init__(self, repository: VinculoFornecedorProdutoRepository):
        self.repository = repository
    
    async def criar_vinculo(
        self,
        tenant_id: UUID,
        fornecedor_id: UUID | str,
        codigo_fornecedor: str,
        produto_id_interno: UUID,
        fator_conversao: float = 1.0,
        unidade_origem: Optional[TipoUnidade] = None,
        unidade_destino: Optional[TipoUnidade] = None,
        criado_por: Optional[UUID] = None
    ) -> VinculoFornecedorProduto:
        """
        Cria novo vínculo fornecedor-produto
        
        Args:
            tenant_id: ID do tenant
            fornecedor_id: ID do fornecedor
            codigo_fornecedor: Código no sistema do fornecedor
            produto_id_interno: ID do produto interno
            fator_conversao: Fator de conversão de unidades
            unidade_origem: Unidade do fornecedor
            unidade_destino: Unidade interna
            criado_por: ID do usuário que criou
            
        Returns:
            Vínculo criado
            
        Raises:
            ValueError: Se dados inválidos
            IntegrityError: Se violar unicidade
        """
        # Validar se já existe
        existente = await self.repository.get_by_codigo_fornecedor(
            tenant_id, fornecedor_id, codigo_fornecedor
        )
        if existente:
            raise ValueError(
                f"Vínculo já existe para fornecedor {fornecedor_id} "
                f"com código '{codigo_fornecedor}'"
            )
        
        # Criar entidade
        vinculo = VinculoFornecedorProduto(
            id=uuid4(),
            tenant_id=tenant_id,
            fornecedor_id=str(fornecedor_id),
            codigo_fornecedor=codigo_fornecedor,
            produto_id_interno=produto_id_interno,
            fator_conversao=fator_conversao,
            unidade_origem=unidade_origem,
            unidade_destino=unidade_destino,
            criado_por=criado_por
        )
        
        return await self.repository.create(vinculo)
    
    async def buscar_vinculo_ativo(
        self,
        tenant_id: UUID,
        fornecedor_id: UUID | str,
        codigo_fornecedor: str
    ) -> Optional[VinculoFornecedorProduto]:
        """
        Busca vínculo ativo para importação
        
        Args:
            tenant_id: ID do tenant
            fornecedor_id: ID do fornecedor
            codigo_fornecedor: Código do produto
            
        Returns:
            Vínculo encontrado ou None
        """
        return await self.repository.get_by_codigo_fornecedor(
            tenant_id, fornecedor_id, codigo_fornecedor
        )
    
    async def listar_vinculos_tenant(
        self,
        tenant_id: UUID,
        status: Optional[StatusVinculo] = None,
        pagina: int = 1,
        tamanho_pagina: int = 20
    ) -> Tuple[List[VinculoFornecedorProduto], int]:
        """
        Lista vínculos do tenant com paginação
        
        Args:
            tenant_id: ID do tenant
            status: Filtro por status
            pagina: Número da página (1-based)
            tamanho_pagina: Tamanho da página
            
        Returns:
            Tupla (vínculos, total_registros)
        """
        offset = (pagina - 1) * tamanho_pagina
        
        return await self.repository.list_by_tenant(
            tenant_id=tenant_id,
            status=status,
            limit=tamanho_pagina,
            offset=offset
        )
    
    async def registrar_utilizacao_importacao(
        self,
        tenant_id: UUID,
        vinculo_id: UUID,
        data_importacao: Optional[datetime] = None
    ) -> bool:
        """
        Registra utilização do vínculo em importação
        
        Args:
            tenant_id: ID do tenant
            vinculo_id: ID do vínculo
            data_importacao: Data da importação
            
        Returns:
            True se registrado com sucesso
        """
        return await self.repository.registrar_utilizacao(
            tenant_id=tenant_id,
            vinculo_id=vinculo_id,
            data_utilizacao=data_importacao
        )
    
    async def atualizar_fator_conversao(
        self,
        tenant_id: UUID,
        vinculo_id: UUID,
        novo_fator: float
    ) -> VinculoFornecedorProduto:
        """
        Atualiza fator de conversão do vínculo
        
        Args:
            tenant_id: ID do tenant
            vinculo_id: ID do vínculo
            novo_fator: Novo fator de conversão
            
        Returns:
            Vínculo atualizado
        """
        vinculo = await self.repository.get_by_id(tenant_id, vinculo_id)
        if not vinculo:
            raise ValueError(f"Vínculo {vinculo_id} não encontrado")
        
        vinculo.atualizar_fator_conversao(novo_fator)
        
        return await self.repository.update(vinculo)
    
    async def desativar_vinculo(
        self,
        tenant_id: UUID,
        vinculo_id: UUID
    ) -> bool:
        """
        Desativa vínculo (soft delete)
        
        Args:
            tenant_id: ID do tenant
            vinculo_id: ID do vínculo
            
        Returns:
            True se desativado com sucesso
        """
        return await self.repository.delete(tenant_id, vinculo_id)
