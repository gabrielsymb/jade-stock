"""Placeholder do cliente Contabil para o SDK unificado Jade-stock."""

from __future__ import annotations


class ContabilClient:
    """Cliente contabil sera implementado na fase de eventos contabeis."""

    def __init__(self, base_url: str = "http://127.0.0.1:8200") -> None:
        self.base_url = base_url
