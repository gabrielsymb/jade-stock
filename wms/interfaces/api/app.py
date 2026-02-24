"""API minima para expor os casos de uso do WMS."""

from __future__ import annotations

import os
from dataclasses import asdict
from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from wms.application.use_cases.registrar_ajuste_estoque import (
    RegistrarAjusteEstoque,
    RegistrarAjusteEstoqueInput,
)
from wms.application.use_cases.registrar_avaria_estoque import (
    RegistrarAvariaEstoque,
    RegistrarAvariaEstoqueInput,
)
from wms.application.use_cases.registrar_politica_kanban import (
    RegistrarPoliticaKanban,
    RegistrarPoliticaKanbanInput,
)
from wms.application.use_cases.registrar_movimentacao_estoque import (
    RegistrarMovimentacaoEstoque,
    RegistrarMovimentacaoEstoqueInput,
)
from wms.application.use_cases.registrar_inventario_ciclico import (
    ItemContagemCiclicaInput,
    RegistrarInventarioCiclico,
    RegistrarInventarioCiclicoInput,
)
from wms.application.use_cases.registrar_recebimento import (
    ItemRecebimentoInput,
    RegistrarRecebimento,
    RegistrarRecebimentoInput,
)
from wms.application.use_cases.processar_curva_abcd import (
    ItemCurvaABCDInput,
    ProcessarCurvaABCD,
    ProcessarCurvaABCDInput,
)
from wms.application.use_cases.processar_giro_estoque import (
    ItemGiroEstoqueInput,
    ProcessarGiroEstoque,
    ProcessarGiroEstoqueInput,
)
from wms.application.use_cases.processar_sazonalidade_operacional import (
    ItemSazonalidadeInput,
    ProcessarSazonalidadeOperacional,
    ProcessarSazonalidadeOperacionalInput,
)
from wms.application.use_cases.processar_governanca_orcamentaria import (
    AporteExternoInput,
    AprovacaoExcecaoInput,
    ProcessarGovernancaOrcamentaria,
    ProcessarGovernancaOrcamentariaInput,
)
from wms.domain.exceptions import DomainError, NotaFiscalDuplicada
from wms.infrastructure.database.database_config import get_connection_postgres
from wms.infrastructure.database.postgres_transaction_manager import postgres_transaction
from wms.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from wms.infrastructure.postgres.postgres_estoque_repository import PostgresEstoqueRepository
from wms.infrastructure.postgres.postgres_event_store import PostgresEventStore
from wms.infrastructure.postgres.postgres_inventario_repository import (
    PostgresInventarioRepository,
)
from wms.infrastructure.postgres.postgres_idempotency_repository import (
    IdempotencyPayloadConflict,
    PostgresIdempotencyRepository,
)
from wms.infrastructure.postgres.postgres_kanban_repository import (
    PostgresKanbanRepository,
)
from wms.infrastructure.postgres.postgres_movimentacao_repository import (
    PostgresMovimentacaoRepository,
)
from wms.infrastructure.postgres.postgres_recebimento_repository import (
    PostgresRecebimentoRepository,
)
from wms.infrastructure.postgres.postgres_politica_reposicao_repository import (
    PostgresPoliticaReposicaoRepository,
)
from wms.infrastructure.postgres.postgres_sinal_externo_repository import (
    PostgresSinalExternoRepository,
)
from wms.infrastructure.postgres.postgres_orcamento_repository import (
    PostgresOrcamentoRepository,
)
from wms.infrastructure.repositories.in_memory_estoque_repository import (
    InMemoryEstoqueRepository,
)
from wms.infrastructure.repositories.in_memory_inventario_repository import (
    InMemoryInventarioRepository,
)
from wms.infrastructure.repositories.in_memory_kanban_repository import (
    InMemoryKanbanRepository,
)
from wms.infrastructure.repositories.in_memory_movimentacao_repository import (
    InMemoryMovimentacaoRepository,
)
from wms.infrastructure.repositories.in_memory_recebimento_repository import (
    InMemoryRecebimentoRepository,
)
from wms.infrastructure.repositories.in_memory_politica_reposicao_repository import (
    InMemoryPoliticaReposicaoRepository,
)
from wms.infrastructure.repositories.in_memory_sinal_externo_repository import (
    InMemorySinalExternoRepository,
)
from wms.infrastructure.repositories.in_memory_orcamento_repository import (
    InMemoryOrcamentoRepository,
)

