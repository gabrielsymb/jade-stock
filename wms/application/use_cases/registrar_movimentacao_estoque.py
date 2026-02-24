"""Primeiro vertical slice recomendado: RegistrarMovimentacaoEstoque."""

from dataclasses import dataclass
from typing import Protocol

from wms.domain.exceptions import (
    EnderecoInvalido,
    EstoqueInsuficiente,
    QuantidadeInvalida,
    SKUInativoOuInexistente,
    TipoMovimentacaoInvalido,
)


@dataclass(frozen=True)
class RegistrarMovimentacaoEstoqueInput:
    sku_id: str
    tipo_movimentacao: str
    quantidade: float
    endereco_origem: str | None
    endereco_destino: str | None
    operador: str
    correlation_id: str
    motivo: str | None = None


@dataclass(frozen=True)
class RegistrarMovimentacaoEstoqueOutput:
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


class RegistrarMovimentacaoEstoque:
    """Vertical slice completo: valida, persiste, atualiza saldo e emite evento."""

    EVENT_NAME = "movimentacao_estoque_registrada"
    TIPOS_VALIDOS = {"entrada", "saida", "transferencia", "ajuste", "avaria"}

    def __init__(
        self,
        movimentacao_repo: MovimentacaoRepository,
        estoque_repo: EstoqueRepository,
        publisher: EventPublisher,
    ) -> None:
        self._movimentacao_repo = movimentacao_repo
        self._estoque_repo = estoque_repo
        self._publisher = publisher

    def execute(self, data: RegistrarMovimentacaoEstoqueInput) -> RegistrarMovimentacaoEstoqueOutput:
        self._validar_regras(data)

        payload = {
            "sku_id": data.sku_id,
            "tipo_movimentacao": data.tipo_movimentacao,
            "quantidade": data.quantidade,
            "endereco_origem": data.endereco_origem,
            "endereco_destino": data.endereco_destino,
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
                "tipo_movimentacao": data.tipo_movimentacao,
                "quantidade": data.quantidade,
                "endereco_origem": data.endereco_origem,
                "endereco_destino": data.endereco_destino,
                "actor_id": data.operador,
                "correlation_id": data.correlation_id,
            },
        )

        return RegistrarMovimentacaoEstoqueOutput(
            movimentacao_id=movimentacao_id,
            saldo_atualizado=True,
            evento_emitido=self.EVENT_NAME,
        )

    def _validar_regras(self, data: RegistrarMovimentacaoEstoqueInput) -> None:
        if data.quantidade <= 0:
            raise QuantidadeInvalida("Quantidade deve ser maior que zero")

        if data.tipo_movimentacao not in self.TIPOS_VALIDOS:
            raise TipoMovimentacaoInvalido(
                f"Tipo de movimentacao invalido: {data.tipo_movimentacao}"
            )

        if not self._estoque_repo.validar_sku_ativo(data.sku_id):
            raise SKUInativoOuInexistente(f"SKU invalido ou inativo: {data.sku_id}")

        if data.endereco_origem and not self._estoque_repo.validar_endereco(data.endereco_origem):
            raise EnderecoInvalido(f"Endereco de origem invalido: {data.endereco_origem}")

        if data.endereco_destino and not self._estoque_repo.validar_endereco(data.endereco_destino):
            raise EnderecoInvalido(f"Endereco de destino invalido: {data.endereco_destino}")

        if data.tipo_movimentacao in {"saida", "transferencia", "avaria"}:
            if not data.endereco_origem:
                raise EnderecoInvalido("Tipo exige endereco de origem")
            if not self._estoque_repo.validar_saldo(
                data.sku_id, data.endereco_origem, data.quantidade
            ):
                raise EstoqueInsuficiente("Saldo insuficiente na origem")

        if data.tipo_movimentacao in {"entrada", "transferencia"} and not data.endereco_destino:
            raise EnderecoInvalido("Tipo exige endereco de destino")
