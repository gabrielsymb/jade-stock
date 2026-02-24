"""Repositorio em memoria para movimentacoes."""

from __future__ import annotations

from uuid import uuid4


class InMemoryMovimentacaoRepository:
    def __init__(self) -> None:
        self.movimentacoes: list[dict] = []

    def salvar_movimentacao(self, payload: dict) -> str:
        movimentacao_id = f"mov_{uuid4().hex[:10]}"
        row = {"movimentacao_id": movimentacao_id, **payload}
        self.movimentacoes.append(row)
        return movimentacao_id
