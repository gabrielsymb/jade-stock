"""Repositorio PostgreSQL para politica Kanban (extended)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4


class PostgresKanbanRepository:
    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def obter_politica(self, sku_id: str) -> dict | None:
        sql = """
            SELECT
                kanban_politica_id,
                sku_id,
                elegivel,
                kanban_ativo,
                faixa_atual,
                faixa_verde_min,
                faixa_amarela_min,
                faixa_vermelha_min
            FROM kanban_politica
            WHERE sku_id = %s
            LIMIT 1
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (sku_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "kanban_politica_id": row[0],
                "sku_id": row[1],
                "elegivel": bool(row[2]),
                "kanban_ativo": bool(row[3]),
                "faixa_atual": row[4],
                "faixa_verde_min": float(row[5]) if row[5] is not None else None,
                "faixa_amarela_min": float(row[6]) if row[6] is not None else None,
                "faixa_vermelha_min": float(row[7]) if row[7] is not None else None,
            }

    def salvar_ou_atualizar_politica(self, payload: dict) -> str:
        existing = self.obter_politica(payload["sku_id"])
        kanban_politica_id = (
            payload.get("kanban_politica_id")
            or (existing or {}).get("kanban_politica_id")
            or f"kbp_{uuid4().hex[:10]}"
        )
        sql = """
            INSERT INTO kanban_politica (
                kanban_politica_id,
                sku_id,
                elegivel,
                kanban_ativo,
                faixa_atual,
                faixa_verde_min,
                faixa_amarela_min,
                faixa_vermelha_min,
                updated_by,
                correlation_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (sku_id)
            DO UPDATE SET
                elegivel = EXCLUDED.elegivel,
                kanban_ativo = EXCLUDED.kanban_ativo,
                faixa_atual = EXCLUDED.faixa_atual,
                faixa_verde_min = EXCLUDED.faixa_verde_min,
                faixa_amarela_min = EXCLUDED.faixa_amarela_min,
                faixa_vermelha_min = EXCLUDED.faixa_vermelha_min,
                updated_at = NOW(),
                updated_by = EXCLUDED.updated_by,
                correlation_id = EXCLUDED.correlation_id
        """
        params = (
            kanban_politica_id,
            payload["sku_id"],
            bool(payload["elegivel"]),
            bool(payload["kanban_ativo"]),
            payload["faixa_atual"],
            payload["faixa_verde_min"],
            payload["faixa_amarela_min"],
            payload["faixa_vermelha_min"],
            payload.get("updated_by"),
            payload.get("correlation_id"),
        )
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
        return kanban_politica_id

    def salvar_historico(self, payload: dict) -> str:
        kanban_historico_id = payload.get("kanban_historico_id") or f"kbh_{uuid4().hex[:10]}"
        sql = """
            INSERT INTO kanban_historico (
                kanban_historico_id,
                sku_id,
                faixa_anterior,
                faixa_nova,
                motivo,
                actor_id,
                correlation_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            kanban_historico_id,
            payload["sku_id"],
            payload.get("faixa_anterior"),
            payload["faixa_nova"],
            payload.get("motivo"),
            payload.get("actor_id"),
            payload.get("correlation_id"),
        )
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
        return kanban_historico_id
