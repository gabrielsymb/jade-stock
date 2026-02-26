"""Cliente HTTP para a API Jade-stock com foco em integracao simples."""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from .utils import new_correlation_id


def _parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class JadeStockSDKError(Exception):
    status_code: int
    code: str
    message: str
    details: dict | list | None = None
    correlation_id: str | None = None

    def __str__(self) -> str:
        return f"{self.status_code} {self.code}: {self.message}"


class JadeStockClient:
    """Cliente para o núcleo WMS e trilhas dedicadas (ex: XML)."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout_seconds: float = 10.0,
        bearer_token: str | None = None,
        retries: int = 0,
        retry_backoff_seconds: float = 0.2,
        auto_correlation_id: bool = False,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._bearer_token = bearer_token
        self._retries = max(0, int(retries))
        self._retry_backoff_seconds = max(0.0, float(retry_backoff_seconds))
        self._auto_correlation_id = auto_correlation_id

    @classmethod
    def from_env(cls) -> "JadeStockClient":
        """Constroi cliente por variaveis de ambiente para plug-and-play.

        Variaveis suportadas:
        - JADESTOCK_BASE_URL
        - JADESTOCK_TIMEOUT_SECONDS
        - JADESTOCK_BEARER_TOKEN
        - JADESTOCK_RETRIES
        - JADESTOCK_RETRY_BACKOFF_SECONDS
        - JADESTOCK_AUTO_CORRELATION_ID
        """
        return cls(
            base_url=os.getenv("JADESTOCK_BASE_URL", "http://127.0.0.1:8000"),
            timeout_seconds=float(os.getenv("JADESTOCK_TIMEOUT_SECONDS", "10.0")),
            bearer_token=os.getenv("JADESTOCK_BEARER_TOKEN"),
            retries=int(os.getenv("JADESTOCK_RETRIES", "0")),
            retry_backoff_seconds=float(os.getenv("JADESTOCK_RETRY_BACKOFF_SECONDS", "0.2")),
            auto_correlation_id=_parse_bool(os.getenv("JADESTOCK_AUTO_CORRELATION_ID"), default=False),
        )

    def set_bearer_token(self, token: str | None) -> None:
        """Atualiza token de autenticacao sem recriar o cliente."""
        self._bearer_token = token

    # Core WMS
    def health(self) -> dict[str, Any]:
        return self._request("GET", "/v1/health")

    def registrar_movimentacao(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/movimentacoes", payload=payload)

    def registrar_ajuste(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/ajustes", payload=payload)

    def registrar_avaria(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/avarias", payload=payload)

    def registrar_recebimento(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/recebimentos", payload=payload)

    def registrar_inventario_ciclico(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/inventarios/ciclico", payload=payload)

    def registrar_politica_kanban(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/kanban/politicas", payload=payload)

    def processar_curva_abcd(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/curva-abcd/processar", payload=payload)

    def processar_giro(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/giro/processar", payload=payload)

    def processar_sazonalidade(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/sazonalidade/processar", payload=payload)

    def simular_orcamento(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/v1/orcamento/simular", payload=payload)

    # Helpers para reduzir boilerplate
    def movimentacao_entrada(
        self,
        *,
        sku_id: str,
        quantidade: float,
        endereco_destino: str,
        operador: str,
        correlation_id: str | None = None,
        motivo: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "sku_id": sku_id,
            "tipo_movimentacao": "entrada",
            "quantidade": quantidade,
            "endereco_origem": None,
            "endereco_destino": endereco_destino,
            "operador": operador,
            "correlation_id": correlation_id or new_correlation_id(),
            "motivo": motivo,
        }
        return self.registrar_movimentacao(payload)

    def movimentacao_saida(
        self,
        *,
        sku_id: str,
        quantidade: float,
        endereco_origem: str,
        operador: str,
        correlation_id: str | None = None,
        motivo: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "sku_id": sku_id,
            "tipo_movimentacao": "saida",
            "quantidade": quantidade,
            "endereco_origem": endereco_origem,
            "endereco_destino": None,
            "operador": operador,
            "correlation_id": correlation_id or new_correlation_id(),
            "motivo": motivo,
        }
        return self.registrar_movimentacao(payload)

    def movimentacao_transferencia(
        self,
        *,
        sku_id: str,
        quantidade: float,
        endereco_origem: str,
        endereco_destino: str,
        operador: str,
        correlation_id: str | None = None,
        motivo: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "sku_id": sku_id,
            "tipo_movimentacao": "transferencia",
            "quantidade": quantidade,
            "endereco_origem": endereco_origem,
            "endereco_destino": endereco_destino,
            "operador": operador,
            "correlation_id": correlation_id or new_correlation_id(),
            "motivo": motivo,
        }
        return self.registrar_movimentacao(payload)

    # Trilha XML dedicada
    def analisar_xml(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/wms/v1/xml/analisar", payload=payload)

    def validar_xml(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/wms/v1/xml/validar", payload=payload)

    def confirmar_xml(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._request("POST", "/wms/v1/xml/confirmar", payload=payload)

    def historico_importacoes(
        self,
        *,
        tenant_id: str,
        limite: int = 100,
        offset: int = 0,
        status_filtro: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"limite": limite, "offset": offset}
        if status_filtro:
            params["status_filtro"] = status_filtro
        return self._request("GET", f"/wms/v1/xml/historico/{tenant_id}", query_params=params)

    def estatisticas_importacoes(self, *, tenant_id: str, dias: int = 30) -> dict[str, Any]:
        return self._request(
            "GET",
            f"/wms/v1/xml/estatisticas/{tenant_id}",
            query_params={"dias": dias},
        )

    def verificar_status_nfe(self, *, tenant_id: str, chave_acesso: str) -> dict[str, Any]:
        return self._request("GET", f"/wms/v1/xml/verificar/{tenant_id}/{chave_acesso}")

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        query_params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        if query_params:
            query = urllib.parse.urlencode(query_params, doseq=True)
            url = f"{url}?{query}"

        headers = {
            "Accept": "application/json",
        }
        data = None
        if payload is not None:
            payload_to_send = payload
            if self._auto_correlation_id and method == "POST":
                corr = payload_to_send.get("correlation_id")
                if not isinstance(corr, str) or not corr.strip():
                    payload_to_send = dict(payload_to_send)
                    payload_to_send["correlation_id"] = new_correlation_id()

            data = json.dumps(payload_to_send).encode("utf-8")
            headers["Content-Type"] = "application/json"
            corr = payload_to_send.get("correlation_id")
            if isinstance(corr, str) and corr.strip():
                headers["X-Correlation-ID"] = corr

        if self._bearer_token:
            headers["Authorization"] = f"Bearer {self._bearer_token}"

        req = urllib.request.Request(
            url=url,
            data=data,
            headers=headers,
            method=method,
        )

        for attempt in range(self._retries + 1):
            try:
                with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                    body = resp.read()
                    return json.loads(body.decode("utf-8")) if body else {}
            except urllib.error.HTTPError as exc:
                raw = exc.read().decode("utf-8")
                try:
                    payload_err = json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    payload_err = {}

                if isinstance(payload_err.get("detail"), dict):
                    payload_err = payload_err["detail"]

                raise JadeStockSDKError(
                    status_code=exc.code,
                    code=payload_err.get("code", payload_err.get("erro", "http_error")),
                    message=payload_err.get("message", payload_err.get("mensagem", raw or "erro_http")),
                    details=payload_err.get("details", payload_err.get("detalhes")),
                    correlation_id=payload_err.get("correlation_id"),
                ) from exc
            except urllib.error.URLError as exc:
                if attempt < self._retries:
                    time.sleep(self._retry_backoff_seconds * (attempt + 1))
                    continue

                reason = str(getattr(exc, "reason", exc))
                raise JadeStockSDKError(
                    status_code=503,
                    code="upstream_unreachable",
                    message=f"Nao foi possivel conectar na API Jade-stock em {url}: {reason}",
                    details={"url": url, "reason": reason},
                    correlation_id=None,
                ) from exc

        raise JadeStockSDKError(
            status_code=500,
            code="sdk_unexpected_state",
            message="falha inesperada no cliente SDK",
        )
