"""
Testes de Idempotência do Endpoint /confirmar
Valida que NF-e só é processada uma vez, mesmo com reenvios
"""

import pytest
import asyncio
import os
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from wms.application.xml_confirmacao_service import XMLConfirmacaoService
from wms.interfaces.schemas.xml_confirmacao import (
    XMLConfirmacaoRequest, StatusConfirmacao
)
from wms.interfaces.api_xml_confirmacao import router
from wms.infrastructure.database import get_async_session
from tests._sync_asgi_client import SyncASGITestClient


def _nova_chave_acesso() -> str:
    """Gera uma chave numérica com 44 dígitos."""
    return f"{uuid4().int:044d}"


@pytest.fixture(scope="module")
def client():
    """Client FastAPI compartilhado para evitar troca de event loop no pool async."""
    from fastapi import FastAPI

    test_database_url = os.getenv(
        "TEST_DATABASE_URL",
        os.getenv(
            "ASYNC_DATABASE_URL",
            os.getenv(
                "DATABASE_URL",
                "postgresql+asyncpg://wms:wms@localhost:5432/wms",
            ),
        ),
    )

    app = FastAPI()
    app.include_router(router)

    async def _build_session_factory():
        engine = create_async_engine(
            test_database_url,
            echo=False,
            pool_pre_ping=True,
            connect_args={"timeout": 5},
        )
        session_local = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        app.state.test_engine = engine
        app.state.test_session_local = session_local

    async def override_get_async_session():
        if not hasattr(app.state, "test_session_local"):
            await _build_session_factory()
        async with app.state.test_session_local() as session:
            yield session

    app.dependency_overrides[get_async_session] = override_get_async_session

    test_client = SyncASGITestClient(app)
    try:
        yield test_client
    finally:
        if hasattr(app.state, "test_engine"):
            test_client._run_coro(app.state.test_engine.dispose())
        app.dependency_overrides.clear()
        test_client.close()


