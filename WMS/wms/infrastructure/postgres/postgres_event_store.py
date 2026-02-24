"""Placeholder de event store/publisher PostgreSQL."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class PostgresEventStore:
    def __init__(self, connection: Any, tenant_id: str = "default") -> None:
        self.connection = connection
        self.tenant_id = tenant_id

    def publish(self, event_name: str, payload: dict) -> None:
        bounded_context = payload.get("bounded_context", "wms")
        aggregate_type = payload.get("aggregate_type")
        aggregate_id = payload.get("aggregate_id")
        causation_id = payload.get("causation_id")
        sql = """
            INSERT INTO event_store (
                event_id,
                event_name,
                event_type,
                bounded_context,
                aggregate_type,
                aggregate_id,
                occurred_at,
                actor_id,
                tenant_id,
                correlation_id,
                causation_id,
                schema_version,
                payload
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
        """
        params = (
            f"evt_{uuid4().hex[:12]}",
            event_name,
            event_name,
            bounded_context,
            aggregate_type,
            aggregate_id,
            datetime.now(timezone.utc),
            payload.get("actor_id", "system"),
            self.tenant_id,
            payload.get("correlation_id"),
            causation_id,
            "1.0",
            self._json_dump(payload),
        )
        with self.connection.cursor() as cursor:
            cursor.execute(sql, params)

    def _json_dump(self, payload: dict) -> str:
        import json

        return json.dumps(payload, ensure_ascii=True)
