"""Utilitarios internos da SDK Jade-stock."""

from __future__ import annotations

import uuid


def new_correlation_id(prefix: str = "corr_sdk") -> str:
    """Gera correlation_id curto e unico para comandos idempotentes."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"