API_BACKEND = os.getenv("WMS_API_BACKEND", "inmemory").strip().lower()
TENANT_ID = os.getenv("WMS_API_TENANT_ID", "loja_demo")

app = FastAPI(title="WMS API", version="0.1.0")


class MovimentacaoRequest(BaseModel):
    sku_id: str
    tipo_movimentacao: Literal["entrada", "saida", "transferencia", "ajuste", "avaria"]
    quantidade: float = Field(gt=0)
    endereco_origem: str | None = None
    endereco_destino: str | None = None
    operador: str
    correlation_id: str
    motivo: str | None = None


class AjusteRequest(BaseModel):
    sku_id: str
    endereco_codigo: str
    quantidade_ajuste: float
    operador: str
    correlation_id: str
    motivo: str


class AvariaRequest(BaseModel):
    sku_id: str
    endereco_codigo: str
    quantidade_avaria: float = Field(gt=0)
    operador: str
    correlation_id: str
    motivo: str


class ItemRecebimentoRequest(BaseModel):
    sku_codigo: str
    quantidade_esperada: float = Field(ge=0)
    quantidade_conferida: float = Field(ge=0)
    endereco_destino: str
    classificacao_divergencia: str | None = None


class RecebimentoRequest(BaseModel):
    nota_fiscal: str
    fornecedor_id: str
    itens: list[ItemRecebimentoRequest]
    operador: str
    correlation_id: str


class ItemInventarioCiclicoRequest(BaseModel):
    sku_id: str
    endereco_codigo: str
    quantidade_contada: float = Field(ge=0)


class InventarioCiclicoRequest(BaseModel):
    operador: str
    correlation_id: str
    motivo: str
    itens: list[ItemInventarioCiclicoRequest]


class KanbanPoliticaRequest(BaseModel):
    sku_id: str
    elegivel: bool
    kanban_ativo: bool
    faixa_atual: Literal["verde", "amarela", "vermelha"]
    faixa_verde_min: float = Field(ge=0)
    faixa_amarela_min: float = Field(ge=0)
    faixa_vermelha_min: float = Field(ge=0)
    operador: str
    correlation_id: str
    motivo: str


class CurvaABCDItemRequest(BaseModel):
    sku_id: str
    impacto_economico: float = Field(ge=0)
    variabilidade: float = Field(ge=0)
    shelf_life_dias: int = Field(gt=0)
    dias_sem_venda: int = Field(ge=0)
    giro_periodo: float
    lead_time_dias: float


class CurvaABCDProcessarRequest(BaseModel):
    operador: str
    correlation_id: str
    itens: list[CurvaABCDItemRequest]


class GiroEstoqueItemRequest(BaseModel):
    sku_id: str
    classe_abc: Literal["A", "B", "C", "D"]
    estoque_atual: float = Field(ge=0)
    venda_media_diaria_prevista: float = Field(ge=0)
    total_vendido_periodo: float = Field(ge=0)
    estoque_medio_periodo: float = Field(ge=0)
    ruptura_recorrente: bool = False
    lead_time_dias: float = Field(ge=0)
    shelf_life_dias: int = Field(gt=0)


class GiroEstoqueProcessarRequest(BaseModel):
    operador: str
    correlation_id: str
    itens: list[GiroEstoqueItemRequest]


class SazonalidadeItemRequest(BaseModel):
    sku_id: str
    fator_sazonal: float = Field(gt=0)
    confianca_modelo: float = Field(ge=0, le=1)
    janela_analise_meses: int = Field(gt=0)
    mudanca_estrutural: bool = False
    origem_motor: str
    versao_modelo: str | None = None


class SazonalidadeProcessarRequest(BaseModel):
    operador: str
    correlation_id: str
    itens: list[SazonalidadeItemRequest]


class OrcamentoAporteRequest(BaseModel):
    valor: float = Field(gt=0)
    origem: str
    destino: str | None = None
    validade_ate: date | None = None
    aprovado_por: str | None = None
    observacao: str | None = None


class OrcamentoAprovacaoExcecaoRequest(BaseModel):
    aprovado_por: str
    motivo: str
    valor_aprovado: float | None = Field(default=None, gt=0)


