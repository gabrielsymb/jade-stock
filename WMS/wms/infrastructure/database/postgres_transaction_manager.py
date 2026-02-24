"""Controle explicito de transacao para adapters PostgreSQL."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any


@contextmanager
def postgres_transaction(connection: Any):
    """Executa um bloco com BEGIN/COMMIT/ROLLBACK explicitos."""
    previous_autocommit = bool(connection.autocommit)
    connection.autocommit = False
    try:
        yield
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.autocommit = previous_autocommit
