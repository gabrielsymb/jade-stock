"""Repositorio PostgreSQL para movimentacoes de estoque (core)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4


class PostgresMovimentacaoRepository:
    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def salvar_movimentacao(self, payload: dict) -> str:
        movimentacao_id = payload.get("movimentacao_id") or f"mov_{uuid4().hex[:10]}"
        sku_id = self._resolve_sku_id(payload["sku_id"])
        if not sku_id:
            raise RuntimeError(f"SKU nao encontrado: {payload['sku_id']}")

        sql = """
            INSERT INTO movimentacao_estoque (
                movimentacao_id,
                tipo_movimentacao,
                sku_id,
                quantidade,
                endereco_origem,
                endereco_destino,
                motivo,
                actor_id,
                tenant_id,
                correlation_id,
                schema_version
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            movimentacao_id,
            payload["tipo_movimentacao"],
            sku_id,
            payload["quantidade"],
            payload.get("endereco_origem"),
            payload.get("endereco_destino"),
            payload.get("motivo"),
            payload.get("operador"),
            payload.get("tenant_id"),
            payload.get("correlation_id"),
            payload.get("schema_version", "1.0"),
        )

        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
        return movimentacao_id

    def _resolve_sku_id(self, sku_ref: str) -> str | None:
        sql = """
            SELECT sku_id
            FROM sku
            WHERE sku_id = %s OR sku_codigo = %s
            LIMIT 1
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (sku_ref, sku_ref))
            row = cursor.fetchone()
            return row[0] if row else None
