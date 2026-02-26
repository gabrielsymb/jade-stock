"""
Testes de Integração - VinculoFornecedorProduto com Dados Reais
Cenários baseados em operações reais de negócio
"""

import pytest
from decimal import Decimal
from uuid import uuid4
from datetime import datetime, timedelta
from types import SimpleNamespace

from wms.domain.vinculo_fornecedor_produto import (
    VinculoFornecedorProduto,
    StatusVinculo,
    TipoUnidade
)
from wms.infrastructure.repositories.vinculo_fornecedor_produto_repository import (
    VinculoFornecedorProdutoRepository
)
from wms.application.vinculo_fornecedor_produto_service import (
    VinculoFornecedorProdutoService
)


class TestVinculoFornecedorProdutoRealData:
    """Testes de integração com dados reais de negócio"""
    
    @pytest.fixture
    def tenant_test_id(self):
        """ID de tenant para testes"""
        return uuid4()
    
    @pytest.fixture
    def fornecedor_solar_id(self):
        """ID do fornecedor Solar para testes"""
        return str(uuid4())
    
    @pytest.fixture
    def produto_cocacola_id(self):
        """ID do produto Coca-Cola para testes"""
        return uuid4()

    @pytest.fixture
    def fornecedor_solar(self):
        return SimpleNamespace(id=str(uuid4()))

    @pytest.fixture
    def fornecedor_ambev(self):
        return SimpleNamespace(id=str(uuid4()))

    @pytest.fixture
    def produtos_internos(self):
        return [
            SimpleNamespace(id=uuid4()),
            SimpleNamespace(id=uuid4()),
            SimpleNamespace(id=uuid4()),
        ]
    
    @pytest.fixture
    def repository(self, db_session):
        """Repository instance"""
        return VinculoFornecedorProdutoRepository(db_session)
    
    @pytest.fixture
    def service(self, repository):
        """Service instance"""
        return VinculoFornecedorProdutoService(repository)
    
    @pytest.mark.asyncio
    async def test_cenario_1_criar_vinculo_coca_cola_caixas(
        self, service, tenant_test_id, fornecedor_solar_id, produto_cocacola_id
    ):
        """
        CENÁRIO 1: Criar vínculo para Coca-Cola em caixas
        
        Dado: Fornecedor Solar envia "Coca-Cola 12x350ml"
        E: Sistema controla unidades individuais (UN)
        E: 1 caixa = 12 unidades
        Então: Sistema deve criar vínculo com fator de conversão 12.0
        """
        
        # Criar vínculo
        vinculo = await service.criar_vinculo(
            tenant_id=tenant_test_id,
            fornecedor_id=fornecedor_solar_id,
            codigo_fornecedor="COCA-COLA-12X350ML",
            produto_id_interno=produto_cocacola_id,
            fator_conversao=12.0,
            unidade_origem=TipoUnidade.CAIXA,
            unidade_destino=TipoUnidade.UNIDADE
        )
        
        # Validar criação
        assert vinculo.id is not None
        assert vinculo.tenant_id == tenant_test_id
        assert vinculo.fornecedor_id == fornecedor_solar_id
        assert vinculo.codigo_fornecedor == "COCA-COLA-12X350ML"
        assert vinculo.produto_id_interno == produto_cocacola_id
        assert vinculo.fator_conversao == Decimal("12.0")
        assert vinculo.unidade_origem == TipoUnidade.CAIXA
        assert vinculo.unidade_destino == TipoUnidade.UNIDADE
        assert vinculo.status == StatusVinculo.ATIVO
        assert vinculo.vezes_utilizado == 0
        
        # Testar conversão
        quantidade_convertida = vinculo.calcular_quantidade_convertida(Decimal("2.5"))
        assert quantidade_convertida == Decimal("30.0")  # 2.5 caixas = 30 unidades
    
    @pytest.mark.asyncio
    async def test_cenario_2_buscar_vinculo_ativo_importacao(
        self, service, repository, tenant_test_id, fornecedor_solar, produtos_internos
    ):
        """
        CENÁRIO 2: Buscar vínculo ativo durante importação
        
        Dado: Vínculo existente para "COCA-COLA-2L-PET"
        E: Sistema recebe XML com mesmo código
        Então: Deve encontrar vínculo automaticamente
        """
        
        # Criar vínculo inicial
        vinculo_criado = await service.criar_vinculo(
            tenant_id=tenant_test_id,
            fornecedor_id=fornecedor_solar.id,
            codigo_fornecedor="COCA-COLA-2L-PET",
            produto_id_interno=produtos_internos[0].id,
            fator_conversao=1.0,
            unidade_origem=TipoUnidade.UNIDADE,
            unidade_destino=TipoUnidade.UNIDADE
        )
        
        # Simular busca durante importação
        vinculo_encontrado = await service.buscar_vinculo_ativo(
            tenant_id=tenant_test_id,
            fornecedor_id=fornecedor_solar.id,
            codigo_fornecedor="COCA-COLA-2L-PET"
        )
        
        # Validar encontro
        assert vinculo_encontrado is not None
        assert vinculo_encontrado.id == vinculo_criado.id
        assert vinculo_encontrado.codigo_fornecedor == "COCA-COLA-2L-PET"
        assert vinculo_encontrado.status == StatusVinculo.ATIVO
    
    @pytest.mark.asyncio
    async def test_cenario_3_registrar_utilizacao_importacao_real(
        self, service, repository, tenant_test_id, fornecedor_ambev, produtos_internos
    ):
        """
        CENÁRIO 3: Registrar utilização em importação real
        
        Dado: Vínculo criado para Ambev
        E: Sistema processa NF-e com 5 caixas
        Então: Deve registrar utilização e atualizar estatísticas
        """
        
        # Criar vínculo
        vinculo = await service.criar_vinculo(
            tenant_id=tenant_test_id,
            fornecedor_id=fornecedor_ambev.id,
            codigo_fornecedor="GUARANA-ANTARTICA-CX12",
            produto_id_interno=produtos_internos[2].id,  # Guaraná
            fator_conversao=12.0,
            unidade_origem=TipoUnidade.CAIXA,
            unidade_destino=TipoUnidade.UNIDADE
        )
        
        # Simular utilização em importação
        data_importacao = datetime.utcnow()
        sucesso = await service.registrar_utilizacao_importacao(
            tenant_id=tenant_test_id,
            vinculo_id=vinculo.id,
            data_importacao=data_importacao
        )
        
        assert sucesso is True
        
        # Verificar atualização
        vinculo_atualizado = await repository.get_by_id(tenant_test_id, vinculo.id)
        assert vinculo_atualizado.vezes_utilizado == 1
        assert vinculo_atualizado.ultima_importacao == data_importacao
        
        # Simular segunda utilização
        await service.registrar_utilizacao_importacao(
            tenant_id=tenant_test_id,
            vinculo_id=vinculo.id
        )
        
        vinculo_final = await repository.get_by_id(tenant_test_id, vinculo.id)
        assert vinculo_final.vezes_utilizado == 2
    
    @pytest.mark.asyncio
    async def test_cenario_4_multiplas_fornecedores_mesmo_produto(
        self, service, repository, tenant_test_id, fornecedor_solar, fornecedor_ambev, produtos_internos
    ):
        """
        CENÁRIO 4: Múltiplos fornecedores para mesmo produto
        
        Dado: Coca-Cola pode vir da Solar ou da Ambev
        E: Cada fornecedor tem seu próprio código
        Então: Sistema deve suportar N vínculos para 1 produto
        """
        
        # Vínculo Solar
        vinculo_solar = await service.criar_vinculo(
            tenant_id=tenant_test_id,
            fornecedor_id=fornecedor_solar.id,
            codigo_fornecedor="COCA-2L-SOLAR",
            produto_id_interno=produtos_internos[0].id,  # Coca-Cola 2L
            fator_conversao=1.0
        )
        
        # Vínculo Ambev
        vinculo_ambev = await service.criar_vinculo(
            tenant_id=tenant_test_id,
            fornecedor_id=fornecedor_ambev.id,
            codigo_fornecedor="COCA-2L-AMBEV",
            produto_id_interno=produtos_internos[0].id,  # Mesmo produto
            fator_conversao=1.0
        )
        
        # Validar que são vínculos diferentes
        assert vinculo_solar.id != vinculo_ambev.id
        assert vinculo_solar.fornecedor_id != vinculo_ambev.fornecedor_id
        assert vinculo_solar.produto_id_interno == vinculo_ambev.produto_id_interno
        
        # Buscar por produto deve retornar ambos
        vinculos_produto = await repository.list_by_produto(
            tenant_id=tenant_test_id,
            produto_id_interno=produtos_internos[0].id
        )
        
        assert len(vinculos_produto) == 2
        fornecedores_ids = {v.fornecedor_id for v in vinculos_produto}
        assert fornecedores_ids == {fornecedor_solar.id, fornecedor_ambev.id}
    
    @pytest.mark.asyncio
    async def test_cenario_5_atualizacao_fator_conversao_correcao(
        self, service, repository, tenant_test_id, fornecedor_solar, produtos_internos
    ):
        """
        CENÁRIO 5: Correção de fator de conversão
        
        Dado: Vínculo criado com fator errado (6.0 ao invés de 12.0)
        E: Operador identifica erro após primeira importação
        Então: Sistema deve permitir correção e manter histórico
        """
        
        # Criar vínculo com fator incorreto
        vinculo = await service.criar_vinculo(
            tenant_id=tenant_test_id,
            fornecedor_id=fornecedor_solar.id,
            codigo_fornecedor="COCA-LATA-CX6",
            produto_id_interno=produtos_internos[1].id,  # Coca-Cola Lata
            fator_conversao=6.0,  # Errado: na verdade são 12
            unidade_origem=TipoUnidade.CAIXA,
            unidade_destino=TipoUnidade.UNIDADE
        )
        
        # Registrar utilização inicial
        await service.registrar_utilizacao_importacao(
            tenant_id=tenant_test_id,
            vinculo_id=vinculo.id
        )
        
        # Corrigir fator
        vinculo_corrigido = await service.atualizar_fator_conversao(
            tenant_id=tenant_test_id,
            vinculo_id=vinculo.id,
            novo_fator=12.0
        )
        
        # Validar correção
        assert vinculo_corrigido.fator_conversao == Decimal("12.0")
        assert vinculo_corrigido.atualizado_em > vinculo.atualizado_em
        
        # Testar conversão corrigida
        quantidade_convertida = vinculo_corrigido.calcular_quantidade_convertida(Decimal("1.0"))
        assert quantidade_convertida == Decimal("12.0")  # 1 caixa = 12 unidades
    
    @pytest.mark.asyncio
    async def test_cenario_6_desativacao_vinculo_obsoleto(
        self, service, repository, tenant_test_id, fornecedor_solar, produtos_internos
    ):
        """
        CENÁRIO 6: Desativação de vínculo obsoleto
        
        Dado: Fornecedor mudou código do produto
        E: Vínculo antigo não será mais utilizado
        Então: Sistema deve desativar sem perder histórico
        """
        
        # Criar vínculo antigo
        vinculo = await service.criar_vinculo(
            tenant_id=tenant_test_id,
            fornecedor_id=fornecedor_solar.id,
            codigo_fornecedor="COCA-CODIGO-ANTIGO",
            produto_id_interno=produtos_internos[0].id,
            fator_conversao=1.0
        )
        
        # Registrar algumas utilizações
        for _ in range(3):
            await service.registrar_utilizacao_importacao(
                tenant_id=tenant_test_id,
                vinculo_id=vinculo.id
            )
        
        # Desativar
        sucesso = await service.desativar_vinculo(
            tenant_id=tenant_test_id,
            vinculo_id=vinculo.id
        )
        
        assert sucesso is True
        
        # Verificar desativação
        vinculo_desativado = await repository.get_by_id(tenant_test_id, vinculo.id)
        assert vinculo_desativado.status == StatusVinculo.INATIVO
        assert vinculo_desativado.vezes_utilizado == 3  # Histórico preservado
        
        # Busca ativa não deve encontrar
        vinculo_ativo = await service.buscar_vinculo_ativo(
            tenant_id=tenant_test_id,
            fornecedor_id=fornecedor_solar.id,
            codigo_fornecedor="COCA-CODIGO-ANTIGO"
        )
        assert vinculo_ativo is None
    
    @pytest.mark.asyncio
    async def test_cenario_7_estatisticas_fornecedor(
        self, repository, service, tenant_test_id, fornecedor_solar, produtos_internos
    ):
        """
        CENÁRIO 7: Estatísticas de vínculos por fornecedor
        
        Dado: Fornecedor com múltiplos vínculos e utilizações
        Então: Sistema deve calcular estatísticas corretamente
        """
        
        # Criar múltiplos vínculos
        vinculos = []
        codigos = ["COCA-2L", "GUARANA-2L", "FANTA-LARANJA-2L"]
        
        for i, codigo in enumerate(codigos):
            vinculo = await service.criar_vinculo(
                tenant_id=tenant_test_id,
                fornecedor_id=fornecedor_solar.id,
                codigo_fornecedor=codigo,
                produto_id_interno=produtos_internos[i % len(produtos_internos)].id,
                fator_conversao=1.0
            )
            vinculos.append(vinculo)
        
        # Registrar utilizações diferentes
        utilizacoes = [5, 12, 3]  # Coca: 5, Guaraná: 12, Fanta: 3
        
        for vinculo, num_utilizacoes in zip(vinculos, utilizacoes):
            for _ in range(num_utilizacoes):
                await service.registrar_utilizacao_importacao(
                    tenant_id=tenant_test_id,
                    vinculo_id=vinculo.id
                )
        
        # Obter estatísticas
        estatisticas = await repository.get_estatisticas_fornecedor(
            tenant_id=tenant_test_id,
            fornecedor_id=fornecedor_solar.id
        )
        
        # Validar estatísticas
        assert estatisticas['total_vinculos'] == 3
        assert estatisticas['vinculos_ativos'] == 3
        assert estatisticas['total_utilizacoes'] == 20  # 5 + 12 + 3
        assert estatisticas['max_utilizacoes'] == 12
        assert estatisticas['avg_peso_confianca'] == 1.0  # Default
    
    @pytest.mark.asyncio
    async def test_cenario_8_busca_parcial_autocomplete(
        self, repository, service, tenant_test_id, fornecedor_solar, produtos_internos
    ):
        """
        CENÁRIO 8: Busca parcial para autocomplete
        
        Dado: Operador digitando "COCA" na tela de conciliação
        Então: Sistema deve sugerir vínculos existentes
        """
        
        # Criar vínculos com códigos similares
        codigos = [
            "COCA-COLA-2L",
            "COCA-COLA-LATA",
            "COCA-COLA-ZERO",
            "GUARANA-ANTARTICA"
        ]
        
        for codigo in codigos:
            await service.criar_vinculo(
                tenant_id=tenant_test_id,
                fornecedor_id=fornecedor_solar.id,
                codigo_fornecedor=codigo,
                produto_id_interno=produtos_internos[0].id,
                fator_conversao=1.0
            )
        
        # Buscar por "COCA"
        resultados = await repository.search_by_codigo_parcial(
            tenant_id=tenant_test_id,
            codigo_parcial="COCA",
            limite=10
        )
        
        # Validar resultados
        assert len(resultados) == 3  # Apenas os 3 "COCA"
        codigos_encontrados = {r.codigo_fornecedor for r in resultados}
        esperados = {"COCA-COLA-2L", "COCA-COLA-LATA", "COCA-COLA-ZERO"}
        assert codigos_encontrados == esperados
    
    @pytest.mark.asyncio
    async def test_cenario_9_vinculos_recentes_aprendizado(
        self, repository, service, tenant_test_id, fornecedor_ambev, produtos_internos
    ):
        """
        CENÁRIO 9: Vínculos recentes para aprendizado
        
        Dado: Novos vínculos criados nos últimos dias
        Então: Sistema deve identificar vínculos recentes
        """
        
        # Criar vínculo hoje
        vinculo_hoje = await service.criar_vinculo(
            tenant_id=tenant_test_id,
            fornecedor_id=fornecedor_ambev.id,
            codigo_fornecedor="PRODUTO-RECENTE",
            produto_id_interno=produtos_internos[0].id,
            fator_conversao=1.0
        )
        
        # Buscar vínculos recentes (últimos 7 dias)
        vinculos_recentes = await repository.get_vinculos_recentes(
            tenant_id=tenant_test_id,
            dias=7
        )
        
        # Validar
        assert len(vinculos_recentes) >= 1
        ids_recentes = {v.id for v in vinculos_recentes}
        assert vinculo_hoje.id in ids_recentes
        
        # Validar propriedade de recenticidade
        vinculo_encontrado = next(v for v in vinculos_recentes if v.id == vinculo_hoje.id)
        assert vinculo_encontrado.eh_recente is True
