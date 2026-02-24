"""Repositorio PostgreSQL para recebimentos (core)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4


class PostgresRecebimentoRepository:
    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def nota_ja_processada(self, nota_fiscal: str, correlation_id: str) -> bool:
        sql = """
            SELECT 1
            FROM recebimento
            WHERE nota_fiscal_numero = %s
              AND correlation_id = %s
            LIMIT 1
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (nota_fiscal, correlation_id))
            return cursor.fetchone() is not None

    def salvar_recebimento(self, payload: dict) -> str:
        recebimento_id = payload.get("recebimento_id") or f"rec_{uuid4().hex[:10]}"

        sql_recebimento = """
            INSERT INTO recebimento (
                recebimento_id,
                nota_fiscal_numero,
                fornecedor_id,
                status_conferencia,
                possui_avaria,
                divergencia_quantidade,
                actor_id,
                tenant_id,
                correlation_id,
                schema_version
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        itens = payload.get("itens", [])
        possui_avaria = any(i.get("classificacao_divergencia") == "avaria" for i in itens)
        divergencia_quantidade = any(bool(i.get("divergencia")) for i in itens)

        params_recebimento = (
            recebimento_id,
            payload["nota_fiscal"],
            payload.get("fornecedor_id"),
            payload.get("status", "conferido"),
            possui_avaria,
            divergencia_quantidade,
            payload.get("operador"),
            payload.get("tenant_id"),
            payload.get("correlation_id"),
            payload.get("schema_version", "1.0"),
        )

        sql_item = """
            INSERT INTO recebimento_item (
                recebimento_item_id,
                recebimento_id,
                sku_id,
                endereco_destino,
                quantidade_esperada,
                quantidade_conferida,
                divergencia,
                classificacao_divergencia,
                correlation_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        with self.connection.cursor() as cursor:
            cursor.execute(sql_recebimento, params_recebimento)

            for item in itens:
                recebimento_item_id = f"rci_{uuid4().hex[:10]}"
                params_item = (
                    recebimento_item_id,
                    recebimento_id,
                    item["sku_codigo"],
                    item["endereco_destino"],
                    item["quantidade_esperada"],
                    item["quantidade_conferida"],
                    bool(item.get("divergencia")),
                    item.get("classificacao_divergencia"),
                    payload.get("correlation_id"),
                )
                cursor.execute(sql_item, params_item)

        return recebimento_id