class OrcamentoSimulacaoRequest(BaseModel):
    operador: str
    correlation_id: str
    periodo_referencia: date
    categoria_id: str
    valor_compra_sugerida: float = Field(gt=0)
    orcamento_total_periodo: float = Field(ge=0)
    orcamento_categoria_periodo: float = Field(ge=0)
    consumo_atual_total: float = Field(ge=0)
    consumo_atual_categoria: float = Field(ge=0)
    aporte_externo: OrcamentoAporteRequest | None = None
    aprovacao_excecao: OrcamentoAprovacaoExcecaoRequest | None = None


_inmemory_estoque = InMemoryEstoqueRepository(
    skus_ativos={"sku_001", "sku_002"},
    enderecos_validos={"DEP-A-01", "DEP-A-02", "LOJA-FR-01"},
)
_inmemory_mov = InMemoryMovimentacaoRepository()
_inmemory_inv = InMemoryInventarioRepository()
_inmemory_kanban = InMemoryKanbanRepository()
_inmemory_politica_reposicao = InMemoryPoliticaReposicaoRepository()
_inmemory_sinal_externo = InMemorySinalExternoRepository()
_inmemory_orcamento = InMemoryOrcamentoRepository()
_inmemory_rec = InMemoryRecebimentoRepository()
_inmemory_pub = InMemoryEventPublisher(tenant_id=TENANT_ID)


def _raise_http(exc: Exception) -> None:
    if isinstance(exc, NotaFiscalDuplicada):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if isinstance(exc, IdempotencyPayloadConflict):
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if isinstance(exc, DomainError):
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    raise HTTPException(status_code=500, detail=f"erro_interno: {exc}") from exc


def _execute_postgres_with_idempotency(
    *,
    connection,
    operation_name: str,
    correlation_id: str,
    request_payload: dict,
    execute,
) -> dict:
    idem_repo = PostgresIdempotencyRepository(connection)
    state = idem_repo.acquire(
        operation_name=operation_name,
        correlation_id=correlation_id,
        request_payload=request_payload,
    )
    if state.cached_response is not None:
        return state.cached_response

    response_payload = execute()
    idem_repo.mark_completed(state.key, response_payload)
    return response_payload


@app.get("/v1/health")
def health() -> dict:
    return {"status": "ok", "backend": API_BACKEND}


@app.get("/favicon.ico")
def favicon() -> Response:
    return Response(status_code=204)


@app.post("/v1/movimentacoes")
def registrar_movimentacao(body: MovimentacaoRequest) -> dict:
    data = RegistrarMovimentacaoEstoqueInput(**body.model_dump())
    try:
        if API_BACKEND == "postgres":
            conn = get_connection_postgres()
            try:
                estoque_repo = PostgresEstoqueRepository(conn)
                mov_repo = PostgresMovimentacaoRepository(conn)
                publisher = PostgresEventStore(conn, tenant_id=TENANT_ID)
                use_case = RegistrarMovimentacaoEstoque(mov_repo, estoque_repo, publisher)
                with postgres_transaction(conn):
                    out = _execute_postgres_with_idempotency(
                        connection=conn,
                        operation_name="registrar_movimentacao",
                        correlation_id=data.correlation_id,
                        request_payload=body.model_dump(mode="json"),
                        execute=lambda: asdict(use_case.execute(data)),
                    )
                return out
            finally:
                conn.close()

        use_case = RegistrarMovimentacaoEstoque(
            _inmemory_mov,
            _inmemory_estoque,
            _inmemory_pub,
        )
        out = use_case.execute(data)
        return asdict(out)
    except Exception as exc:
        _raise_http(exc)


