"""Repositorio PostgreSQL para sinais externos (extended)."""

from __future__ import annotations

import json
from typing import Any
from uuid import uuid4


class PostgresSinalExternoRepository:
    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def salvar_sinal(self, payload: dict) -> str:
        sinal_externo_id = payload.get("sinal_externo_id") or f"sxn_{uuid4().hex[:10]}"
        sql = """
            INSERT INTO sinal_externo (
                sinal_externo_id,
                sku_id,
                origem_motor,
                tipo_sinal,
                versao_modelo,
                valor_sinal,
                payload,
                validade_ate,
                correlation_id
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
        """
        params = (
            sinal_externo_id,
            payload.get("sku_id"),
            payload.get("origem_motor"),
            payload.get("tipo_sinal"),
            payload.get("versao_modelo"),
            payload.get("valor_sinal"),
            json.dumps(payload.get("payload", {}), ensure_ascii=True),
            payload.get("validade_ate"),
            payload.get("correlation_id"),
        )
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)
        return sinal_externo_id
