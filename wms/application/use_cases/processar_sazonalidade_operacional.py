"""Vertical slice: ProcessarSazonalidadeOperacional."""

from dataclasses import dataclass
from typing import Protocol

from wms.domain.exceptions import QuantidadeInvalida, RegraSazonalidadeInvalida, SKUInativoOuInexistente


@dataclass(frozen=True)
class ItemSazonalidadeInput:
    sku_id: str
    fator_sazonal: float
    confianca_modelo: float
    janela_analise_meses: int
    mudanca_estrutural: bool
    origem_motor: str
    versao_modelo: str | None = None


@dataclass(frozen=True)
class ProcessarSazonalidadeOperacionalInput:
    operador: str
    correlation_id: str
    itens: list[ItemSazonalidadeInput]
    confianca_minima: float = 0.7
    janela_minima_meses: int = 24
    margem_shelf_life_dias: int = 2


@dataclass(frozen=True)
class ProcessarSazonalidadeOperacionalOutput:
    itens_processados: int
    alertas_acionados: int
    evento_emitido: str


class EstoqueRepository(Protocol):
    def validar_sku_ativo(self, sku_id: str) -> bool: ...


class PoliticaReposicaoRepository(Protocol):
    def obter_politica(self, sku_id: str) -> dict | None: ...
    def salvar_ou_atualizar_politica(self, payload: dict) -> str: ...


class SinalExternoRepository(Protocol):
    def salvar_sinal(self, payload: dict) -> str: ...


class EventPublisher(Protocol):
    def publish(self, event_name: str, payload: dict) -> None: ...


class ProcessarSazonalidadeOperacional:
    EVENT_ITEM = "sazonalidade_item_processada"
    EVENT_SUMARIO = "sazonalidade_processada"

    def __init__(
        self,
        estoque_repo: EstoqueRepository,
        politica_repo: PoliticaReposicaoRepository,
        sinal_repo: SinalExternoRepository,
        publisher: EventPublisher,
    ) -> None:
        self._estoque_repo = estoque_repo
        self._politica_repo = politica_repo
        self._sinal_repo = sinal_repo
        self._publisher = publisher

    def execute(
        self,
        data: ProcessarSazonalidadeOperacionalInput,
    ) -> ProcessarSazonalidadeOperacionalOutput:
        if not data.itens:
            raise QuantidadeInvalida("Processamento sazonal exige ao menos um item")
        for item in data.itens:
            self._validar_item(item)

        alertas_acionados = 0
        for item in data.itens:
            politica_atual = self._politica_repo.obter_politica(item.sku_id)
            if not politica_atual:
                raise RegraSazonalidadeInvalida(
                    f"Politica de reposicao ausente para SKU: {item.sku_id}"
                )

            cobertura_pre = float(politica_atual.get("cobertura_dias") or 0.0)
            cobertura_bruta = cobertura_pre * item.fator_sazonal

            alertas_item: list[str] = []
            status = "ativo"
            cobertura_final = cobertura_bruta

            baixa_confianca = (
                item.confianca_modelo < data.confianca_minima
                or item.janela_analise_meses < data.janela_minima_meses
            )
            if baixa_confianca:
                status = "baixa_confianca"
                cobertura_final = cobertura_pre
                alertas_item.append("sinal_sazonal_baixa_confianca")
                alertas_item.append("revisao_manual_recomendada")

            if item.mudanca_estrutural:
                status = "baixa_confianca"
                cobertura_final = cobertura_pre
                alertas_item.append("mudanca_estrutural_detectada")
                if "revisao_manual_recomendada" not in alertas_item:
                    alertas_item.append("revisao_manual_recomendada")

            shelf_life = politica_atual.get("shelf_life_dias")
            if shelf_life:
                shelf_limit = max(1.0, float(shelf_life) - data.margem_shelf_life_dias)
                if cobertura_final > shelf_limit:
                    cobertura_final = shelf_limit
                    alertas_item.append("conflito_sazonalidade_vs_shelf_life")

            politica_id = self._politica_repo.salvar_ou_atualizar_politica(
                {
                    "politica_reposicao_id": politica_atual.get("politica_reposicao_id"),
                    "sku_id": item.sku_id,
                    "classe_abc": politica_atual.get("classe_abc"),
                    "cobertura_dias": cobertura_final,
                    "giro_periodo": politica_atual.get("giro_periodo"),
                    "lead_time_dias": politica_atual.get("lead_time_dias"),
                    "fator_sazonal": item.fator_sazonal,
                    "sazonalidade_status": status,
                    "janela_analise_meses": item.janela_analise_meses,
                    "shelf_life_dias": politica_atual.get("shelf_life_dias"),
                    "risco_vencimento": politica_atual.get("risco_vencimento"),
                    "updated_by": data.operador,
                    "correlation_id": data.correlation_id,
                }
            )

            sinal_id = self._sinal_repo.salvar_sinal(
                {
                    "sku_id": item.sku_id,
                    "origem_motor": item.origem_motor,
                    "tipo_sinal": "fator_sazonal",
                    "versao_modelo": item.versao_modelo,
                    "valor_sinal": item.fator_sazonal,
                    "payload": {
                        "confianca_modelo": item.confianca_modelo,
                        "janela_analise_meses": item.janela_analise_meses,
                        "mudanca_estrutural": item.mudanca_estrutural,
                        "cobertura_pre": cobertura_pre,
                        "cobertura_final": cobertura_final,
                        "status": status,
                        "alertas": alertas_item,
                    },
                    "correlation_id": data.correlation_id,
                }
            )

            alertas_acionados += len(alertas_item)
            self._publisher.publish(
                self.EVENT_ITEM,
                {
                    "politica_reposicao_id": politica_id,
                    "sinal_externo_id": sinal_id,
                    "sku_id": item.sku_id,
                    "fator_sazonal": item.fator_sazonal,
                    "sazonalidade_status": status,
                    "cobertura_antes": cobertura_pre,
                    "cobertura_depois": cobertura_final,
                    "alertas": alertas_item,
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
        return ProcessarSazonalidadeOperacionalOutput(
            itens_processados=len(data.itens),
            alertas_acionados=alertas_acionados,
            evento_emitido=self.EVENT_SUMARIO,
        )

    def _validar_item(self, item: ItemSazonalidadeInput) -> None:
        if not self._estoque_repo.validar_sku_ativo(item.sku_id):
            raise SKUInativoOuInexistente(f"SKU invalido ou inativo: {item.sku_id}")
        if item.fator_sazonal <= 0:
            raise RegraSazonalidadeInvalida("fator_sazonal deve ser maior que zero")
        if item.confianca_modelo < 0 or item.confianca_modelo > 1:
            raise RegraSazonalidadeInvalida("confianca_modelo deve estar entre 0 e 1")
        if item.janela_analise_meses <= 0:
            raise QuantidadeInvalida("janela_analise_meses deve ser > 0")
        if not item.origem_motor or not item.origem_motor.strip():
            raise RegraSazonalidadeInvalida("origem_motor e obrigatorio")
