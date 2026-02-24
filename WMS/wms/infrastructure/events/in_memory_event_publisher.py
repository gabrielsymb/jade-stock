"""Publisher em memoria para eventos de dominio."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4


class InMemoryEventPublisher:
    def __init__(self, tenant_id: str = "default") -> None:
        self.tenant_id = tenant_id
        self.events: list[dict] = []

    def publish(self, event_name: str, payload: dict) -> None:
        event = {
            "event_name": event_name,
            "event_type": event_name,
            "bounded_context": payload.get("bounded_context", "wms"),
            "aggregate_type": payload.get("aggregate_type"),
            "aggregate_id": payload.get("aggregate_id"),
            "event_id": f"evt_{uuid4().hex[:12]}",
            "occurred_at": datetime.now(timezone.utc).isoformat(),
            "actor_id": payload.get("actor_id", "system"),
            "tenant_id": self.tenant_id,
            "correlation_id": payload.get("correlation_id"),
            "causation_id": payload.get("causation_id"),
            "schema_version": "1.0",
            "payload": payload,
        }
        self.events.append(event)
