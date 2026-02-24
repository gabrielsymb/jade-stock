"""API minima para expor os casos de uso do WMS."""

from __future__ import annotations

import os
from dataclasses import asdict
from datetime import date
from typing import Literal

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

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

IDEMPOTENCY_NOTE = (
    " Idempotencia: para retry, reutilize o mesmo `correlation_id` com o mesmo payload. "
    "Se enviar o mesmo `correlation_id` com payload diferente, a API retorna `409 Conflict`."
)

IDEMPOTENCY_RESPONSES = {
    409: {
        "description": "Conflito de idempotencia (mesmo correlation_id com payload diferente).",
        "content": {
            "application/json": {
                "example": {
                    "code": "idempotency_payload_conflict",
                    "message": "idempotency payload conflict",
                    "details": None,
                    "correlation_id": "corr_exemplo_001",
                }
            }
        },
    }
}


class ErrorResponse(BaseModel):
    code: str = Field(description="Codigo padrao de erro da API.")
    message: str = Field(description="Mensagem amigavel do erro.")
    details: dict | list | None = Field(
        default=None,
        description="Detalhes adicionais para depuracao.",
    )
    correlation_id: str | None = Field(
        default=None,
        description="Correlation ID relacionado a operacao que falhou.",
    )


class MovimentacaoRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sku_id": "SKU_REFRI_LATA_350",
                "tipo_movimentacao": "transferencia",
                "quantidade": 24,
                "endereco_origem": "DEP-BEB-A-01",
                "endereco_destino": "LOJA-FR-01",
                "operador": "op_deposito_01",
                "correlation_id": "corr_mov_2026-02-24_001",
                "motivo": "Reposicao da frente de loja",
            }
        }
    )

    sku_id: str = Field(
        description="Identificador imutavel do SKU no WMS.",
        examples=["SKU_REFRI_LATA_350"],
    )
    tipo_movimentacao: Literal["entrada", "saida", "transferencia", "ajuste", "avaria"] = Field(
        description="Tipo de movimentacao que sera registrada.",
        examples=["transferencia"],
    )
    quantidade: float = Field(
        gt=0,
        description="Quantidade da movimentacao (deve ser maior que zero).",
        examples=[24],
    )
    endereco_origem: str | None = Field(
        default=None,
        description="Endereco de origem (obrigatorio para saida/transferencia).",
        examples=["DEP-BEB-A-01"],
    )
    endereco_destino: str | None = Field(
        default=None,
        description="Endereco de destino (obrigatorio para entrada/transferencia).",
        examples=["LOJA-FR-01"],
    )
    operador: str = Field(
        description="Identificador de quem executou a operacao.",
        examples=["op_deposito_01"],
    )
    correlation_id: str = Field(
        description="Chave de idempotencia da operacao.",
        examples=["corr_mov_2026-02-24_001"],
    )
    motivo: str | None = Field(
        default=None,
        description="Motivo operacional da movimentacao (quando aplicavel).",
        examples=["Reposicao da frente de loja"],
    )


class AjusteRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sku_id": "SKU_REFRI_LATA_350",
                "endereco_codigo": "DEP-BEB-A-01",
                "quantidade_ajuste": -2,
                "operador": "op_inventario_01",
                "correlation_id": "corr_ajuste_2026-02-24_001",
                "motivo": "Quebra identificada na conferencia",
            }
        }
    )

    sku_id: str = Field(description="SKU que sera ajustado.", examples=["SKU_REFRI_LATA_350"])
    endereco_codigo: str = Field(
        description="Endereco onde o ajuste sera aplicado.",
        examples=["DEP-BEB-A-01"],
    )
    quantidade_ajuste: float = Field(
        description="Quantidade de ajuste (pode ser positiva ou negativa).",
        examples=[-2],
    )
    operador: str = Field(description="Operador responsavel pelo ajuste.", examples=["op_inventario_01"])
    correlation_id: str = Field(
        description="Chave de idempotencia para o ajuste.",
        examples=["corr_ajuste_2026-02-24_001"],
    )
    motivo: str = Field(
        description="Motivo obrigatorio para trilha de auditoria.",
        examples=["Quebra identificada na conferencia"],
    )


class AvariaRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sku_id": "SKU_CERVEJA_LONGNECK_355",
                "endereco_codigo": "DEP-BEB-CAMERA-02",
                "quantidade_avaria": 1,
                "operador": "op_deposito_01",
                "correlation_id": "corr_avaria_2026-02-24_001",
                "motivo": "Garrafa quebrada na movimentacao interna",
            }
        }
    )

    sku_id: str = Field(description="SKU com avaria.", examples=["SKU_CERVEJA_LONGNECK_355"])
    endereco_codigo: str = Field(
        description="Endereco onde a avaria foi identificada.",
        examples=["DEP-BEB-CAMERA-02"],
    )
    quantidade_avaria: float = Field(
        gt=0,
        description="Quantidade avariada (maior que zero).",
        examples=[1],
    )
    operador: str = Field(description="Operador que registrou a avaria.", examples=["op_deposito_01"])
    correlation_id: str = Field(
        description="Chave de idempotencia para evitar duplicidade.",
        examples=["corr_avaria_2026-02-24_001"],
    )
    motivo: str = Field(
        description="Motivo obrigatorio da avaria para auditoria.",
        examples=["Garrafa quebrada na movimentacao interna"],
    )


class ItemRecebimentoRequest(BaseModel):
    sku_codigo: str = Field(
        description="Codigo do SKU recebido no item da nota fiscal.",
        examples=["SKU_REFRI_LATA_350"],
    )
    quantidade_esperada: float = Field(
        ge=0,
        description="Quantidade esperada conforme documento fiscal.",
        examples=[120],
    )
    quantidade_conferida: float = Field(
        ge=0,
        description="Quantidade fisicamente conferida no recebimento.",
        examples=[118],
    )
    endereco_destino: str = Field(
        description="Endereco de armazenamento inicial do item.",
        examples=["DEP-BEB-A-01"],
    )
    classificacao_divergencia: str | None = Field(
        default=None,
        description="Classificacao de divergencia quando esperado <> conferido.",
        examples=["falta"],
    )


class RecebimentoRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "nota_fiscal": "NF-BEB-2026-000123",
                "fornecedor_id": "forn_bebidas_01",
                "itens": [
                    {
                        "sku_codigo": "SKU_REFRI_LATA_350",
                        "quantidade_esperada": 120,
                        "quantidade_conferida": 118,
                        "endereco_destino": "DEP-BEB-A-01",
                        "classificacao_divergencia": "falta",
                    }
                ],
                "operador": "op_recebimento_01",
                "correlation_id": "corr_rec_2026-02-24_001",
            }
        }
    )

    nota_fiscal: str = Field(description="Numero da nota fiscal recebida.", examples=["NF-BEB-2026-000123"])
    fornecedor_id: str = Field(description="Identificador do fornecedor.", examples=["forn_bebidas_01"])
    itens: list[ItemRecebimentoRequest] = Field(
        description="Lista de itens recebidos e conferidos.",
    )
    operador: str = Field(description="Operador responsavel pelo recebimento.", examples=["op_recebimento_01"])
    correlation_id: str = Field(
        description="Chave de idempotencia do recebimento.",
        examples=["corr_rec_2026-02-24_001"],
    )


class ItemInventarioCiclicoRequest(BaseModel):
    sku_id: str = Field(
        description="Identificador imutavel do SKU no WMS. Use o SKU interno, nao EAN.",
        examples=["SKU_REFRI_LATA_350", "SKU_CERVEJA_LONGNECK_355"],
    )
    endereco_codigo: str = Field(
        description="Codigo do endereco fisico onde a contagem foi realizada.",
        examples=["DEP-BEB-A-01", "DEP-BEB-CAMERA-02"],
    )
    quantidade_contada: float = Field(
        ge=0,
        description="Quantidade fisica contada no endereco para o SKU informado.",
        examples=[84, 120],
    )


class InventarioCiclicoRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "operador": "op_deposito_01",
                "correlation_id": "corr_inv_2026-02-24_turno_manha_001",
                "data_referencia": "2026-02-24",
                "motivo": "Contagem ciclica semanal - corredor bebidas",
                "itens": [
                    {
                        "sku_id": "SKU_REFRI_LATA_350",
                        "endereco_codigo": "DEP-BEB-A-01",
                        "quantidade_contada": 84,
                    },
                    {
                        "sku_id": "SKU_CERVEJA_LONGNECK_355",
                        "endereco_codigo": "DEP-BEB-CAMERA-02",
                        "quantidade_contada": 120,
                    },
                ],
            }
        }
    )

    operador: str = Field(
        description="Identificador de quem executou a contagem.",
        examples=["op_deposito_01"],
    )
    correlation_id: str = Field(
        description=(
            "Chave de idempotencia da operacao. Reuse em retries com o mesmo payload "
            "e troque para nova operacao."
        ),
        examples=["corr_inv_2026-02-24_turno_manha_001"],
    )
    data_referencia: date | None = Field(
        default=None,
        description=(
            "Data de referencia da contagem (didatico/auditoria). "
            "Nao altera a regra de negocio do caso de uso atual."
        ),
        examples=["2026-02-24"],
    )
    motivo: str = Field(
        description="Motivo operacional da contagem ciclica. Campo obrigatorio.",
        examples=["Contagem ciclica semanal - corredor bebidas"],
    )
    itens: list[ItemInventarioCiclicoRequest] = Field(
        description="Itens contados no inventario ciclico (SKU/endereco/quantidade).",
    )


class KanbanPoliticaRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "sku_id": "SKU_REFRI_LATA_350",
                "elegivel": True,
                "kanban_ativo": True,
                "faixa_atual": "amarela",
                "faixa_verde_min": 80,
                "faixa_amarela_min": 40,
                "faixa_vermelha_min": 20,
                "operador": "op_planejamento_01",
                "correlation_id": "corr_kanban_2026-02-24_001",
                "motivo": "Politica de reposicao do deposito de bebidas",
            }
        }
    )

    sku_id: str = Field(description="SKU alvo da politica Kanban.", examples=["SKU_REFRI_LATA_350"])
    elegivel: bool = Field(description="Se o SKU e elegivel ao fluxo Kanban.")
    kanban_ativo: bool = Field(description="Liga/desliga a politica Kanban do SKU.")
    faixa_atual: Literal["verde", "amarela", "vermelha"] = Field(
        description="Faixa atual do cartao Kanban.",
        examples=["amarela"],
    )
    faixa_verde_min: float = Field(ge=0, description="Limite minimo da faixa verde.", examples=[80])
    faixa_amarela_min: float = Field(ge=0, description="Limite minimo da faixa amarela.", examples=[40])
    faixa_vermelha_min: float = Field(ge=0, description="Limite minimo da faixa vermelha.", examples=[20])
    operador: str = Field(description="Operador responsavel.", examples=["op_planejamento_01"])
    correlation_id: str = Field(description="Chave de idempotencia da politica.", examples=["corr_kanban_2026-02-24_001"])
    motivo: str = Field(description="Motivo da criacao/alteracao da politica.", examples=["Politica de reposicao do deposito de bebidas"])


class CurvaABCDItemRequest(BaseModel):
    sku_id: str = Field(description="SKU analisado no lote da curva ABCD.", examples=["SKU_REFRI_LATA_350"])
    impacto_economico: float = Field(ge=0, description="Impacto economico acumulado no periodo.", examples=[18500.0])
    variabilidade: float = Field(ge=0, description="Indice de variabilidade da demanda.", examples=[0.32])
    shelf_life_dias: int = Field(gt=0, description="Validade util do item em dias.", examples=[120])
    dias_sem_venda: int = Field(ge=0, description="Dias sem venda no periodo observado.", examples=[4])
    giro_periodo: float = Field(description="Giro do SKU no periodo.", examples=[9.4])
    lead_time_dias: float = Field(description="Lead time de reposicao em dias.", examples=[2.0])


class CurvaABCDProcessarRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "operador": "op_planejamento_01",
                "correlation_id": "corr_abcd_2026-02-24_001",
                "itens": [
                    {
                        "sku_id": "SKU_REFRI_LATA_350",
                        "impacto_economico": 18500.0,
                        "variabilidade": 0.32,
                        "shelf_life_dias": 120,
                        "dias_sem_venda": 4,
                        "giro_periodo": 9.4,
                        "lead_time_dias": 2.0,
                    }
                ],
            }
        }
    )
    operador: str = Field(description="Operador responsavel pelo processamento.", examples=["op_planejamento_01"])
    correlation_id: str = Field(description="Chave de idempotencia do lote.", examples=["corr_abcd_2026-02-24_001"])
    itens: list[CurvaABCDItemRequest] = Field(description="Itens de entrada para classificacao ABCD.")


