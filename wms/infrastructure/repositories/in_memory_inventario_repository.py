"""Repositorio em memoria para inventario ciclico."""

from __future__ import annotations

from uuid import uuid4


class InMemoryInventarioRepository:
    def __init__(self) -> None:
        self.contagens: list[dict] = []

    def salvar_contagem(self, payload: dict) -> str:
        contagem_id = payload.get("contagem_id") or f"cnt_{uuid4().hex[:10]}"
        row = {"contagem_id": contagem_id, **payload}
        self.contagens.append(row)
        return contagem_id
