"""Repositorio PostgreSQL para controle de idempotencia de comandos."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any


class IdempotencyPayloadConflict(RuntimeError):
    """Mesmo endpoint/correlation_id com payload diferente."""


@dataclass(frozen=True)
class IdempotencyAcquireResult:
    key: str
    acquired: bool
    cached_response: dict | None


class PostgresIdempotencyRepository:
    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def acquire(
        self,
        operation_name: str,
        correlation_id: str,
        request_payload: dict,
    ) -> IdempotencyAcquireResult:
        key = f"{operation_name}:{correlation_id}"
        request_hash = self._hash_payload(request_payload)

        sql_insert = """
            INSERT INTO idempotency_command (
                idempotency_key,
                operation_name,
                correlation_id,
                request_hash,
                status
            )
            VALUES (%s, %s, %s, %s, 'processing')
            ON CONFLICT (idempotency_key) DO NOTHING
            RETURNING idempotency_key
        """

        with self.connection.cursor() as cursor:
            cursor.execute(sql_insert, (key, operation_name, correlation_id, request_hash))
            inserted = cursor.fetchone()
            if inserted:
                return IdempotencyAcquireResult(
                    key=key,
                    acquired=True,
                    cached_response=None,
                )

            cursor.execute(
                """
                SELECT request_hash, status, response_payload
                FROM idempotency_command
                WHERE idempotency_key = %s
                FOR UPDATE
                """,
                (key,),
            )
            row = cursor.fetchone()
            if row is None:
                return IdempotencyAcquireResult(
                    key=key,
                    acquired=True,
                    cached_response=None,
                )

            stored_hash, status, response_payload = row
            if stored_hash != request_hash:
                raise IdempotencyPayloadConflict(
                    f"Conflito de idempotencia para {operation_name}/{correlation_id}"
                )

            if status == "completed" and response_payload is not None:
                return IdempotencyAcquireResult(
                    key=key,
                    acquired=False,
                    cached_response=response_payload,
                )

            return IdempotencyAcquireResult(
                key=key,
                acquired=True,
                cached_response=None,
            )

    def mark_completed(self, key: str, response_payload: dict) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE idempotency_command
                SET status = 'completed',
                    response_payload = %s::jsonb,
                    updated_at = NOW()
                WHERE idempotency_key = %s
                """,
                (json.dumps(response_payload, ensure_ascii=True), key),
            )

    def _hash_payload(self, payload: dict) -> str:
        normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
