"""Repositorio PostgreSQL para estoque (core)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4


class PostgresEstoqueRepository:
    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def validar_sku_ativo(self, sku_id: str) -> bool:
        sql = """
            SELECT 1
            FROM sku
            WHERE status_ativo = TRUE
              AND (sku_id = %s OR sku_codigo = %s)
            LIMIT 1
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (sku_id, sku_id))
            return cursor.fetchone() is not None

    def validar_endereco(self, endereco_codigo: str) -> bool:
        sql = """
            SELECT 1
            FROM endereco
            WHERE endereco_codigo = %s
              AND ativo = TRUE
            LIMIT 1
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (endereco_codigo,))
            return cursor.fetchone() is not None

    def validar_saldo(self, sku_id: str, endereco_origem: str | None, quantidade: float) -> bool:
        if not endereco_origem:
            return False
        sku_ref = self._resolve_sku_id(sku_id)
        if not sku_ref:
            return False

        sql = """
            SELECT COALESCE(saldo_disponivel, 0)
            FROM saldo_estoque
            WHERE sku_id = %s
              AND endereco_codigo = %s
            FOR UPDATE
            LIMIT 1
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (sku_ref, endereco_origem))
            row = cursor.fetchone()
            atual = float(row[0]) if row else 0.0
            return atual >= quantidade

    def saldo_atual(self, sku_id: str, endereco_codigo: str) -> float:
        sku_ref = self._resolve_sku_id(sku_id)
        if not sku_ref:
            return 0.0
        sql = """
            SELECT COALESCE(saldo_disponivel, 0)
            FROM saldo_estoque
            WHERE sku_id = %s
              AND endereco_codigo = %s
            LIMIT 1
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (sku_ref, endereco_codigo))
            row = cursor.fetchone()
            return float(row[0]) if row else 0.0

    def aplicar_movimentacao(self, payload: dict) -> None:
        sku_ref = self._resolve_sku_id(payload["sku_id"])
        if not sku_ref:
            raise RuntimeError(f"SKU nao encontrado: {payload['sku_id']}")

        tipo = payload["tipo_movimentacao"]
        qtd = float(payload["quantidade"])
        origem = payload.get("endereco_origem")
        destino = payload.get("endereco_destino")
        corr = payload.get("correlation_id")

        if tipo == "entrada":
            self._upsert_add(sku_ref, destino, qtd, corr)
        elif tipo in {"saida", "avaria"}:
            self._upsert_sub(sku_ref, origem, qtd, corr)
        elif tipo == "transferencia":
            self._upsert_sub(sku_ref, origem, qtd, corr)
            self._upsert_add(sku_ref, destino, qtd, corr)
        elif tipo == "ajuste":
            if destino:
                self._upsert_add(sku_ref, destino, qtd, corr)
            elif origem:
                self._upsert_sub(sku_ref, origem, qtd, corr)

    def atualizar_saldo_recebimento(self, payload: dict) -> None:
        corr = payload.get("correlation_id")
        for item in payload.get("itens", []):
            sku_ref = self._resolve_sku_id(item["sku_codigo"])
            if not sku_ref:
                raise RuntimeError(f"SKU nao encontrado: {item['sku_codigo']}")
            self._upsert_add(
                sku_ref,
                item["endereco_destino"],
                float(item["quantidade_conferida"]),
                corr,
            )
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

    def _upsert_add(self, sku_id: str, endereco_codigo: str | None, qtd: float, corr: str | None) -> None:
        if not endereco_codigo:
            return
        sql = """
            INSERT INTO saldo_estoque (
                saldo_estoque_id,
                sku_id,
                endereco_codigo,
                saldo_disponivel,
                saldo_avariado,
                saldo_bloqueado,
                saldo_total,
                correlation_id
            )
            VALUES (%s, %s, %s, %s, 0, 0, %s, %s)
            ON CONFLICT (sku_id, endereco_codigo)
            DO UPDATE SET
                saldo_disponivel = saldo_estoque.saldo_disponivel + EXCLUDED.saldo_disponivel,
                saldo_total = saldo_estoque.saldo_total + EXCLUDED.saldo_total,
                updated_at = NOW(),
                correlation_id = EXCLUDED.correlation_id
        """
        params = (f"sld_{uuid4().hex[:10]}", sku_id, endereco_codigo, qtd, qtd, corr)
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)

    def _upsert_sub(self, sku_id: str, endereco_codigo: str | None, qtd: float, corr: str | None) -> None:
        if not endereco_codigo:
            return
        sql_insert_if_missing = """
            INSERT INTO saldo_estoque (
                saldo_estoque_id,
                sku_id,
                endereco_codigo,
                saldo_disponivel,
                saldo_avariado,
                saldo_bloqueado,
                saldo_total,
                correlation_id
            )
            VALUES (%s, %s, %s, 0, 0, 0, 0, %s)
            ON CONFLICT (sku_id, endereco_codigo) DO NOTHING
        """
        sql_sub = """
            UPDATE saldo_estoque
            SET
                saldo_disponivel = saldo_disponivel - %s,
                saldo_total = saldo_total - %s,
                updated_at = NOW(),
                correlation_id = %s
            WHERE sku_id = %s
              AND endereco_codigo = %s
              AND saldo_disponivel >= %s
            RETURNING saldo_estoque_id
        """
        params_insert = (f"sld_{uuid4().hex[:10]}", sku_id, endereco_codigo, corr)
        params_sub = (qtd, qtd, corr, sku_id, endereco_codigo, qtd)
        with self.connection.cursor() as cursor:
            cursor.execute(sql_insert_if_missing, params_insert)
            cursor.execute(sql_sub, params_sub)
            if cursor.fetchone() is None:
                raise RuntimeError(
                    f"Saldo insuficiente para debito atomico: sku={sku_id}, endereco={endereco_codigo}"
                )
