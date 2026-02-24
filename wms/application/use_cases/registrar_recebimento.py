"""Contrato de aplicacao para o caso de uso RegistrarRecebimento."""

from dataclasses import dataclass
from typing import Protocol

from wms.domain.exceptions import (
    DivergenciaNaoClassificada,
    EnderecoInvalido,
    NotaFiscalDuplicada,
    QuantidadeInvalida,
    SKUInativoOuInexistente,
)


@dataclass(frozen=True)
class ItemRecebimentoInput:
    sku_codigo: str
    quantidade_esperada: float
    quantidade_conferida: float
    endereco_destino: str
    classificacao_divergencia: str | None = None


@dataclass(frozen=True)
class RegistrarRecebimentoInput:
    nota_fiscal: str
    fornecedor_id: str
    itens: list[ItemRecebimentoInput]
    operador: str
    correlation_id: str


@dataclass(frozen=True)
class RegistrarRecebimentoOutput:
    recebimento_id: str
    status: str
    itens_processados: int
    itens_com_divergencia: int
    eventos_emitidos: list[str]


class RecebimentoRepository(Protocol):
    def nota_ja_processada(self, nota_fiscal: str, correlation_id: str) -> bool: ...
    def salvar_recebimento(self, payload: dict) -> str: ...


class EstoqueRepository(Protocol):
    def validar_sku_ativo(self, sku_id: str) -> bool: ...
    def validar_endereco(self, endereco_codigo: str) -> bool: ...
    def atualizar_saldo_recebimento(self, payload: dict) -> None: ...


class EventPublisher(Protocol):
    def publish(self, event_name: str, payload: dict) -> None: ...


class RegistrarRecebimento:
    EVENT_CONFERIDO = "recebimento_conferido"
    EVENT_DIVERGENTE = "recebimento_divergente"
    CLASSIFICACOES_DIVERGENCIA = {"falta", "sobra", "avaria"}

    def __init__(
        self,
        recebimento_repo: RecebimentoRepository,
        estoque_repo: EstoqueRepository,
        publisher: EventPublisher,
    ) -> None:
        self._recebimento_repo = recebimento_repo
        self._estoque_repo = estoque_repo
        self._publisher = publisher

    def execute(self, data: RegistrarRecebimentoInput) -> RegistrarRecebimentoOutput:
        if self._recebimento_repo.nota_ja_processada(data.nota_fiscal, data.correlation_id):
            raise NotaFiscalDuplicada(
                f"Nota fiscal ja processada: {data.nota_fiscal}/{data.correlation_id}"
            )

        itens_payload: list[dict] = []
        itens_com_divergencia = 0

        for item in data.itens:
            self._validar_item(item)
            divergiu = item.quantidade_esperada != item.quantidade_conferida

            if divergiu:
                itens_com_divergencia += 1
                self._validar_divergencia(item)

            itens_payload.append(
                {
                    "sku_codigo": item.sku_codigo,
                    "quantidade_esperada": item.quantidade_esperada,
                    "quantidade_conferida": item.quantidade_conferida,
                    "endereco_destino": item.endereco_destino,
                    "divergencia": divergiu,
                    "classificacao_divergencia": item.classificacao_divergencia,
                }
            )

        status = "conferido_com_divergencia" if itens_com_divergencia > 0 else "conferido"

        recebimento_payload = {
            "nota_fiscal": data.nota_fiscal,
            "fornecedor_id": data.fornecedor_id,
            "itens": itens_payload,
            "operador": data.operador,
            "correlation_id": data.correlation_id,
            "status": status,
        }

        self._estoque_repo.atualizar_saldo_recebimento(recebimento_payload)
        recebimento_id = self._recebimento_repo.salvar_recebimento(recebimento_payload)

        eventos_emitidos = [self.EVENT_CONFERIDO]
        self._publisher.publish(
            self.EVENT_CONFERIDO,
            {
                "recebimento_id": recebimento_id,
                "nota_fiscal": data.nota_fiscal,
                "itens_processados": len(data.itens),
                "itens_com_divergencia": itens_com_divergencia,
                "actor_id": data.operador,
                "correlation_id": data.correlation_id,
            },
        )

        if itens_com_divergencia > 0:
            eventos_emitidos.append(self.EVENT_DIVERGENTE)
            self._publisher.publish(
                self.EVENT_DIVERGENTE,
                {
                    "recebimento_id": recebimento_id,
                    "nota_fiscal": data.nota_fiscal,
                    "itens_com_divergencia": itens_com_divergencia,
                    "actor_id": data.operador,
                    "correlation_id": data.correlation_id,
                },
            )

        return RegistrarRecebimentoOutput(
            recebimento_id=recebimento_id,
            status=status,
            itens_processados=len(data.itens),
            itens_com_divergencia=itens_com_divergencia,
            eventos_emitidos=eventos_emitidos,
        )

    def _validar_item(self, item: ItemRecebimentoInput) -> None:
        if item.quantidade_esperada < 0 or item.quantidade_conferida < 0:
            raise QuantidadeInvalida("Quantidades nao podem ser negativas")
        if not self._estoque_repo.validar_sku_ativo(item.sku_codigo):
            raise SKUInativoOuInexistente(f"SKU invalido ou inativo: {item.sku_codigo}")
        if not self._estoque_repo.validar_endereco(item.endereco_destino):
            raise EnderecoInvalido(f"Endereco invalido: {item.endereco_destino}")

    def _validar_divergencia(self, item: ItemRecebimentoInput) -> None:
        if not item.classificacao_divergencia:
            raise DivergenciaNaoClassificada(
                f"Divergencia sem classificacao para SKU: {item.sku_codigo}"
            )
        if item.classificacao_divergencia not in self.CLASSIFICACOES_DIVERGENCIA:
            raise DivergenciaNaoClassificada(
                f"Classificacao invalida: {item.classificacao_divergencia}"
            )
