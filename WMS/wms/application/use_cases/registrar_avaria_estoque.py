"""Vertical slice: RegistrarAvariaEstoque."""

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
class RegistrarAvariaEstoqueInput:
    sku_id: str
    endereco_codigo: str
    quantidade_avaria: float
    operador: str
    correlation_id: str
    motivo: str


@dataclass(frozen=True)
class RegistrarAvariaEstoqueOutput:
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


class RegistrarAvariaEstoque:
    EVENT_NAME = "avaria_estoque_registrada"

    def __init__(
        self,
        movimentacao_repo: MovimentacaoRepository,
        estoque_repo: EstoqueRepository,
        publisher: EventPublisher,
    ) -> None:
        self._movimentacao_repo = movimentacao_repo
        self._estoque_repo = estoque_repo
        self._publisher = publisher

    def execute(self, data: RegistrarAvariaEstoqueInput) -> RegistrarAvariaEstoqueOutput:
        self._validar_regras(data)

        payload = {
            "sku_id": data.sku_id,
            "tipo_movimentacao": "avaria",
            "quantidade": data.quantidade_avaria,
            "endereco_origem": data.endereco_codigo,
            "endereco_destino": None,
            "operador": data.operador,
            "correlation_id": data.correlation_id,
            "motivo": data.motivo,
        }

        self._estoque_repo.aplicar_movimentacao(payload)
        movimentacao_id = self._movimentacao_repo.salvar_movimentacao(payload)

        self._publisher.publish(
            self.EVENT_NAME,
            {
                "movimentacao_id": movimentacao_id,
                "sku_id": data.sku_id,
                "tipo_movimentacao": "avaria",
                "quantidade": data.quantidade_avaria,
                "endereco_origem": data.endereco_codigo,
                "endereco_destino": None,
                "actor_id": data.operador,
                "correlation_id": data.correlation_id,
                "motivo": data.motivo,
            },
        )

        return RegistrarAvariaEstoqueOutput(
            movimentacao_id=movimentacao_id,
            saldo_atualizado=True,
            evento_emitido=self.EVENT_NAME,
        )

    def _validar_regras(self, data: RegistrarAvariaEstoqueInput) -> None:
        if data.quantidade_avaria <= 0:
            raise QuantidadeInvalida("Quantidade de avaria deve ser maior que zero")

        if not data.motivo or not data.motivo.strip():
            raise MotivoObrigatorio("Motivo e obrigatorio para avaria")

        if not self._estoque_repo.validar_sku_ativo(data.sku_id):
            raise SKUInativoOuInexistente(f"SKU invalido ou inativo: {data.sku_id}")

        if not self._estoque_repo.validar_endereco(data.endereco_codigo):
            raise EnderecoInvalido(f"Endereco invalido: {data.endereco_codigo}")

        if not self._estoque_repo.validar_saldo(
            data.sku_id,
            data.endereco_codigo,
            data.quantidade_avaria,
        ):
            raise EstoqueInsuficiente("Saldo insuficiente para registrar avaria")
