"""Vertical slice: RegistrarPoliticaKanban."""

from dataclasses import dataclass
from typing import Protocol

from wms.domain.exceptions import RegraKanbanInvalida, SKUInativoOuInexistente


@dataclass(frozen=True)
class RegistrarPoliticaKanbanInput:
    sku_id: str
    elegivel: bool
    kanban_ativo: bool
    faixa_atual: str
    faixa_verde_min: float
    faixa_amarela_min: float
    faixa_vermelha_min: float
    operador: str
    correlation_id: str
    motivo: str


@dataclass(frozen=True)
class RegistrarPoliticaKanbanOutput:
    kanban_politica_id: str
    faixa_alterada: bool
    evento_emitido: str


class EstoqueRepository(Protocol):
    def validar_sku_ativo(self, sku_id: str) -> bool: ...


class KanbanRepository(Protocol):
    def obter_politica(self, sku_id: str) -> dict | None: ...
    def salvar_ou_atualizar_politica(self, payload: dict) -> str: ...
    def salvar_historico(self, payload: dict) -> str: ...


class EventPublisher(Protocol):
    def publish(self, event_name: str, payload: dict) -> None: ...


class RegistrarPoliticaKanban:
    EVENT_POLITICA = "kanban_politica_atualizada"
    EVENT_FAIXA = "kanban_faixa_atualizada"
    EVENT_REPOSICAO = "kanban_reposicao_disparada"
    FAIXAS_VALIDAS = {"verde", "amarela", "vermelha"}

    def __init__(
        self,
        estoque_repo: EstoqueRepository,
        kanban_repo: KanbanRepository,
        publisher: EventPublisher,
    ) -> None:
        self._estoque_repo = estoque_repo
        self._kanban_repo = kanban_repo
        self._publisher = publisher

    def execute(self, data: RegistrarPoliticaKanbanInput) -> RegistrarPoliticaKanbanOutput:
        self._validar_regras(data)

        politica_anterior = self._kanban_repo.obter_politica(data.sku_id)
        faixa_anterior = politica_anterior["faixa_atual"] if politica_anterior else None
        faixa_alterada = faixa_anterior != data.faixa_atual

        payload = {
            "sku_id": data.sku_id,
            "elegivel": data.elegivel,
            "kanban_ativo": data.kanban_ativo,
            "faixa_atual": data.faixa_atual,
            "faixa_verde_min": data.faixa_verde_min,
            "faixa_amarela_min": data.faixa_amarela_min,
            "faixa_vermelha_min": data.faixa_vermelha_min,
            "updated_by": data.operador,
            "correlation_id": data.correlation_id,
        }
        kanban_politica_id = self._kanban_repo.salvar_ou_atualizar_politica(payload)

        self._publisher.publish(
            self.EVENT_POLITICA,
            {
                "kanban_politica_id": kanban_politica_id,
                "sku_id": data.sku_id,
                "elegivel": data.elegivel,
                "kanban_ativo": data.kanban_ativo,
                "faixa_atual": data.faixa_atual,
                "faixa_verde_min": data.faixa_verde_min,
                "faixa_amarela_min": data.faixa_amarela_min,
                "faixa_vermelha_min": data.faixa_vermelha_min,
                "actor_id": data.operador,
                "correlation_id": data.correlation_id,
            },
        )

        if faixa_alterada:
            self._kanban_repo.salvar_historico(
                {
                    "sku_id": data.sku_id,
                    "faixa_anterior": faixa_anterior,
                    "faixa_nova": data.faixa_atual,
                    "motivo": data.motivo,
                    "actor_id": data.operador,
                    "correlation_id": data.correlation_id,
                }
            )
            self._publisher.publish(
                self.EVENT_FAIXA,
                {
                    "sku_id": data.sku_id,
                    "faixa_anterior": faixa_anterior,
                    "faixa_nova": data.faixa_atual,
                    "motivo": data.motivo,
                    "actor_id": data.operador,
                    "correlation_id": data.correlation_id,
                },
            )

        if data.kanban_ativo and data.faixa_atual in {"amarela", "vermelha"}:
            self._publisher.publish(
                self.EVENT_REPOSICAO,
                {
                    "sku_id": data.sku_id,
                    "faixa_atual": data.faixa_atual,
                    "motivo": data.motivo,
                    "actor_id": data.operador,
                    "correlation_id": data.correlation_id,
                },
            )

        return RegistrarPoliticaKanbanOutput(
            kanban_politica_id=kanban_politica_id,
            faixa_alterada=faixa_alterada,
            evento_emitido=self.EVENT_POLITICA,
        )

    def _validar_regras(self, data: RegistrarPoliticaKanbanInput) -> None:
        if not self._estoque_repo.validar_sku_ativo(data.sku_id):
            raise SKUInativoOuInexistente(f"SKU invalido ou inativo: {data.sku_id}")
        if not data.motivo or not data.motivo.strip():
            raise RegraKanbanInvalida("Motivo e obrigatorio para atualizar politica Kanban")
        if data.faixa_atual not in self.FAIXAS_VALIDAS:
            raise RegraKanbanInvalida(f"Faixa atual invalida: {data.faixa_atual}")
        if not data.elegivel and data.kanban_ativo:
            raise RegraKanbanInvalida("SKU nao elegivel nao pode ter Kanban ativo")
        if (
            data.faixa_verde_min < 0
            or data.faixa_amarela_min < 0
            or data.faixa_vermelha_min < 0
        ):
            raise RegraKanbanInvalida("Faixas Kanban nao podem ser negativas")
        if not (
            data.faixa_verde_min >= data.faixa_amarela_min >= data.faixa_vermelha_min
        ):
            raise RegraKanbanInvalida(
                "Faixas invalidas: esperado verde >= amarela >= vermelha"
            )
