"""Repositorio em memoria para sinais externos."""

from __future__ import annotations

from uuid import uuid4


class InMemorySinalExternoRepository:
    def __init__(self) -> None:
        self.sinais: list[dict] = []

    def salvar_sinal(self, payload: dict) -> str:
        sinal_id = payload.get("sinal_externo_id") or f"sxn_{uuid4().hex[:10]}"
        self.sinais.append({"sinal_externo_id": sinal_id, **payload})
        return sinal_id
