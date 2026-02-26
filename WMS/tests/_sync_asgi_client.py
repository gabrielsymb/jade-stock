"""Cliente de teste síncrono para ASGI com loop dedicado.

Evita abrir/fechar event loop por request (problema comum com asyncpg/SQLAlchemy).
"""

from __future__ import annotations

import asyncio
import threading
from typing import Any

from httpx import ASGITransport, AsyncClient, Response


class SyncASGITestClient:
    """Cliente síncrono mínimo compatível com get/post/request."""

    __test__ = False

    def __init__(self, app: Any, base_url: str = "http://testserver"):
        self._app = app
        self._base_url = base_url
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._closed = False
        self._client: AsyncClient | None = None

        self._thread.start()
        self._run_coro(self._build_client())

    def _run_loop(self) -> None:
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()

    async def _build_client(self) -> None:
        transport = ASGITransport(app=self._app, raise_app_exceptions=True)
        self._client = AsyncClient(
            transport=transport,
            base_url=self._base_url,
            follow_redirects=True,
        )

    def _run_coro(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def __enter__(self) -> "SyncASGITestClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._client is not None:
            self._run_coro(self._client.aclose())
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=2)
        self._loop.close()

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass

    def request(self, method: str, url: str, **kwargs: Any) -> Response:
        async def _do_request() -> Response:
            assert self._client is not None
            return await self._client.request(method, url, **kwargs)

        return self._run_coro(_do_request())

    def get(self, url: str, **kwargs: Any) -> Response:
        return self.request("GET", url, **kwargs)

    def post(self, url: str, **kwargs: Any) -> Response:
        return self.request("POST", url, **kwargs)