class GiroEstoqueItemRequest(BaseModel):
    sku_id: str = Field(description="SKU analisado no processamento de giro.", examples=["SKU_REFRI_LATA_350"])
    classe_abc: Literal["A", "B", "C", "D"] = Field(description="Classe ABC atual do SKU.", examples=["A"])
    estoque_atual: float = Field(ge=0, description="Estoque atual em unidades.", examples=[100])
    venda_media_diaria_prevista: float = Field(ge=0, description="Venda media diaria prevista.", examples=[4.2])
    total_vendido_periodo: float = Field(ge=0, description="Total vendido no periodo de analise.", examples=[126])
    estoque_medio_periodo: float = Field(ge=0, description="Estoque medio do periodo.", examples=[24])
    ruptura_recorrente: bool = Field(default=False, description="Marca se houve ruptura recorrente do SKU.")
    lead_time_dias: float = Field(ge=0, description="Lead time medio de reposicao.", examples=[2.0])
    shelf_life_dias: int = Field(gt=0, description="Validade do produto em dias.", examples=[120])


class GiroEstoqueProcessarRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "operador": "op_planejamento_01",
                "correlation_id": "corr_giro_2026-02-24_001",
                "itens": [
                    {
                        "sku_id": "SKU_REFRI_LATA_350",
                        "classe_abc": "A",
                        "estoque_atual": 100,
                        "venda_media_diaria_prevista": 4.2,
                        "total_vendido_periodo": 126,
                        "estoque_medio_periodo": 24,
                        "ruptura_recorrente": False,
                        "lead_time_dias": 2.0,
                        "shelf_life_dias": 120,
                    }
                ],
            }
        }
    )
    operador: str = Field(description="Operador responsavel pelo processamento.", examples=["op_planejamento_01"])
    correlation_id: str = Field(description="Chave de idempotencia do lote.", examples=["corr_giro_2026-02-24_001"])
    itens: list[GiroEstoqueItemRequest] = Field(description="Itens para calculo de giro e cobertura.")


class SazonalidadeItemRequest(BaseModel):
    sku_id: str = Field(description="SKU que recebera ajuste sazonal.", examples=["SKU_REFRI_LATA_350"])
    fator_sazonal: float = Field(gt=0, description="Fator multiplicador sazonal.", examples=[1.20])
    confianca_modelo: float = Field(ge=0, le=1, description="Confianca do modelo externo (0 a 1).", examples=[0.87])
    janela_analise_meses: int = Field(gt=0, description="Janela historica usada no modelo externo.", examples=[24])
    mudanca_estrutural: bool = Field(default=False, description="Indica mudanca estrutural detectada no periodo.")
    origem_motor: str = Field(description="Origem do motor estatistico/IA.", examples=["stats_engine_v2"])
    versao_modelo: str | None = Field(default=None, description="Versao do modelo externo.", examples=["v2.1.0"])


class SazonalidadeProcessarRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "operador": "op_planejamento_01",
                "correlation_id": "corr_sazo_2026-02-24_001",
                "itens": [
                    {
                        "sku_id": "SKU_REFRI_LATA_350",
                        "fator_sazonal": 1.2,
                        "confianca_modelo": 0.87,
                        "janela_analise_meses": 24,
                        "mudanca_estrutural": False,
                        "origem_motor": "stats_engine_v2",
                        "versao_modelo": "v2.1.0",
                    }
                ],
            }
        }
    )
    operador: str = Field(description="Operador responsavel pela carga sazonal.", examples=["op_planejamento_01"])
    correlation_id: str = Field(description="Chave de idempotencia do lote sazonal.", examples=["corr_sazo_2026-02-24_001"])
    itens: list[SazonalidadeItemRequest] = Field(description="Itens com sinal sazonal externo.")


class OrcamentoAporteRequest(BaseModel):
    valor: float = Field(gt=0, description="Valor do aporte externo.", examples=[5000.0])
    origem: str = Field(description="Origem do recurso.", examples=["fundo_emergencial"])
    destino: str | None = Field(default=None, description="Destino do aporte (opcional).", examples=["categoria_bebidas"])
    validade_ate: date | None = Field(default=None, description="Data limite de validade do aporte.", examples=["2026-12-31"])
    aprovado_por: str | None = Field(default=None, description="Responsavel pela aprovacao do aporte.", examples=["gestor_financeiro_01"])
    observacao: str | None = Field(default=None, description="Observacao complementar.", examples=["Aporte para alta sazonal de verao"])


