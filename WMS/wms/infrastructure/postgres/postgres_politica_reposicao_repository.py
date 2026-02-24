"""Repositorio PostgreSQL para politica de reposicao (extended)."""

from __future__ import annotations

from typing import Any
from uuid import uuid4


class PostgresPoliticaReposicaoRepository:
    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def obter_politica(self, sku_id: str) -> dict | None:
        sql = """
            SELECT
                politica_reposicao_id,
                sku_id,
                classe_abc,
                cobertura_dias,
                giro_periodo,
                lead_time_dias,
                fator_sazonal,
                sazonalidade_status,
                janela_analise_meses,
                shelf_life_dias,
                risco_vencimento
            FROM politica_reposicao
            WHERE sku_id = %s
            LIMIT 1
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (sku_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return {
                "politica_reposicao_id": row[0],
                "sku_id": row[1],
                "classe_abc": row[2],
                "cobertura_dias": float(row[3]) if row[3] is not None else None,
                "giro_periodo": float(row[4]) if row[4] is not None else None,
                "lead_time_dias": float(row[5]) if row[5] is not None else None,
                "fator_sazonal": float(row[6]) if row[6] is not None else None,
                "sazonalidade_status": row[7],
                "janela_analise_meses": int(row[8]) if row[8] is not None else None,
                "shelf_life_dias": int(row[9]) if row[9] is not None else None,
                "risco_vencimento": row[10],
            }

    def salvar_ou_atualizar_politica(self, payload: dict) -> str:
        politica_reposicao_id = payload.get("politica_reposicao_id") or self._buscar_id(payload["sku_id"]) or f"prp_{uuid4().hex[:10]}"
        sql = """
            INSERT INTO politica_reposicao (
                politica_reposicao_id,
                sku_id,
                classe_abc,
                cobertura_dias,
                giro_periodo,
                lead_time_dias,
                fator_sazonal,
                sazonalidade_status,
                janela_analise_meses,
                shelf_life_dias,
                risco_vencimento,
                updated_by,
                correlation_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (sku_id)
            DO UPDATE SET
                classe_abc = EXCLUDED.classe_abc,
                cobertura_dias = EXCLUDED.cobertura_dias,
                giro_periodo = EXCLUDED.giro_periodo,
                lead_time_dias = EXCLUDED.lead_time_dias,
                fator_sazonal = EXCLUDED.fator_sazonal,
                sazonalidade_status = EXCLUDED.sazonalidade_status,
                janela_analise_meses = EXCLUDED.janela_analise_meses,
                shelf_life_dias = EXCLUDED.shelf_life_dias,
                risco_vencimento = EXCLUDED.risco_vencimento,
                updated_at = NOW(),
                updated_by = EXCLUDED.updated_by,
                correlation_id = EXCLUDED.correlation_id
        """
        params = (
            politica_reposicao_id,
            payload["sku_id"],
            payload.get("classe_abc"),
            payload.get("cobertura_dias"),
            payload.get("giro_periodo"),
            payload.get("lead_time_dias"),
            payload.get("fator_sazonal"),
            payload.get("sazonalidade_status"),
            payload.get("janela_analise_meses"),
            payload.get("shelf_life_dias"),
            payload.get("risco_vencimento"),
            payload.get("updated_by"),
            payload.get("correlation_id"),
        )
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
        return politica_reposicao_id

    def _buscar_id(self, sku_id: str) -> str | None:
        sql = """
            SELECT politica_reposicao_id
            FROM politica_reposicao
            WHERE sku_id = %s
            LIMIT 1
        """
        with self.connection.cursor() as cursor:
            cursor.execute(sql, (sku_id,))
            row = cursor.fetchone()
            return row[0] if row else None