@app.post("/v1/ajustes")
def registrar_ajuste(body: AjusteRequest) -> dict:
    data = RegistrarAjusteEstoqueInput(**body.model_dump())
    try:
        if API_BACKEND == "postgres":
            conn = get_connection_postgres()
            try:
                estoque_repo = PostgresEstoqueRepository(conn)
                mov_repo = PostgresMovimentacaoRepository(conn)
                publisher = PostgresEventStore(conn, tenant_id=TENANT_ID)
                use_case = RegistrarAjusteEstoque(mov_repo, estoque_repo, publisher)
                with postgres_transaction(conn):
                    out = _execute_postgres_with_idempotency(
                        connection=conn,
                        operation_name="registrar_ajuste",
                        correlation_id=data.correlation_id,
                        request_payload=body.model_dump(mode="json"),
                        execute=lambda: asdict(use_case.execute(data)),
                    )
                return out
            finally:
                conn.close()

        use_case = RegistrarAjusteEstoque(
            _inmemory_mov,
            _inmemory_estoque,
            _inmemory_pub,
        )
        out = use_case.execute(data)
        return asdict(out)
    except Exception as exc:
        _raise_http(exc)


@app.post("/v1/avarias")
def registrar_avaria(body: AvariaRequest) -> dict:
    data = RegistrarAvariaEstoqueInput(**body.model_dump())
    try:
        if API_BACKEND == "postgres":
            conn = get_connection_postgres()
            try:
                estoque_repo = PostgresEstoqueRepository(conn)
                mov_repo = PostgresMovimentacaoRepository(conn)
                publisher = PostgresEventStore(conn, tenant_id=TENANT_ID)
                use_case = RegistrarAvariaEstoque(mov_repo, estoque_repo, publisher)
                with postgres_transaction(conn):
                    out = _execute_postgres_with_idempotency(
                        connection=conn,
                        operation_name="registrar_avaria",
                        correlation_id=data.correlation_id,
                        request_payload=body.model_dump(mode="json"),
                        execute=lambda: asdict(use_case.execute(data)),
                    )
                return out
            finally:
                conn.close()

        use_case = RegistrarAvariaEstoque(
            _inmemory_mov,
            _inmemory_estoque,
            _inmemory_pub,
        )
        out = use_case.execute(data)
        return asdict(out)
    except Exception as exc:
        _raise_http(exc)


@app.post("/v1/recebimentos")
def registrar_recebimento(body: RecebimentoRequest) -> dict:
    itens = [ItemRecebimentoInput(**item.model_dump()) for item in body.itens]
    data = RegistrarRecebimentoInput(
        nota_fiscal=body.nota_fiscal,
        fornecedor_id=body.fornecedor_id,
        itens=itens,
        operador=body.operador,
        correlation_id=body.correlation_id,
    )
    try:
        if API_BACKEND == "postgres":
            conn = get_connection_postgres()
            try:
                estoque_repo = PostgresEstoqueRepository(conn)
                rec_repo = PostgresRecebimentoRepository(conn)
                publisher = PostgresEventStore(conn, tenant_id=TENANT_ID)
                use_case = RegistrarRecebimento(rec_repo, estoque_repo, publisher)
                with postgres_transaction(conn):
                    out = _execute_postgres_with_idempotency(
                        connection=conn,
                        operation_name="registrar_recebimento",
                        correlation_id=data.correlation_id,
                        request_payload=body.model_dump(mode="json"),
                        execute=lambda: asdict(use_case.execute(data)),
                    )
                return out
            finally:
                conn.close()

        use_case = RegistrarRecebimento(
            _inmemory_rec,
            _inmemory_estoque,
            _inmemory_pub,
        )
        out = use_case.execute(data)
        return asdict(out)
    except Exception as exc:
        _raise_http(exc)


@app.post("/v1/inventarios/ciclico")
def registrar_inventario_ciclico(body: InventarioCiclicoRequest) -> dict:
    itens = [ItemContagemCiclicaInput(**item.model_dump()) for item in body.itens]
    data = RegistrarInventarioCiclicoInput(
        operador=body.operador,
        correlation_id=body.correlation_id,
        motivo=body.motivo,
        itens=itens,
    )
    try:
        if API_BACKEND == "postgres":
            conn = get_connection_postgres()
            try:
                estoque_repo = PostgresEstoqueRepository(conn)
                mov_repo = PostgresMovimentacaoRepository(conn)
                inv_repo = PostgresInventarioRepository(conn)
                publisher = PostgresEventStore(conn, tenant_id=TENANT_ID)
                use_case = RegistrarInventarioCiclico(
                    mov_repo,
                    estoque_repo,
                    inv_repo,
                    publisher,
                )
                with postgres_transaction(conn):
                    out = _execute_postgres_with_idempotency(
                        connection=conn,
                        operation_name="registrar_inventario_ciclico",
                        correlation_id=data.correlation_id,
                        request_payload=body.model_dump(mode="json"),
                        execute=lambda: asdict(use_case.execute(data)),
                    )
                return out
            finally:
                conn.close()

        use_case = RegistrarInventarioCiclico(
            _inmemory_mov,
            _inmemory_estoque,
            _inmemory_inv,
            _inmemory_pub,
        )
        out = use_case.execute(data)
        return asdict(out)
    except Exception as exc:
        _raise_http(exc)


