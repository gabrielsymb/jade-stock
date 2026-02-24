"""Repositorio em memoria para politica de reposicao (ABCD)."""

from __future__ import annotations

from uuid import uuid4


class InMemoryPoliticaReposicaoRepository:
    def __init__(self) -> None:
        self.politicas: dict[str, dict] = {}

    def obter_politica(self, sku_id: str) -> dict | None:
        return self.politicas.get(sku_id)

    def salvar_ou_atualizar_politica(self, payload: dict) -> str:
        current = self.politicas.get(payload["sku_id"])
        politica_reposicao_id = (
            payload.get("politica_reposicao_id")
            or (current or {}).get("politica_reposicao_id")
            or f"prp_{uuid4().hex[:10]}"
        )
        self.politicas[payload["sku_id"]] = {
            "politica_reposicao_id": politica_reposicao_id,
            **payload,
        }
        return politica_reposicao_id