class TestXMLConfirmacaoIdempotencia:
    """Testes de idempotência do endpoint /confirmar"""

    @pytest.fixture
    def chave_acesso(self) -> str:
        return _nova_chave_acesso()

    @pytest.fixture
    def tenant_id(self) -> str:
        return str(uuid4())

    @pytest.fixture
    def fornecedor_id(self) -> str:
        return str(uuid4())

    @pytest.fixture
    def processamento_id(self) -> str:
        return str(uuid4())

    @pytest.fixture
    def confirmacao_request(
        self,
        chave_acesso: str,
        tenant_id: str,
        fornecedor_id: str,
        processamento_id: str,
    ):
        """Request padrão para testes"""
        return XMLConfirmacaoRequest(
            chave_acesso=chave_acesso,
            tenant_id=tenant_id,
            fornecedor_id=fornecedor_id,
            processamento_id=processamento_id,
            observacoes="Teste de idempotência"
        )
    
    @pytest.mark.asyncio
    async def test_primeira_confirmacao_sucesso(
        self, confirmacao_request: XMLConfirmacaoRequest, db_session: AsyncSession
    ):
        """
        CENÁRIO 1: Primeira confirmação deve ser bem-sucedida
        """
        # Preparar: Limpar histórico
        from wms.infrastructure.repositories.historico_importacoes_repository import HistoricoImportacoesRepository
        repo = HistoricoImportacoesRepository(db_session)
        
        # Verificar que não existe registro prévio
        registro = await repo.verificar_idempotencia(
            tenant_id=confirmacao_request.tenant_id,
            chave_acesso=confirmacao_request.chave_acesso
        )
        assert registro is None, "Não deve existir registro prévio"
        
        # Executar confirmação
        service = XMLConfirmacaoService(db_session)
        resultado = await service.confirmar_xml(confirmacao_request)
        
        # Validar sucesso
        assert resultado.status == StatusConfirmacao.CONCLUIDO
        assert resultado.chave_acesso == confirmacao_request.chave_acesso
        assert resultado.tenant_id == confirmacao_request.tenant_id
        assert resultado.fornecedor_id == confirmacao_request.fornecedor_id
        assert resultado.processamento_id == confirmacao_request.processamento_id
        assert resultado.total_items > 0
        assert resultado.itens_confirmados > 0
        assert resultado.itens_com_erro == 0
        assert resultado.confirmacao_id is not None
        assert resultado.tempo_processamento_ms is not None
        assert resultado.mensagem == "Processamento concluído com sucesso"
        
        # Verificar que foi criado no histórico
        registro_criado = await repo.verificar_idempotencia(
            tenant_id=confirmacao_request.tenant_id,
            chave_acesso=confirmacao_request.chave_acesso
        )
        assert registro_criado is not None
        assert registro_criado.status == StatusConfirmacao.CONCLUIDO.value
        assert registro_criado.confirmacao_id == resultado.confirmacao_id
    
    @pytest.mark.asyncio
    async def test_segunda_confirmacao_mesma_chave_erro_409(
        self, confirmacao_request: XMLConfirmacaoRequest, db_session: AsyncSession
    ):
        """
        CENÁRIO 2: Segunda confirmação com mesma chave deve retornar erro 409
        """
        from wms.infrastructure.repositories.historico_importacoes_repository import HistoricoImportacoesRepository
        repo = HistoricoImportacoesRepository(db_session)
        
        # 1. Primeira confirmação (sucesso)
        service = XMLConfirmacaoService(db_session)
        resultado1 = await service.confirmar_xml(confirmacao_request)
        assert resultado1.status == StatusConfirmacao.CONCLUIDO
        
        # 2. Segunda confirmação com mesma chave
        resultado2 = await service.confirmar_xml(confirmacao_request)
        
        # Validar erro de duplicidade
        assert resultado2.status == StatusConfirmacao.DUPLICADO
        assert resultado2.chave_acesso == confirmacao_request.chave_acesso
        assert resultado2.mensagem == "Esta nota fiscal já foi processada anteriormente"
        assert resultado2.total_items == 0
        assert resultado2.itens_confirmados == 0
        assert resultado2.itens_com_erro == 0
        assert resultado2.itens == []
        
        # Verificar que não criou novo registro
        registros = await repo.buscar_por_tenant(
            tenant_id=confirmacao_request.tenant_id,
            limite=10
        )
        registros_chave = [r for r in registros if r.chave_acesso == confirmacao_request.chave_acesso]
        assert len(registros_chave) == 1, "Deve existir apenas um registro para esta chave"
        assert registros_chave[0].status == StatusConfirmacao.CONCLUIDO.value
    
    def test_endpoint_primeira_confirmacao_sucesso(
        self, client: SyncASGITestClient, confirmacao_request: XMLConfirmacaoRequest
    ):
        """
        CENÁRIO 3: Endpoint POST /confirmar primeira vez - sucesso
        """
        response = client.post("/wms/v1/xml/confirmar", json=confirmacao_request.model_dump())
        
        # Validar response
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "CONCLUIDO"
        assert data["chave_acesso"] == confirmacao_request.chave_acesso
        assert data["tenant_id"] == confirmacao_request.tenant_id
        assert data["fornecedor_id"] == confirmacao_request.fornecedor_id
        assert data["processamento_id"] == confirmacao_request.processamento_id
        assert data["total_items"] > 0
        assert data["itens_confirmados"] > 0
        assert "confirmacao_id" in data
        assert "confirmado_em" in data
        assert "tempo_processamento_ms" in data
    
    def test_endpoint_segunda_confirmacao_erro_409(
        self, client: SyncASGITestClient, confirmacao_request: XMLConfirmacaoRequest
    ):
        """
        CENÁRIO 4: Endpoint POST /confirmar segunda vez - erro 409
        """
        # Primeira confirmação
        response1 = client.post("/wms/v1/xml/confirmar", json=confirmacao_request.model_dump())
        assert response1.status_code == 200
        
        # Segunda confirmação (deve falhar)
        response2 = client.post("/wms/v1/xml/confirmar", json=confirmacao_request.model_dump())
        
        # Validar erro 409
        assert response2.status_code == 409
        
        data = response2.json()
        assert data["erro"] == "NF_E_JA_PROCESSADA"
        assert "já foi processada" in data["mensagem"].lower()
        assert data["chave_acesso"] == confirmacao_request.chave_acesso
        assert "confirmacao_id" in data
        assert "timestamp" in data
    
    def test_endpoint_chave_acesso_invalida(
        self, client: SyncASGITestClient
    ):
        """
        CENÁRIO 5: Chave de acesso inválida - erro 422
        """
        request_invalido = {
            "chave_acesso": "123",  # Inválida: menos de 44 dígitos
            "tenant_id": str(uuid4()),
            "processamento_id": str(uuid4())
        }
        
        response = client.post("/wms/v1/xml/confirmar", json=request_invalido)
        
        assert response.status_code == 422
        
        data = response.json()
        assert "chave_acesso" in str(data).lower()
        assert "44" in str(data)  # Deve mencionar 44 dígitos
    
    def test_endpoint_tenant_id_obrigatorio(
        self, client: SyncASGITestClient, chave_acesso: str
    ):
        """
        CENÁRIO 6: tenant_id obrigatório - erro 422
        """
        request_sem_tenant = {
            "chave_acesso": chave_acesso,
            "processamento_id": str(uuid4())
            # tenant_id faltando
        }
        
        response = client.post("/wms/v1/xml/confirmar", json=request_sem_tenant)
        
        assert response.status_code == 422
        
        data = response.json()
        assert "tenant_id" in str(data).lower()
    
    def test_endpoint_processamento_id_obrigatorio(
        self, client: SyncASGITestClient, chave_acesso: str, tenant_id: str
    ):
        """
        CENÁRIO 7: processamento_id obrigatório - erro 422
        """
        request_sem_processamento = {
            "chave_acesso": chave_acesso,
            "tenant_id": tenant_id
            # processamento_id faltando
        }
        
        response = client.post("/wms/v1/xml/confirmar", json=request_sem_processamento)
        
        assert response.status_code == 422
        
        data = response.json()
        assert "processamento_id" in str(data).lower()
    
    @pytest.mark.asyncio
    async def test_concorrencia_confirmacoes_simultaneas(
        self, confirmacao_request: XMLConfirmacaoRequest, db_session: AsyncSession
    ):
        """
        CENÁRIO 8: Confirmações simultâneas da mesma NF-e
        Apenas uma deve ser bem-sucedida
        """
        from wms.infrastructure.repositories.historico_importacoes_repository import HistoricoImportacoesRepository

        SessionLocal = async_sessionmaker(
            bind=db_session.bind,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async def executar_confirmacao(idx: int):
            request = XMLConfirmacaoRequest(
                chave_acesso=confirmacao_request.chave_acesso,
                tenant_id=confirmacao_request.tenant_id,
                fornecedor_id=confirmacao_request.fornecedor_id,
                processamento_id=f"{confirmacao_request.processamento_id}_{idx}",
                observacoes=f"Teste concorrente {idx}"
            )
            async with SessionLocal() as session:
                return await XMLConfirmacaoService(session).confirmar_xml(request)

        # Criar múltiplas tasks simultâneas
        tasks = [asyncio.create_task(executar_confirmacao(i)) for i in range(5)]
        
        # Executar todas simultaneamente
        resultados = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analisar resultados
        sucessos = 0
        duplicados = 0
        erros = 0
        
        for resultado in resultados:
            if isinstance(resultado, Exception):
                erros += 1
            elif hasattr(resultado, 'status'):
                if resultado.status == StatusConfirmacao.CONCLUIDO:
                    sucessos += 1
                elif resultado.status == StatusConfirmacao.DUPLICADO:
                    duplicados += 1
        
        # Validar: apenas um sucesso, os demais duplicados
        assert sucessos == 1, f"Esperado 1 sucesso, obtido {sucessos}"
        assert duplicados == 4, f"Esperado 4 duplicados, obtido {duplicados}"
        assert erros == 0, f"Esperado 0 erros, obtido {erros}"
        
        # Verificar consistência no banco
        repo = HistoricoImportacoesRepository(db_session)
        registro = await repo.verificar_idempotencia(
            tenant_id=confirmacao_request.tenant_id,
            chave_acesso=confirmacao_request.chave_acesso
        )
        
        assert registro is not None
        assert registro.status == StatusConfirmacao.CONCLUIDO.value
    
    def test_endpoint_verificar_status_nao_processado(
        self, client: SyncASGITestClient, tenant_id: str, chave_acesso: str
    ):
        """
        CENÁRIO 9: Verificar status de NF-e não processada
        """
        response = client.get(f"/wms/v1/xml/verificar/{tenant_id}/{chave_acesso}")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["tenant_id"] == tenant_id
        assert data["chave_acesso"] == chave_acesso
        assert data["processado"] is False
        assert data["status"] is None
        assert "ainda não foi processada" in data["mensagem"]
    
    def test_endpoint_verificar_status_ja_processado(
        self, client: SyncASGITestClient, confirmacao_request: XMLConfirmacaoRequest
    ):
        """
        CENÁRIO 10: Verificar status de NF-e já processada
        """
        # Primeiro processa a NF-e
        response_confirm = client.post("/wms/v1/xml/confirmar", json=confirmacao_request.model_dump())
        assert response_confirm.status_code == 200
        
        confirmacao_id = response_confirm.json()["confirmacao_id"]
        
        # Depois verifica o status
        response_verificar = client.get(
            f"/wms/v1/xml/verificar/{confirmacao_request.tenant_id}/{confirmacao_request.chave_acesso}"
        )
        
        assert response_verificar.status_code == 200
        
        data = response_verificar.json()
        assert data["tenant_id"] == confirmacao_request.tenant_id
        assert data["chave_acesso"] == confirmacao_request.chave_acesso
        assert data["processado"] is True
        assert data["status"] == "CONCLUIDO"
        assert data["processamento_id"] == confirmacao_request.processamento_id
        assert data["confirmacao_id"] == confirmacao_id
        assert "data_processamento" in data
    
    def test_endpoint_verificar_chave_invalida(
        self, client: SyncASGITestClient, tenant_id: str
    ):
        """
        CENÁRIO 11: Verificar status com chave inválida
        """
        response = client.get(f"/wms/v1/xml/verificar/{tenant_id}/123")
        
        assert response.status_code == 400
        
        data = response.json()
        assert data["erro"] == "INVALID_CHAVE_ACESSO"
        assert "44 dígitos" in data["mensagem"]
    
    def test_endpoint_historico_importacoes(
        self, client: SyncASGITestClient, confirmacao_request: XMLConfirmacaoRequest
    ):
        """
        CENÁRIO 12: Consultar histórico de importações
        """
        # Processar algumas NF-e
        for i in range(3):
            request = XMLConfirmacaoRequest(
                chave_acesso=_nova_chave_acesso(),
                tenant_id=confirmacao_request.tenant_id,
                fornecedor_id=confirmacao_request.fornecedor_id,
                processamento_id=f"{confirmacao_request.processamento_id}_{i}"
            )
            client.post("/wms/v1/xml/confirmar", json=request.model_dump())
        
        # Consultar histórico
        response = client.get(f"/wms/v1/xml/historico/{confirmacao_request.tenant_id}")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["tenant_id"] == confirmacao_request.tenant_id
        assert "historico" in data
        assert "estatisticas" in data
        assert "paginacao" in data
        
        historico = data["historico"]
        assert len(historico) >= 3
        
        # Validar estrutura dos itens
        for item in historico[:3]:
            assert "chave_acesso" in item
            assert "status" in item
            assert "criado_em" in item
            assert "tenant_id" in item
    
    def test_endpoint_estatisticas_importacoes(
        self, client: SyncASGITestClient, confirmacao_request: XMLConfirmacaoRequest
    ):
        """
        CENÁRIO 13: Consultar estatísticas de importações
        """
        # Processar uma NF-e
        client.post("/wms/v1/xml/confirmar", json=confirmacao_request.model_dump())
        
        # Consultar estatísticas
        response = client.get(f"/wms/v1/xml/estatisticas/{confirmacao_request.tenant_id}")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["tenant_id"] == confirmacao_request.tenant_id
        assert "periodo_analisado" in data
        assert "estatisticas" in data
        
        estatisticas = data["estatisticas"]
        assert "total_importacoes" in estatisticas
        assert "importacoes_concluidas" in estatisticas
        assert "taxa_sucesso" in estatisticas
        assert "valor_total_importado" in estatisticas
        assert "periodo_dias" in estatisticas
    
    @pytest.mark.asyncio
    async def test_rollback_em_erro_atualizacao_estoque(
        self, db_session: AsyncSession, monkeypatch: pytest.MonkeyPatch
    ):
        """
        CENÁRIO 14: Rollback em caso de erro na atualização de estoque
        """
        from wms.infrastructure.repositories.historico_importacoes_repository import HistoricoImportacoesRepository
        
        async def _falhar_obter_dados_analise(self, processamento_id):
            raise Exception("falha simulada no processo de analise")

        monkeypatch.setattr(
            XMLConfirmacaoService,
            "_obter_dados_analise",
            _falhar_obter_dados_analise,
        )

        # Simular erro no processamento com request válido
        request_com_erro = XMLConfirmacaoRequest(
            chave_acesso=_nova_chave_acesso(),
            tenant_id=str(uuid4()),
            fornecedor_id=str(uuid4()),
            processamento_id=str(uuid4())
        )
        
        # Tentar processar (deve falhar e fazer rollback)
        with pytest.raises(Exception):
            await XMLConfirmacaoService(db_session).confirmar_xml(request_com_erro)
        
        # Verificar que não criou registro no histórico
        repo = HistoricoImportacoesRepository(db_session)
        registro = await repo.verificar_idempotencia(
            tenant_id=request_com_erro.tenant_id,
            chave_acesso=request_com_erro.chave_acesso
        )
        assert registro is None, "Não deve criar registro em caso de erro"
    
    def test_performance_confirmacao(
        self, client: SyncASGITestClient, confirmacao_request: XMLConfirmacaoRequest
    ):
        """
        CENÁRIO 15: Performance da confirmação
        Confirmação deve ser rápida (< 3 segundos)
        """
        import time
        
        start_time = time.time()
        response = client.post("/wms/v1/xml/confirmar", json=confirmacao_request.model_dump())
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Validar performance
        assert response.status_code == 200
        assert processing_time < 3.0, f"Confirmação demorou: {processing_time:.2f}s"
        
        data = response.json()
        assert data["tempo_processamento_ms"] is not None
        assert data["tempo_processamento_ms"] < 3000  # < 3 segundos
