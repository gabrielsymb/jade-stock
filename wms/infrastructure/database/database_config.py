"""Configuracao basica de conexao de banco (placeholder)."""

from __future__ import annotations

import os
from typing import Any


def get_connection_sqlite() -> Any:
    """Placeholder para eventual conexao SQLite de transicao."""
    raise NotImplementedError("SQLite nao configurado neste projeto no momento")


def get_connection_postgres() -> Any:
    """Retorna conexao PostgreSQL quando psycopg2 estiver disponivel."""
    dsn = os.getenv("WMS_POSTGRES_DSN")
    if not dsn:
        raise RuntimeError("Defina WMS_POSTGRES_DSN para conectar ao PostgreSQL")

    try:
        import psycopg2  # type: ignore
    except ImportError as exc:
        raise RuntimeError("psycopg2 nao instalado. Instale para habilitar conexao PostgreSQL") from exc

    return psycopg2.connect(dsn)
