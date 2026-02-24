"""Laboratorio visual para testar a API Jade-stock via SDK.

Uso:
  PYTHONPATH=. python -m uvicorn LaboratorioDepositoBebidas.app:app --reload --port 8700
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Garante import do SDK local sem instalar pacote no site-packages.
ROOT_DIR = Path(__file__).resolve().parents[1]
SDK_DIR = ROOT_DIR / "sdk"
if str(SDK_DIR) not in sys.path:
    sys.path.insert(0, str(SDK_DIR))

from jadestock_sdk.client import JadeStockClient, JadeStockSDKError  # noqa: E402


class ExecuteRequest(BaseModel):
    operation: str
    base_url: str = Field(default="http://127.0.0.1:8000")
    bearer_token: str | None = None
    payload: dict[str, Any] | None = None


app = FastAPI(title="Laboratorio Deposito de Bebidas", version="1.0.0")
app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")


_OPERATION_MAP = {
    "health": "health",
    "registrar_movimentacao": "registrar_movimentacao",
    "registrar_ajuste": "registrar_ajuste",
    "registrar_avaria": "registrar_avaria",
    "registrar_recebimento": "registrar_recebimento",
    "registrar_inventario_ciclico": "registrar_inventario_ciclico",
    "registrar_politica_kanban": "registrar_politica_kanban",
    "processar_curva_abcd": "processar_curva_abcd",
    "processar_giro": "processar_giro",
    "processar_sazonalidade": "processar_sazonalidade",
    "simular_orcamento": "simular_orcamento",
}


@app.get("/")
def home() -> FileResponse:
    return FileResponse(Path(__file__).parent / "static" / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "laboratorio-deposito-bebidas"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon() -> Response:
    return Response(status_code=204)


@app.get("/.well-known/appspecific/com.chrome.devtools.json", include_in_schema=False)
def chrome_devtools_noise() -> Response:
    return Response(status_code=204)


@app.get("/api/operations")
def list_operations() -> dict[str, list[str]]:
    return {"operations": list(_OPERATION_MAP.keys())}


@app.post("/api/execute")
def execute(req: ExecuteRequest) -> dict[str, Any]:
    if req.operation not in _OPERATION_MAP:
        raise HTTPException(status_code=400, detail="operation_invalida")

    client = JadeStockClient(
        base_url=req.base_url,
        bearer_token=req.bearer_token,
    )

    method_name = _OPERATION_MAP[req.operation]
    method = getattr(client, method_name)

    try:
        if req.operation == "health":
            result = method()
        else:
            payload = req.payload or {}
            result = method(payload)
    except JadeStockSDKError as exc:
        raise HTTPException(
            status_code=exc.status_code,
            detail={
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "correlation_id": exc.correlation_id,
            },
        ) from exc
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=500, detail=f"erro_interno: {exc}") from exc

    # Retorna JSON serializavel para facilitar debug no frontend.
    try:
        json.dumps(result)
        safe_result = result
    except TypeError:
        safe_result = json.loads(json.dumps(result, default=str))

    return {
        "ok": True,
        "operation": req.operation,
        "base_url": req.base_url,
        "result": safe_result,
    }
