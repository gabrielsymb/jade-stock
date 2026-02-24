"""Vertical slice: ProcessarCurvaABCD."""

from dataclasses import dataclass
from typing import Protocol

from wms.domain.exceptions import QuantidadeInvalida, SKUInativoOuInexistente


@dataclass(frozen=True)
class ItemCurvaABCDInput:
    sku_id: str
    impacto_economico: float
    variabilidade: float
    shelf_life_dias: int
    dias_sem_venda: int
    giro_periodo: float
    lead_time_dias: float


@dataclass(frozen=True)
class ProcessarCurvaABCDInput:
    operador: str
    correlation_id: str
    itens: list[ItemCurvaABCDInput]
    limite_a: float = 0.80
    limite_b: float = 0.95
    limite_c: float = 0.995
    cobertura_classe_a: float = 7.0
    cobertura_classe_b: float = 14.0
    cobertura_classe_c: float = 21.0
    cobertura_classe_d: float = 3.0
    limite_variabilidade_alta: float = 0.35
    colchao_variabilidade_dias: float = 3.0
    margem_shelf_life_dias: int = 2
    limite_baixo_giro_dias: int = 90
    cobertura_minima_baixo_giro: float = 1.0


@dataclass(frozen=True)
class ProcessarCurvaABCDOutput:
    itens_processados: int
    alertas_acionados: int
    evento_emitido: str


class EstoqueRepository(Protocol):
    def validar_sku_ativo(self, sku_id: str) -> bool: ...


class PoliticaReposicaoRepository(Protocol):
    def salvar_ou_atualizar_politica(self, payload: dict) -> str: ...


class EventPublisher(Protocol):
    def publish(self, event_name: str, payload: dict) -> None: ...


class ProcessarCurvaABCD:
    EVENT_ITEM = "curva_abcd_item_processado"
    EVENT_SUMARIO = "curva_abcd_processada"

    def __init__(
        self,
        estoque_repo: EstoqueRepository,
        politica_repo: PoliticaReposicaoRepository,
        publisher: EventPublisher,
    ) -> None:
        self._estoque_repo = estoque_repo
        self._politica_repo = politica_repo
        self._publisher = publisher

    def execute(self, data: ProcessarCurvaABCDInput) -> ProcessarCurvaABCDOutput:
        if not data.itens:
            raise QuantidadeInvalida("Processamento ABCD exige ao menos um item")
        for item in data.itens:
            self._validar_item(item)

        ordered = sorted(data.itens, key=lambda x: x.impacto_economico, reverse=True)
        total_impacto = sum(x.impacto_economico for x in ordered)
        acumulado = 0.0
        alertas_acionados = 0

        for item in ordered:
            acumulado += item.impacto_economico
            share = (acumulado / total_impacto) if total_impacto > 0 else 1.0
            classe = self._classe_por_share(share, data)
            cobertura_base = self._cobertura_por_classe(classe, data)

            cobertura = cobertura_base
            alertas_item: list[str] = []
            justificativas: list[str] = [f"classe_{classe}"]

            if item.variabilidade > data.limite_variabilidade_alta:
                cobertura += data.colchao_variabilidade_dias
                alertas_item.append("revisao_classificacao")
                justificativas.append("colchao_variabilidade")

            shelf_limit = max(float(data.cobertura_minima_baixo_giro), item.shelf_life_dias - data.margem_shelf_life_dias)
            if cobertura > shelf_limit:
                cobertura = shelf_limit
                alertas_item.append("alerta_perecibilidade")
                justificativas.append("limitado_por_shelf_life")

            if item.dias_sem_venda >= data.limite_baixo_giro_dias:
                cobertura = min(cobertura, data.cobertura_minima_baixo_giro)
                alertas_item.append("baixo_giro_critico")
                alertas_item.append("capital_imobilizado")
                justificativas.append("baixo_giro")

            politica_id = self._politica_repo.salvar_ou_atualizar_politica(
                {
                    "sku_id": item.sku_id,
                    "classe_abc": classe,
                    "cobertura_dias": cobertura,
                    "giro_periodo": item.giro_periodo,
                    "lead_time_dias": item.lead_time_dias,
                    "fator_sazonal": None,
                    "sazonalidade_status": "nao_avaliado",
                    "janela_analise_meses": 3,
                    "shelf_life_dias": item.shelf_life_dias,
                    "risco_vencimento": "alto" if "alerta_perecibilidade" in alertas_item else "baixo",
                    "updated_by": data.operador,
                    "correlation_id": data.correlation_id,
                }
            )

            alertas_acionados += len(alertas_item)
            self._publisher.publish(
                self.EVENT_ITEM,
                {
                    "politica_reposicao_id": politica_id,
                    "sku_id": item.sku_id,
                    "classe_abc": classe,
                    "cobertura_dias": cobertura,
                    "share_acumulado": round(share, 6),
                    "alertas": alertas_item,
                    "justificativa": ",".join(justificativas),
                    "actor_id": data.operador,
                    "correlation_id": data.correlation_id,
                },
            )

        self._publisher.publish(
            self.EVENT_SUMARIO,
            {
                "itens_processados": len(ordered),
                "alertas_acionados": alertas_acionados,
                "actor_id": data.operador,
                "correlation_id": data.correlation_id,
            },
        )

        return ProcessarCurvaABCDOutput(
            itens_processados=len(ordered),
            alertas_acionados=alertas_acionados,
            evento_emitido=self.EVENT_SUMARIO,
        )

    def _validar_item(self, item: ItemCurvaABCDInput) -> None:
        if not self._estoque_repo.validar_sku_ativo(item.sku_id):
            raise SKUInativoOuInexistente(f"SKU invalido ou inativo: {item.sku_id}")
        if item.impacto_economico < 0:
            raise QuantidadeInvalida("impacto_economico nao pode ser negativo")
        if item.variabilidade < 0:
            raise QuantidadeInvalida("variabilidade nao pode ser negativa")
        if item.shelf_life_dias <= 0:
            raise QuantidadeInvalida("shelf_life_dias deve ser > 0")
        if item.dias_sem_venda < 0:
            raise QuantidadeInvalida("dias_sem_venda nao pode ser negativo")

    def _classe_por_share(self, share: float, data: ProcessarCurvaABCDInput) -> str:
        if share <= data.limite_a:
            return "A"
        if share <= data.limite_b:
            return "B"
        if share <= data.limite_c:
            return "C"
        return "D"

    def _cobertura_por_classe(self, classe: str, data: ProcessarCurvaABCDInput) -> float:
        if classe == "A":
            return data.cobertura_classe_a
        if classe == "B":
            return data.cobertura_classe_b
        if classe == "C":
            return data.cobertura_classe_c
        return data.cobertura_classe_d
