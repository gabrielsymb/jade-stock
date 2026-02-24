"""Vertical slice: ProcessarGiroEstoque."""

from dataclasses import dataclass
from typing import Protocol

from wms.domain.exceptions import QuantidadeInvalida, RegraGiroInvalida, SKUInativoOuInexistente


@dataclass(frozen=True)
class ItemGiroEstoqueInput:
    sku_id: str
    classe_abc: str
    estoque_atual: float
    venda_media_diaria_prevista: float
    total_vendido_periodo: float
    estoque_medio_periodo: float
    ruptura_recorrente: bool
    lead_time_dias: float
    shelf_life_dias: int


@dataclass(frozen=True)
class ProcessarGiroEstoqueInput:
    operador: str
    correlation_id: str
    itens: list[ItemGiroEstoqueInput]
    meta_giro_a: float = 8.0
    meta_giro_b: float = 4.0
    meta_giro_c: float = 1.0
    cobertura_max_a: float = 10.0
    cobertura_max_b: float = 20.0
    cobertura_max_c: float = 35.0
    cobertura_c_incremento_ruptura: float = 3.0


@dataclass(frozen=True)
class ProcessarGiroEstoqueOutput:
    itens_processados: int
    alertas_acionados: int
    evento_emitido: str


class EstoqueRepository(Protocol):
    def validar_sku_ativo(self, sku_id: str) -> bool: ...


class PoliticaReposicaoRepository(Protocol):
    def salvar_ou_atualizar_politica(self, payload: dict) -> str: ...


class EventPublisher(Protocol):
    def publish(self, event_name: str, payload: dict) -> None: ...


class ProcessarGiroEstoque:
    EVENT_ITEM = "giro_estoque_item_processado"
    EVENT_SUMARIO = "giro_estoque_processado"
    CLASSES_VALIDAS = {"A", "B", "C", "D"}

    def __init__(
        self,
        estoque_repo: EstoqueRepository,
        politica_repo: PoliticaReposicaoRepository,
        publisher: EventPublisher,
    ) -> None:
        self._estoque_repo = estoque_repo
        self._politica_repo = politica_repo
        self._publisher = publisher

    def execute(self, data: ProcessarGiroEstoqueInput) -> ProcessarGiroEstoqueOutput:
        if not data.itens:
            raise QuantidadeInvalida("Processamento de giro exige ao menos um item")
        for item in data.itens:
            self._validar_item(item)

        alertas_acionados = 0
        for item in data.itens:
            cobertura_dias = self._calc_cobertura(item)
            giro_periodo = self._calc_giro(item)
            alertas, acao = self._avaliar_alertas(item, data, cobertura_dias, giro_periodo)
            cobertura_final = cobertura_dias

            if item.classe_abc == "C" and item.ruptura_recorrente:
                cobertura_final = min(
                    data.cobertura_max_c,
                    cobertura_dias + data.cobertura_c_incremento_ruptura,
                )

            politica_id = self._politica_repo.salvar_ou_atualizar_politica(
                {
                    "sku_id": item.sku_id,
                    "classe_abc": item.classe_abc,
                    "cobertura_dias": cobertura_final,
                    "giro_periodo": giro_periodo,
                    "lead_time_dias": item.lead_time_dias,
                    "fator_sazonal": None,
                    "sazonalidade_status": "nao_avaliado",
                    "janela_analise_meses": 3,
                    "shelf_life_dias": item.shelf_life_dias,
                    "risco_vencimento": "baixo",
                    "updated_by": data.operador,
                    "correlation_id": data.correlation_id,
                }
            )

            alertas_acionados += len(alertas)
            self._publisher.publish(
                self.EVENT_ITEM,
                {
                    "politica_reposicao_id": politica_id,
                    "sku_id": item.sku_id,
                    "classe_abc": item.classe_abc,
                    "cobertura_dias": cobertura_final,
                    "giro_periodo": giro_periodo,
                    "alertas": alertas,
                    "acao_sugerida": acao,
                    "actor_id": data.operador,
                    "correlation_id": data.correlation_id,
                },
            )

        self._publisher.publish(
            self.EVENT_SUMARIO,
            {
                "itens_processados": len(data.itens),
                "alertas_acionados": alertas_acionados,
                "actor_id": data.operador,
                "correlation_id": data.correlation_id,
            },
        )
        return ProcessarGiroEstoqueOutput(
            itens_processados=len(data.itens),
            alertas_acionados=alertas_acionados,
            evento_emitido=self.EVENT_SUMARIO,
        )

    def _validar_item(self, item: ItemGiroEstoqueInput) -> None:
        if not self._estoque_repo.validar_sku_ativo(item.sku_id):
            raise SKUInativoOuInexistente(f"SKU invalido ou inativo: {item.sku_id}")
        if item.classe_abc not in self.CLASSES_VALIDAS:
            raise RegraGiroInvalida(f"Classe ABC invalida: {item.classe_abc}")
        if item.estoque_atual < 0:
            raise QuantidadeInvalida("estoque_atual nao pode ser negativo")
        if item.venda_media_diaria_prevista < 0:
            raise QuantidadeInvalida("venda_media_diaria_prevista nao pode ser negativa")
        if item.total_vendido_periodo < 0:
            raise QuantidadeInvalida("total_vendido_periodo nao pode ser negativo")
        if item.estoque_medio_periodo < 0:
            raise QuantidadeInvalida("estoque_medio_periodo nao pode ser negativo")
        if item.lead_time_dias < 0:
            raise QuantidadeInvalida("lead_time_dias nao pode ser negativo")
        if item.shelf_life_dias <= 0:
            raise QuantidadeInvalida("shelf_life_dias deve ser > 0")

    def _calc_cobertura(self, item: ItemGiroEstoqueInput) -> float:
        if item.venda_media_diaria_prevista == 0:
            return 9999.0
        return item.estoque_atual / item.venda_media_diaria_prevista

    def _calc_giro(self, item: ItemGiroEstoqueInput) -> float:
        if item.estoque_medio_periodo == 0:
            return 0.0
        return item.total_vendido_periodo / item.estoque_medio_periodo

    def _avaliar_alertas(
        self,
        item: ItemGiroEstoqueInput,
        data: ProcessarGiroEstoqueInput,
        cobertura_dias: float,
        giro_periodo: float,
    ) -> tuple[list[str], str]:
        alertas: list[str] = []
        acao = "manter_politica"

        meta_giro = {"A": data.meta_giro_a, "B": data.meta_giro_b, "C": data.meta_giro_c, "D": 0.0}[item.classe_abc]
        cobertura_max = {
            "A": data.cobertura_max_a,
            "B": data.cobertura_max_b,
            "C": data.cobertura_max_c,
            "D": data.cobertura_max_c,
        }[item.classe_abc]

        if item.classe_abc == "A" and giro_periodo < meta_giro:
            alertas.append("giro_abaixo_meta_classe_a")
            alertas.append("revisao_politica_reposicao")
            acao = "reduzir_lote_e_aumentar_frequencia"

        if item.classe_abc in {"A", "B"} and cobertura_dias > cobertura_max:
            alertas.append("capital_imobilizado_excessivo")
            if acao == "manter_politica":
                acao = "reduzir_cobertura"

        if item.classe_abc == "C" and item.ruptura_recorrente:
            alertas.append("ruptura_recorrente_item_c")
            alertas.append("revisao_politica_reposicao")
            acao = "elevar_cobertura_com_limites"

        return alertas, acao
