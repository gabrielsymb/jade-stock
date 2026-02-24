"""Cliente HTTP minimo para a API WMS (v1)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


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
    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8000",
        timeout_seconds: float = 10.0,
        bearer_token: str | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._bearer_token = bearer_token

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

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = f"{self._base_url}{path}"
        headers = {
            "Accept": "application/json",
        }
        data = None
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
            corr = payload.get("correlation_id")
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
            raise JadeStockSDKError(
                status_code=exc.code,
                code=payload_err.get("code", "http_error"),
                message=payload_err.get("message", raw or "erro_http"),
                details=payload_err.get("details"),
                correlation_id=payload_err.get("correlation_id"),
            ) from exc
        except urllib.error.URLError as exc:
            reason = str(getattr(exc, "reason", exc))
            raise JadeStockSDKError(
                status_code=503,
                code="upstream_unreachable",
                message=f"Nao foi possivel conectar na API Jade-stock em {url}: {reason}",
                details={"url": url, "reason": reason},
                correlation_id=None,
            ) from exc