class OrcamentoAprovacaoExcecaoRequest(BaseModel):
    aprovado_por: str = Field(description="Aprovador da excecao.", examples=["gerente_regional_01"])
    motivo: str = Field(description="Justificativa da excecao.", examples=["Item critico para abastecimento da rede"])
    valor_aprovado: float | None = Field(
        default=None,
        gt=0,
        description="Valor autorizado na excecao (se parcial).",
        examples=[2200.0],
    )


class OrcamentoSimulacaoRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "operador": "op_financeiro_01",
                "correlation_id": "corr_orc_2026-02-24_001",
                "periodo_referencia": "2026-02-01",
                "categoria_id": "bebidas",
                "valor_compra_sugerida": 2500.0,
                "orcamento_total_periodo": 12000.0,
                "orcamento_categoria_periodo": 3000.0,
                "consumo_atual_total": 8200.0,
                "consumo_atual_categoria": 900.0,
                "aporte_externo": {
                    "valor": 5000.0,
                    "origem": "fundo_emergencial",
                    "destino": "categoria_bebidas",
                    "validade_ate": "2026-12-31",
                    "aprovado_por": "gestor_financeiro_01",
                    "observacao": "Aporte para alta sazonal de verao",
                },
                "aprovacao_excecao": {
                    "aprovado_por": "gerente_regional_01",
                    "motivo": "Item critico para abastecimento da rede",
                    "valor_aprovado": 2200.0,
                },
            }
        }
    )

    operador: str = Field(description="Operador responsavel pela simulacao.", examples=["op_financeiro_01"])
    correlation_id: str = Field(description="Chave de idempotencia da simulacao.", examples=["corr_orc_2026-02-24_001"])
    periodo_referencia: date = Field(description="Data base do periodo orcamentario.", examples=["2026-02-01"])
    categoria_id: str = Field(description="Categoria analisada na simulacao.", examples=["bebidas"])
    valor_compra_sugerida: float = Field(gt=0, description="Valor da compra proposta.", examples=[2500.0])
    orcamento_total_periodo: float = Field(ge=0, description="Orcamento total do periodo.", examples=[12000.0])
    orcamento_categoria_periodo: float = Field(ge=0, description="Orcamento da categoria no periodo.", examples=[3000.0])
    consumo_atual_total: float = Field(ge=0, description="Consumo total ja realizado no periodo.", examples=[8200.0])
    consumo_atual_categoria: float = Field(ge=0, description="Consumo atual da categoria no periodo.", examples=[900.0])
    aporte_externo: OrcamentoAporteRequest | None = Field(default=None, description="Aporte opcional para ampliar limite.")
    aprovacao_excecao: OrcamentoAprovacaoExcecaoRequest | None = Field(default=None, description="Aprovacao opcional para excecao.")


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


def _build_error(
    *,
    code: str,
    message: str,
    status_code: int,
    details: dict | list | None = None,
    correlation_id: str | None = None,
) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={
            "code": code,
            "message": message,
            "details": details,
            "correlation_id": correlation_id,
        },
    )


def _raise_http(exc: Exception, *, correlation_id: str | None = None) -> None:
    if isinstance(exc, NotaFiscalDuplicada):
        raise _build_error(
            code="nota_fiscal_duplicada",
            message=str(exc),
            status_code=409,
            correlation_id=correlation_id,
        ) from exc
    if isinstance(exc, IdempotencyPayloadConflict):
        raise _build_error(
            code="idempotency_payload_conflict",
            message=str(exc),
            status_code=409,
            correlation_id=correlation_id,
        ) from exc
    if isinstance(exc, DomainError):
        raise _build_error(
            code="domain_error",
            message=str(exc),
            status_code=400,
            correlation_id=correlation_id,
        ) from exc
    raise _build_error(
        code="internal_error",
        message="erro_interno",
        status_code=500,
        details={"error": str(exc)},
        correlation_id=correlation_id,
    ) from exc


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    correlation_id = request.headers.get("X-Correlation-ID")
    if not correlation_id:
        try:
            body = await request.json()
        except Exception:
            body = None
        if isinstance(body, dict):
            correlation_id = body.get("correlation_id")
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            code="validation_error",
            message="payload_invalido",
            details=exc.errors(),
            correlation_id=correlation_id,
        ).model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    if isinstance(exc.detail, dict) and "code" in exc.detail and "message" in exc.detail:
        content = ErrorResponse(
            code=exc.detail.get("code", "http_error"),
            message=exc.detail.get("message", "erro_http"),
            details=exc.detail.get("details"),
            correlation_id=exc.detail.get("correlation_id"),
        ).model_dump()
        return JSONResponse(status_code=exc.status_code, content=content)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(code="http_error", message=str(exc.detail)).model_dump(),
    )


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


