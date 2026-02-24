"""Repositorio em memoria para politica Kanban."""

from __future__ import annotations

from uuid import uuid4


class InMemoryKanbanRepository:
    def __init__(self) -> None:
        self.politicas: dict[str, dict] = {}
        self.historicos: list[dict] = []

    def obter_politica(self, sku_id: str) -> dict | None:
        return self.politicas.get(sku_id)

    def salvar_ou_atualizar_politica(self, payload: dict) -> str:
        current = self.politicas.get(payload["sku_id"])
        kanban_politica_id = (
            payload.get("kanban_politica_id")
            or (current or {}).get("kanban_politica_id")
            or f"kbp_{uuid4().hex[:10]}"
        )
        self.politicas[payload["sku_id"]] = {"kanban_politica_id": kanban_politica_id, **payload}
        return kanban_politica_id

    def salvar_historico(self, payload: dict) -> str:
        kanban_historico_id = payload.get("kanban_historico_id") or f"kbh_{uuid4().hex[:10]}"
        self.historicos.append({"kanban_historico_id": kanban_historico_id, **payload})
        return kanban_historico_id