@app.post("/v1/kanban/politicas")
def registrar_politica_kanban(body: KanbanPoliticaRequest) -> dict:
    data = RegistrarPoliticaKanbanInput(**body.model_dump())
    try:
        if API_BACKEND == "postgres":
            conn = get_connection_postgres()
            try:
                estoque_repo = PostgresEstoqueRepository(conn)
                kanban_repo = PostgresKanbanRepository(conn)
                publisher = PostgresEventStore(conn, tenant_id=TENANT_ID)
                use_case = RegistrarPoliticaKanban(estoque_repo, kanban_repo, publisher)
                with postgres_transaction(conn):
                    out = _execute_postgres_with_idempotency(
                        connection=conn,
                        operation_name="registrar_politica_kanban",
                        correlation_id=data.correlation_id,
                        request_payload=body.model_dump(mode="json"),
                        execute=lambda: asdict(use_case.execute(data)),
                    )
                return out
            finally:
                conn.close()

        use_case = RegistrarPoliticaKanban(
            _inmemory_estoque,
            _inmemory_kanban,
            _inmemory_pub,
        )
        out = use_case.execute(data)
        return asdict(out)
    except Exception as exc:
        _raise_http(exc)


@app.post("/v1/curva-abcd/processar")
def processar_curva_abcd(body: CurvaABCDProcessarRequest) -> dict:
    itens = [ItemCurvaABCDInput(**item.model_dump()) for item in body.itens]
    data = ProcessarCurvaABCDInput(
        operador=body.operador,
        correlation_id=body.correlation_id,
        itens=itens,
    )
    try:
        if API_BACKEND == "postgres":
            conn = get_connection_postgres()
            try:
                estoque_repo = PostgresEstoqueRepository(conn)
                politica_repo = PostgresPoliticaReposicaoRepository(conn)
                publisher = PostgresEventStore(conn, tenant_id=TENANT_ID)
                use_case = ProcessarCurvaABCD(estoque_repo, politica_repo, publisher)
                with postgres_transaction(conn):
                    out = _execute_postgres_with_idempotency(
                        connection=conn,
                        operation_name="processar_curva_abcd",
                        correlation_id=data.correlation_id,
                        request_payload=body.model_dump(mode="json"),
                        execute=lambda: asdict(use_case.execute(data)),
                    )
                return out
            finally:
                conn.close()

        use_case = ProcessarCurvaABCD(
            _inmemory_estoque,
            _inmemory_politica_reposicao,
            _inmemory_pub,
        )
        out = use_case.execute(data)
        return asdict(out)
    except Exception as exc:
        _raise_http(exc)


@app.post("/v1/giro/processar")
def processar_giro_estoque(body: GiroEstoqueProcessarRequest) -> dict:
    itens = [ItemGiroEstoqueInput(**item.model_dump()) for item in body.itens]
    data = ProcessarGiroEstoqueInput(
        operador=body.operador,
        correlation_id=body.correlation_id,
        itens=itens,
    )
    try:
        if API_BACKEND == "postgres":
            conn = get_connection_postgres()
            try:
                estoque_repo = PostgresEstoqueRepository(conn)
                politica_repo = PostgresPoliticaReposicaoRepository(conn)
                publisher = PostgresEventStore(conn, tenant_id=TENANT_ID)
                use_case = ProcessarGiroEstoque(estoque_repo, politica_repo, publisher)
                with postgres_transaction(conn):
                    out = _execute_postgres_with_idempotency(
                        connection=conn,
                        operation_name="processar_giro_estoque",
                        correlation_id=data.correlation_id,
                        request_payload=body.model_dump(mode="json"),
                        execute=lambda: asdict(use_case.execute(data)),
                    )
                return out
            finally:
                conn.close()

        use_case = ProcessarGiroEstoque(
            _inmemory_estoque,
            _inmemory_politica_reposicao,
            _inmemory_pub,
        )
        out = use_case.execute(data)
        return asdict(out)
    except Exception as exc:
        _raise_http(exc)