@app.get(
    "/v1/health",
    summary="Health check da API",
    description="Retorna status da API e backend ativo (inmemory ou postgres).",
)
def health() -> dict:
    return {"status": "ok", "backend": API_BACKEND}


@app.get("/favicon.ico")
def favicon() -> Response:
    return Response(status_code=204)


@app.post(
    "/v1/movimentacoes",
    summary="Registrar movimentacao de estoque",
    description=(
        "Registra entrada, saida, transferencia, ajuste ou avaria com validacoes de negocio."
        + IDEMPOTENCY_NOTE
    ),
    responses=IDEMPOTENCY_RESPONSES,
)
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
        _raise_http(exc, correlation_id=data.correlation_id)


@app.post(
    "/v1/ajustes",
    summary="Registrar ajuste de estoque",
    description=(
        "Aplica ajuste positivo ou negativo no saldo, com motivo obrigatorio e trilha de auditoria."
        + IDEMPOTENCY_NOTE
    ),
    responses=IDEMPOTENCY_RESPONSES,
)
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
        _raise_http(exc, correlation_id=data.correlation_id)


@app.post(
    "/v1/avarias",
    summary="Registrar avaria de estoque",
    description=(
        "Registra perda operacional por avaria com validacoes de saldo e motivo obrigatorio."
        + IDEMPOTENCY_NOTE
    ),
    responses=IDEMPOTENCY_RESPONSES,
)
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
        _raise_http(exc, correlation_id=data.correlation_id)


@app.post(
    "/v1/recebimentos",
    summary="Registrar recebimento com conferencia",
    description=(
        "Registra nota fiscal, conferencia por item e trata divergencias de recebimento."
        + IDEMPOTENCY_NOTE
    ),
    responses=IDEMPOTENCY_RESPONSES,
)
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
        _raise_http(exc, correlation_id=data.correlation_id)


@app.post(
    "/v1/inventarios/ciclico",
    summary="Registrar inventario ciclico",
    description=(
        "Registra contagem fisica por SKU/endereco, compara com saldo sistemico e "
        "gera ajustes automaticos quando houver divergencia."
        + IDEMPOTENCY_NOTE
    ),
    responses=IDEMPOTENCY_RESPONSES,
)
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
        _raise_http(exc, correlation_id=data.correlation_id)


@app.post(
    "/v1/kanban/politicas",
    summary="Registrar politica Kanban",
    description=(
        "Cria ou atualiza politica Kanban por SKU, com faixas e eventos de reposicao."
        + IDEMPOTENCY_NOTE
    ),
    responses=IDEMPOTENCY_RESPONSES,
)
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
        _raise_http(exc, correlation_id=data.correlation_id)


@app.post(
    "/v1/curva-abcd/processar",
    summary="Processar curva ABCD",
    description=(
        "Classifica itens em A/B/C/D e atualiza politica operacional de cobertura/reposicao."
        + IDEMPOTENCY_NOTE
    ),
    responses=IDEMPOTENCY_RESPONSES,
)
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
        _raise_http(exc, correlation_id=data.correlation_id)


@app.post(
    "/v1/giro/processar",
    summary="Processar giro de estoque",
    description=(
        "Calcula giro e cobertura por item, emitindo alertas operacionais e atualizando politica."
        + IDEMPOTENCY_NOTE
    ),
    responses=IDEMPOTENCY_RESPONSES,
)
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
        _raise_http(exc, correlation_id=data.correlation_id)


@app.post(
    "/v1/sazonalidade/processar",
    summary="Processar sazonalidade operacional",
    description=(
        "Aplica sinal sazonal externo de forma deterministica e auditavel na politica de estoque."
        + IDEMPOTENCY_NOTE
    ),
    responses=IDEMPOTENCY_RESPONSES,
)
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
        _raise_http(exc, correlation_id=data.correlation_id)


@app.post(
    "/v1/orcamento/simular",
    summary="Simular governanca orcamentaria",
    description=(
        "Valida compra sugerida contra limites de orcamento total/categoria e registra excecoes."
        + IDEMPOTENCY_NOTE
    ),
    responses=IDEMPOTENCY_RESPONSES,
)
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
        _raise_http(exc, correlation_id=data.correlation_id)
