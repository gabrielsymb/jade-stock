"""Repositorio em memoria para estado de estoque."""

from __future__ import annotations


class InMemoryEstoqueRepository:
    def __init__(self, skus_ativos: set[str] | None = None, enderecos_validos: set[str] | None = None) -> None:
        self.skus_ativos = skus_ativos or set()
        self.enderecos_validos = enderecos_validos or set()
        self.saldos: dict[tuple[str, str], float] = {}

    def validar_sku_ativo(self, sku_id: str) -> bool:
        return sku_id in self.skus_ativos

    def validar_endereco(self, endereco_codigo: str) -> bool:
        return endereco_codigo in self.enderecos_validos

    def validar_saldo(self, sku_id: str, endereco_origem: str | None, quantidade: float) -> bool:
        if not endereco_origem:
            return False
        atual = self.saldos.get((sku_id, endereco_origem), 0.0)
        return atual >= quantidade

    def saldo_atual(self, sku_id: str, endereco_codigo: str) -> float:
        return self.saldos.get((sku_id, endereco_codigo), 0.0)

    def aplicar_movimentacao(self, payload: dict) -> None:
        sku_id = payload["sku_id"]
        tipo = payload["tipo_movimentacao"]
        qtd = payload["quantidade"]
        origem = payload.get("endereco_origem")
        destino = payload.get("endereco_destino")

        if tipo == "entrada":
            self._add(sku_id, destino, qtd)
            return

        if tipo in {"saida", "avaria"}:
            self._sub(sku_id, origem, qtd)
            return

        if tipo == "transferencia":
            self._sub(sku_id, origem, qtd)
            self._add(sku_id, destino, qtd)
            return

        if tipo == "ajuste":
            if destino:
                self._add(sku_id, destino, qtd)
            elif origem:
                self._sub(sku_id, origem, qtd)

    def atualizar_saldo_recebimento(self, payload: dict) -> None:
        for item in payload.get("itens", []):
            sku_codigo = item["sku_codigo"]
            endereco_destino = item["endereco_destino"]
            quantidade_conferida = item["quantidade_conferida"]
            self._add(sku_codigo, endereco_destino, quantidade_conferida)

    def _add(self, sku_id: str, endereco: str | None, qtd: float) -> None:
        if not endereco:
            return
        key = (sku_id, endereco)
        self.saldos[key] = self.saldos.get(key, 0.0) + qtd

    def _sub(self, sku_id: str, endereco: str | None, qtd: float) -> None:
        if not endereco:
            return
        key = (sku_id, endereco)
        self.saldos[key] = self.saldos.get(key, 0.0) - qtd
