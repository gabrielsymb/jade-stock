"""Repositorio PostgreSQL para inventario ciclico (extended)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4


class PostgresInventarioRepository:
    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def salvar_contagem(self, payload: dict) -> str:
        contagem_id = payload.get("contagem_id") or f"cnt_{uuid4().hex[:10]}"

        sql = """
            INSERT INTO inventario_contagem (
                contagem_id,
                sku_id,
                endereco_codigo,
                quantidade_sistemica,
                quantidade_contada,
                divergencia,
                divergencia_valor,
                snapshot_url,
                actor_id,
                correlation_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            contagem_id,
            payload["sku_id"],
            payload["endereco_codigo"],
            payload["quantidade_sistemica"],
            payload["quantidade_contada"],
            bool(payload.get("divergencia")),
            payload.get("divergencia_valor", 0),
            payload.get("snapshot_url"),
            payload.get("actor_id"),
            payload.get("correlation_id"),
        )

        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)

        return contagem_id
