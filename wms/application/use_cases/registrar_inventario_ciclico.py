"""Vertical slice: RegistrarInventarioCiclico."""

from dataclasses import dataclass
from typing import Protocol

from wms.domain.exceptions import (
    EnderecoInvalido,
    MotivoObrigatorio,
    QuantidadeInvalida,
    SKUInativoOuInexistente,
)


@dataclass(frozen=True)
class ItemContagemCiclicaInput:
    sku_id: str
    endereco_codigo: str
    quantidade_contada: float


@dataclass(frozen=True)
class RegistrarInventarioCiclicoInput:
    operador: str
    correlation_id: str
    motivo: str
    itens: list[ItemContagemCiclicaInput]


@dataclass(frozen=True)
class RegistrarInventarioCiclicoOutput:
    itens_processados: int
    ajustes_gerados: int
    evento_emitido: str


class MovimentacaoRepository(Protocol):
    def salvar_movimentacao(self, payload: dict) -> str: ...


class EstoqueRepository(Protocol):
    def validar_sku_ativo(self, sku_id: str) -> bool: ...
    def validar_endereco(self, endereco_codigo: str) -> bool: ...
    def saldo_atual(self, sku_id: str, endereco_codigo: str) -> float: ...
    def aplicar_movimentacao(self, payload: dict) -> None: ...


class InventarioRepository(Protocol):
    def salvar_contagem(self, payload: dict) -> str: ...


class EventPublisher(Protocol):
    def publish(self, event_name: str, payload: dict) -> None: ...


class RegistrarInventarioCiclico:
    EVENT_ITEM_AJUSTADO = "inventario_ciclico_ajuste_registrado"
    EVENT_SUMARIO = "inventario_ciclico_processado"

    def __init__(
        self,
        movimentacao_repo: MovimentacaoRepository,
        estoque_repo: EstoqueRepository,
        inventario_repo: InventarioRepository,
        publisher: EventPublisher,
    ) -> None:
        self._movimentacao_repo = movimentacao_repo
        self._estoque_repo = estoque_repo
        self._inventario_repo = inventario_repo
        self._publisher = publisher

    def execute(self, data: RegistrarInventarioCiclicoInput) -> RegistrarInventarioCiclicoOutput:
        self._validar_entrada(data)

        ajustes_gerados = 0
        itens_processados = 0

        for item in data.itens:
            self._validar_item(item)
            itens_processados += 1

            saldo_atual = self._estoque_repo.saldo_atual(item.sku_id, item.endereco_codigo)
            diferenca = item.quantidade_contada - saldo_atual

            self._inventario_repo.salvar_contagem(
                {
                    "sku_id": item.sku_id,
                    "endereco_codigo": item.endereco_codigo,
                    "quantidade_sistemica": saldo_atual,
                    "quantidade_contada": item.quantidade_contada,
                    "divergencia": diferenca != 0,
                    "divergencia_valor": diferenca,
                    "snapshot_url": None,
                    "actor_id": data.operador,
                    "correlation_id": data.correlation_id,
                }
            )

            if diferenca == 0:
                continue

            payload = self._to_movimentacao_payload(item, data, diferenca)
            self._estoque_repo.aplicar_movimentacao(payload)
            movimentacao_id = self._movimentacao_repo.salvar_movimentacao(payload)
            ajustes_gerados += 1

            self._publisher.publish(
                self.EVENT_ITEM_AJUSTADO,
                {
                    "movimentacao_id": movimentacao_id,
                    "sku_id": item.sku_id,
                    "endereco_codigo": item.endereco_codigo,
                    "saldo_antes": saldo_atual,
                    "saldo_contado": item.quantidade_contada,
                    "diferenca": diferenca,
                    "actor_id": data.operador,
                    "correlation_id": data.correlation_id,
                    "motivo": data.motivo,
                },
            )

        self._publisher.publish(
            self.EVENT_SUMARIO,
            {
                "itens_processados": itens_processados,
                "ajustes_gerados": ajustes_gerados,
                "actor_id": data.operador,
                "correlation_id": data.correlation_id,
                "motivo": data.motivo,
            },
        )

        return RegistrarInventarioCiclicoOutput(
            itens_processados=itens_processados,
            ajustes_gerados=ajustes_gerados,
            evento_emitido=self.EVENT_SUMARIO,
        )

    def _validar_entrada(self, data: RegistrarInventarioCiclicoInput) -> None:
        if not data.motivo or not data.motivo.strip():
            raise MotivoObrigatorio("Motivo e obrigatorio para inventario ciclico")
        if not data.itens:
            raise QuantidadeInvalida("Inventario ciclico exige ao menos um item")

    def _validar_item(self, item: ItemContagemCiclicaInput) -> None:
        if item.quantidade_contada < 0:
            raise QuantidadeInvalida("Quantidade contada nao pode ser negativa")
        if not self._estoque_repo.validar_sku_ativo(item.sku_id):
            raise SKUInativoOuInexistente(f"SKU invalido ou inativo: {item.sku_id}")
        if not self._estoque_repo.validar_endereco(item.endereco_codigo):
            raise EnderecoInvalido(f"Endereco invalido: {item.endereco_codigo}")

    def _to_movimentacao_payload(
        self,
        item: ItemContagemCiclicaInput,
        data: RegistrarInventarioCiclicoInput,
        diferenca: float,
    ) -> dict:
        is_positive = diferenca > 0
        quantidade = abs(diferenca)
        return {
            "sku_id": item.sku_id,
            "tipo_movimentacao": "ajuste",
            "quantidade": quantidade,
            "endereco_origem": None if is_positive else item.endereco_codigo,
            "endereco_destino": item.endereco_codigo if is_positive else None,
            "operador": data.operador,
            "correlation_id": data.correlation_id,
            "motivo": data.motivo,
        }
