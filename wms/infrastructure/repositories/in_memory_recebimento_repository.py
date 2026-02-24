"""Repositorio em memoria para recebimentos."""

from __future__ import annotations

from uuid import uuid4


class InMemoryRecebimentoRepository:
    def __init__(self) -> None:
        self.recebimentos: list[dict] = []

    def nota_ja_processada(self, nota_fiscal: str, correlation_id: str) -> bool:
        for row in self.recebimentos:
            if row["nota_fiscal"] == nota_fiscal and row["correlation_id"] == correlation_id:
                return True
        return False

    def salvar_recebimento(self, payload: dict) -> str:
        recebimento_id = f"rec_{uuid4().hex[:10]}"
        row = {"recebimento_id": recebimento_id, **payload}
        self.recebimentos.append(row)
        return recebimento_id
