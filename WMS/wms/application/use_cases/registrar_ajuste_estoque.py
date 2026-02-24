"""Vertical slice: RegistrarAjusteEstoque."""

from dataclasses import dataclass
from typing import Protocol

from wms.domain.exceptions import (
    EnderecoInvalido,
    EstoqueInsuficiente,
    MotivoObrigatorio,
    QuantidadeInvalida,
    SKUInativoOuInexistente,
)


@dataclass(frozen=True)
class RegistrarAjusteEstoqueInput:
    sku_id: str
    endereco_codigo: str
    quantidade_ajuste: float
    operador: str
    correlation_id: str
    motivo: str


@dataclass(frozen=True)
class RegistrarAjusteEstoqueOutput:
    movimentacao_id: str
    saldo_atualizado: bool
    evento_emitido: str


class MovimentacaoRepository(Protocol):
    def salvar_movimentacao(self, payload: dict) -> str: ...


class EstoqueRepository(Protocol):
    def validar_sku_ativo(self, sku_id: str) -> bool: ...
    def validar_endereco(self, endereco_codigo: str) -> bool: ...
    def validar_saldo(self, sku_id: str, endereco_origem: str | None, quantidade: float) -> bool: ...
    def aplicar_movimentacao(self, payload: dict) -> None: ...


class EventPublisher(Protocol):
    def publish(self, event_name: str, payload: dict) -> None: ...


class RegistrarAjusteEstoque:
    EVENT_NAME = "ajuste_estoque_registrado"

    def __init__(
        self,
        movimentacao_repo: MovimentacaoRepository,
        estoque_repo: EstoqueRepository,
        publisher: EventPublisher,
    ) -> None:
        self._movimentacao_repo = movimentacao_repo
        self._estoque_repo = estoque_repo
        self._publisher = publisher

    def execute(self, data: RegistrarAjusteEstoqueInput) -> RegistrarAjusteEstoqueOutput:
        self._validar_regras(data)

        payload = self._to_payload(data)
        self._estoque_repo.aplicar_movimentacao(payload)
        movimentacao_id = self._movimentacao_repo.salvar_movimentacao(payload)

        self._publisher.publish(
            self.EVENT_NAME,
            {
                "movimentacao_id": movimentacao_id,
                "sku_id": data.sku_id,
                "tipo_movimentacao": "ajuste",
                "quantidade": payload["quantidade"],
                "endereco_origem": payload["endereco_origem"],
                "endereco_destino": payload["endereco_destino"],
                "actor_id": data.operador,
                "correlation_id": data.correlation_id,
                "motivo": data.motivo,
            },
        )

        return RegistrarAjusteEstoqueOutput(
            movimentacao_id=movimentacao_id,
            saldo_atualizado=True,
            evento_emitido=self.EVENT_NAME,
        )

    def _validar_regras(self, data: RegistrarAjusteEstoqueInput) -> None:
        if data.quantidade_ajuste == 0:
            raise QuantidadeInvalida("Ajuste nao pode ser zero")

        if not data.motivo or not data.motivo.strip():
            raise MotivoObrigatorio("Motivo e obrigatorio para ajuste")

        if not self._estoque_repo.validar_sku_ativo(data.sku_id):
            raise SKUInativoOuInexistente(f"SKU invalido ou inativo: {data.sku_id}")

        if not self._estoque_repo.validar_endereco(data.endereco_codigo):
            raise EnderecoInvalido(f"Endereco invalido: {data.endereco_codigo}")

        if data.quantidade_ajuste < 0:
            if not self._estoque_repo.validar_saldo(
                data.sku_id,
                data.endereco_codigo,
                abs(data.quantidade_ajuste),
            ):
                raise EstoqueInsuficiente("Saldo insuficiente para ajuste negativo")

    def _to_payload(self, data: RegistrarAjusteEstoqueInput) -> dict:
        quantidade_abs = abs(data.quantidade_ajuste)
        is_positive = data.quantidade_ajuste > 0

        return {
            "sku_id": data.sku_id,
            "tipo_movimentacao": "ajuste",
            "quantidade": quantidade_abs,
            "endereco_origem": None if is_positive else data.endereco_codigo,
            "endereco_destino": data.endereco_codigo if is_positive else None,
            "operador": data.operador,
            "correlation_id": data.correlation_id,
            "motivo": data.motivo,
        }
