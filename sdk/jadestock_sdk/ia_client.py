"""Placeholder do cliente IA para o SDK unificado Jade-stock."""

from __future__ import annotations


class IAClient:
    """Cliente IA sera implementado na fase de ultra processamento."""

    def __init__(self, base_url: str = "http://127.0.0.1:8100") -> None:
        self.base_url = base_url
