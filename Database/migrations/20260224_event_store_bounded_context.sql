-- Migration incremental para event_store (DDD/Event Sourcing naming)
-- Aplica em ambientes onde event_store ja existe sem os novos campos.

ALTER TABLE event_store
    ADD COLUMN IF NOT EXISTS event_type TEXT;

ALTER TABLE event_store
    ADD COLUMN IF NOT EXISTS bounded_context TEXT;

ALTER TABLE event_store
    ADD COLUMN IF NOT EXISTS aggregate_type TEXT;

ALTER TABLE event_store
    ADD COLUMN IF NOT EXISTS aggregate_id TEXT;

ALTER TABLE event_store
    ADD COLUMN IF NOT EXISTS causation_id TEXT;

UPDATE event_store
SET event_type = event_name
WHERE event_type IS NULL;

UPDATE event_store
SET bounded_context = 'wms'
WHERE bounded_context IS NULL;

ALTER TABLE event_store
    ALTER COLUMN event_type SET NOT NULL;

ALTER TABLE event_store
    ALTER COLUMN bounded_context SET NOT NULL;

ALTER TABLE event_store
    ALTER COLUMN bounded_context SET DEFAULT 'wms';

CREATE INDEX IF NOT EXISTS ix_event_store_type_time
    ON event_store (event_type, occurred_at DESC);

CREATE INDEX IF NOT EXISTS ix_event_store_context_time
    ON event_store (bounded_context, occurred_at DESC);

CREATE INDEX IF NOT EXISTS ix_event_store_aggregate_time
    ON event_store (aggregate_type, aggregate_id, occurred_at DESC);
