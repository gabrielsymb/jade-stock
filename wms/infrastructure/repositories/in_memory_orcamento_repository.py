"""Repositorio em memoria para governanca orcamentaria."""

from __future__ import annotations

from datetime import date
from uuid import uuid4


class InMemoryOrcamentoRepository:
    def __init__(self) -> None:
        self.periodos: dict[date, dict] = {}
        self.categorias: dict[tuple[date, str], dict] = {}
        self.aportes: list[dict] = []
        self.excecoes: list[dict] = []

    def salvar_ou_atualizar_periodo(self, payload: dict) -> str:
        periodo = payload["periodo_referencia"]
        current = self.periodos.get(periodo)
        orcamento_periodo_id = (
            payload.get("orcamento_periodo_id")
            or (current or {}).get("orcamento_periodo_id")
            or f"orp_{uuid4().hex[:10]}"
        )
        self.periodos[periodo] = {"orcamento_periodo_id": orcamento_periodo_id, **payload}
        return orcamento_periodo_id

    def salvar_ou_atualizar_categoria(self, payload: dict) -> str:
        key = (payload["periodo_referencia"], payload["categoria_id"])
        current = self.categorias.get(key)
        orcamento_categoria_id = (
            payload.get("orcamento_categoria_id")
            or (current or {}).get("orcamento_categoria_id")
            or f"orc_{uuid4().hex[:10]}"
        )
        self.categorias[key] = {"orcamento_categoria_id": orcamento_categoria_id, **payload}
        return orcamento_categoria_id

    def salvar_aporte_externo(self, payload: dict) -> str:
        aporte_externo_id = payload.get("aporte_externo_id") or f"ape_{uuid4().hex[:10]}"
        self.aportes.append({"aporte_externo_id": aporte_externo_id, **payload})
        return aporte_externo_id

    def salvar_compra_excecao(self, payload: dict) -> str:
        compra_excecao_id = payload.get("compra_excecao_id") or f"exc_{uuid4().hex[:10]}"
        self.excecoes.append({"compra_excecao_id": compra_excecao_id, **payload})
        return compra_excecao_id
