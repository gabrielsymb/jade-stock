"""Repositorio PostgreSQL para governanca orcamentaria (extended)."""

from __future__ import annotations

from datetime import date
from typing import Any
from uuid import uuid4


class PostgresOrcamentoRepository:
    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def salvar_ou_atualizar_periodo(self, payload: dict) -> str:
        periodo = payload["periodo_referencia"]
        orcamento_periodo_id = (
            payload.get("orcamento_periodo_id")
            or self._buscar_periodo_id(periodo)
            or f"orp_{uuid4().hex[:10]}"
        )
        sql = """
            INSERT INTO orcamento_periodo (
                orcamento_periodo_id,
                periodo_referencia,
                orcamento_total_periodo,
                consumo_orcamento,
                created_by,
                correlation_id
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (periodo_referencia)
            DO UPDATE SET
                orcamento_total_periodo = EXCLUDED.orcamento_total_periodo,
                consumo_orcamento = EXCLUDED.consumo_orcamento,
                updated_at = NOW(),
                created_by = EXCLUDED.created_by,
                correlation_id = EXCLUDED.correlation_id
        """
        params = (
            orcamento_periodo_id,
            periodo,
            payload["orcamento_total_periodo"],
            payload["consumo_orcamento"],
            payload.get("created_by"),
            payload.get("correlation_id"),
        )
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
        return orcamento_periodo_id

    def salvar_ou_atualizar_categoria(self, payload: dict) -> str:
        periodo_id = self._buscar_periodo_id(payload["periodo_referencia"])
        if not periodo_id:
            raise RuntimeError("orcamento_periodo nao encontrado para categoria")

        orcamento_categoria_id = (
            payload.get("orcamento_categoria_id")
            or self._buscar_categoria_id(periodo_id, payload["categoria_id"])
            or f"orc_{uuid4().hex[:10]}"
        )

        sql = """
            INSERT INTO orcamento_categoria (
                orcamento_categoria_id,
                orcamento_periodo_id,
                categoria_id,
                orcamento_categoria_periodo,
                consumo_categoria,
                correlation_id
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (orcamento_periodo_id, categoria_id)
            DO UPDATE SET
                orcamento_categoria_periodo = EXCLUDED.orcamento_categoria_periodo,
                consumo_categoria = EXCLUDED.consumo_categoria,
                updated_at = NOW(),
                correlation_id = EXCLUDED.correlation_id
        """
        params = (
            orcamento_categoria_id,
            periodo_id,
            payload["categoria_id"],
            payload["orcamento_categoria_periodo"],
            payload["consumo_categoria"],
            payload.get("correlation_id"),
        )
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
        return orcamento_categoria_id

    def salvar_aporte_externo(self, payload: dict) -> str:
        periodo_id = self._buscar_periodo_id(payload["periodo_referencia"])
        if not periodo_id:
            raise RuntimeError("orcamento_periodo nao encontrado para aporte")
        aporte_externo_id = payload.get("aporte_externo_id") or f"ape_{uuid4().hex[:10]}"
        sql = """
            INSERT INTO aporte_externo (
                aporte_externo_id,
                orcamento_periodo_id,
                valor,
                origem,
                destino,
                validade_ate,
                aprovado_por,
                observacao,
                correlation_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            aporte_externo_id,
            periodo_id,
            payload["valor"],
            payload["origem"],
            payload.get("destino"),
            payload.get("validade_ate"),
            payload.get("aprovado_por"),
            payload.get("observacao"),
            payload.get("correlation_id"),
        )
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
        return aporte_externo_id

    def salvar_compra_excecao(self, payload: dict) -> str:
        periodo_id = self._buscar_periodo_id(payload["periodo_referencia"])
        if not periodo_id:
            raise RuntimeError("orcamento_periodo nao encontrado para excecao")
        compra_excecao_id = payload.get("compra_excecao_id") or f"exc_{uuid4().hex[:10]}"
        sql = """
            INSERT INTO compra_excecao (
                compra_excecao_id,
                orcamento_periodo_id,
                categoria_id,
                valor_solicitado,
                valor_aprovado,
                motivo,
                aprovado_por,
                status,
                correlation_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        params = (
            compra_excecao_id,
            periodo_id,
            payload.get("categoria_id"),
            payload["valor_solicitado"],
            payload.get("valor_aprovado"),
            payload.get("motivo"),
            payload.get("aprovado_por"),
            payload.get("status"),
            payload.get("correlation_id"),
        )
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
        return compra_excecao_id

    def _buscar_periodo_id(self, periodo_referencia: date) -> str | None:
        sql = """
            SELECT orcamento_periodo_id
            FROM orcamento_periodo
            WHERE periodo_referencia = %s
            LIMIT 1
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (periodo_referencia,))
            row = cursor.fetchone()
            return row[0] if row else None

    def _buscar_categoria_id(self, periodo_id: str, categoria_id: str) -> str | None:
        sql = """
            SELECT orcamento_categoria_id
            FROM orcamento_categoria
            WHERE orcamento_periodo_id = %s AND categoria_id = %s
            LIMIT 1
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (periodo_id, categoria_id))
            row = cursor.fetchone()
            return row[0] if row else None