@app.post("/v1/sazonalidade/processar")
def processar_sazonalidade(body: SazonalidadeProcessarRequest) -> dict:
    itens = [ItemSazonalidadeInput(**item.model_dump()) for item in body.itens]
    data = ProcessarSazonalidadeOperacionalInput(
        operador=body.operador,
        correlation_id=body.correlation_id,
        itens=itens,
    )
    try:
        if API_BACKEND == "postgres":
            conn = get_connection_postgres()
            try:
                estoque_repo = PostgresEstoqueRepository(conn)
                politica_repo = PostgresPoliticaReposicaoRepository(conn)
                sinal_repo = PostgresSinalExternoRepository(conn)
                publisher = PostgresEventStore(conn, tenant_id=TENANT_ID)
                use_case = ProcessarSazonalidadeOperacional(
                    estoque_repo,
                    politica_repo,
                    sinal_repo,
                    publisher,
                )
                with postgres_transaction(conn):
                    out = _execute_postgres_with_idempotency(
                        connection=conn,
                        operation_name="processar_sazonalidade_operacional",
                        correlation_id=data.correlation_id,
                        request_payload=body.model_dump(mode="json"),
                        execute=lambda: asdict(use_case.execute(data)),
                    )
                return out
            finally:
                conn.close()

        use_case = ProcessarSazonalidadeOperacional(
            _inmemory_estoque,
            _inmemory_politica_reposicao,
            _inmemory_sinal_externo,
            _inmemory_pub,
        )
        out = use_case.execute(data)
        return asdict(out)
    except Exception as exc:
        _raise_http(exc)


@app.post("/v1/orcamento/simular")
def processar_governanca_orcamentaria(body: OrcamentoSimulacaoRequest) -> dict:
    aporte = None
    if body.aporte_externo is not None:
        aporte = AporteExternoInput(
            valor=body.aporte_externo.valor,
            origem=body.aporte_externo.origem,
            destino=body.aporte_externo.destino,
            validade_ate=body.aporte_externo.validade_ate,
            aprovado_por=body.aporte_externo.aprovado_por,
            observacao=body.aporte_externo.observacao,
        )

    aprovacao = None
    if body.aprovacao_excecao is not None:
        aprovacao = AprovacaoExcecaoInput(
            aprovado_por=body.aprovacao_excecao.aprovado_por,
            motivo=body.aprovacao_excecao.motivo,
            valor_aprovado=body.aprovacao_excecao.valor_aprovado,
        )

    data = ProcessarGovernancaOrcamentariaInput(
        operador=body.operador,
        correlation_id=body.correlation_id,
        periodo_referencia=body.periodo_referencia,
        categoria_id=body.categoria_id,
        valor_compra_sugerida=body.valor_compra_sugerida,
        orcamento_total_periodo=body.orcamento_total_periodo,
        orcamento_categoria_periodo=body.orcamento_categoria_periodo,
        consumo_atual_total=body.consumo_atual_total,
        consumo_atual_categoria=body.consumo_atual_categoria,
        aporte_externo=aporte,
        aprovacao_excecao=aprovacao,
    )
    try:
        if API_BACKEND == "postgres":
            conn = get_connection_postgres()
            try:
                orcamento_repo = PostgresOrcamentoRepository(conn)
                publisher = PostgresEventStore(conn, tenant_id=TENANT_ID)
                use_case = ProcessarGovernancaOrcamentaria(orcamento_repo, publisher)
                with postgres_transaction(conn):
                    out = _execute_postgres_with_idempotency(
                        connection=conn,
                        operation_name="processar_governanca_orcamentaria",
                        correlation_id=data.correlation_id,
                        request_payload=body.model_dump(mode="json"),
                        execute=lambda: asdict(use_case.execute(data)),
                    )
                return out
            finally:
                conn.close()

        use_case = ProcessarGovernancaOrcamentaria(
            _inmemory_orcamento,
            _inmemory_pub,
        )
        out = use_case.execute(data)
        return asdict(out)
    except Exception as exc:
        _raise_http(exc)
