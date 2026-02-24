-- =====================================================
-- WMS - Schema CORE (fase atual)
-- Uso: casos de uso implementados hoje
-- - RegistrarMovimentacaoEstoque
-- - RegistrarAjusteEstoque
-- - RegistrarRecebimento
--
-- Regras:
-- - Sem trigger/procedure
-- - Sem logica de negocio no SQL
-- - IDs em TEXT (UUID/string gerados pela aplicacao)
-- =====================================================

-- =====================================
-- 1) Cadastro minimo
-- =====================================

CREATE TABLE IF NOT EXISTS item_master (
    item_master_id           TEXT PRIMARY KEY,
    item_nome                TEXT NOT NULL,
    categoria_id             TEXT,
    classe_abc               TEXT,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by               TEXT,
    correlation_id           TEXT
);

CREATE TABLE IF NOT EXISTS sku (
    sku_id                   TEXT PRIMARY KEY,
    sku_codigo               TEXT NOT NULL UNIQUE,
    sku_nome                 TEXT NOT NULL,
    item_master_id           TEXT REFERENCES item_master(item_master_id),
    ean                      TEXT,
    unidade_medida           TEXT,
    status_ativo             BOOLEAN NOT NULL DEFAULT TRUE,
    variacao_volume          TEXT,
    variacao_cor             TEXT,
    variacao_tamanho         TEXT,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by               TEXT,
    correlation_id           TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_sku_ean_not_null
    ON sku (ean)
    WHERE ean IS NOT NULL;

CREATE TABLE IF NOT EXISTS endereco (
    endereco_codigo          TEXT PRIMARY KEY,
    zona_codigo              TEXT NOT NULL,
    prateleira_codigo        TEXT,
    posicao_codigo           TEXT,
    tipo_endereco            TEXT NOT NULL,
    ativo                    BOOLEAN NOT NULL DEFAULT TRUE,
    capacidade_maxima        NUMERIC(18,4),
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by               TEXT,
    correlation_id           TEXT
);

-- =====================================
-- 2) Estoque e movimentacao
-- =====================================

CREATE TABLE IF NOT EXISTS saldo_estoque (
    saldo_estoque_id         TEXT PRIMARY KEY,
    sku_id                   TEXT NOT NULL REFERENCES sku(sku_id),
    endereco_codigo          TEXT NOT NULL REFERENCES endereco(endereco_codigo),
    saldo_disponivel         NUMERIC(18,4) NOT NULL DEFAULT 0,
    saldo_avariado           NUMERIC(18,4) NOT NULL DEFAULT 0,
    saldo_bloqueado          NUMERIC(18,4) NOT NULL DEFAULT 0,
    saldo_total              NUMERIC(18,4) NOT NULL DEFAULT 0,
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by               TEXT,
    correlation_id           TEXT,
    CONSTRAINT uq_saldo_sku_endereco UNIQUE (sku_id, endereco_codigo)
);

CREATE INDEX IF NOT EXISTS ix_saldo_sku ON saldo_estoque (sku_id);
CREATE INDEX IF NOT EXISTS ix_saldo_endereco ON saldo_estoque (endereco_codigo);

CREATE TABLE IF NOT EXISTS movimentacao_estoque (
    movimentacao_id          TEXT PRIMARY KEY,
    tipo_movimentacao        TEXT NOT NULL,
    sku_id                   TEXT NOT NULL REFERENCES sku(sku_id),
    quantidade               NUMERIC(18,4) NOT NULL,
    endereco_origem          TEXT REFERENCES endereco(endereco_codigo),
    endereco_destino         TEXT REFERENCES endereco(endereco_codigo),
    motivo                   TEXT,
    actor_id                 TEXT,
    tenant_id                TEXT,
    correlation_id           TEXT NOT NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    schema_version           TEXT NOT NULL DEFAULT '1.0'
);

CREATE INDEX IF NOT EXISTS ix_movimentacao_sku ON movimentacao_estoque (sku_id, created_at DESC);
CREATE INDEX IF NOT EXISTS ix_movimentacao_corr ON movimentacao_estoque (correlation_id);

-- =====================================
-- 3) Recebimento
-- =====================================

CREATE TABLE IF NOT EXISTS recebimento (
    recebimento_id           TEXT PRIMARY KEY,
    nota_fiscal_numero       TEXT NOT NULL,
    fornecedor_id            TEXT,
    status_conferencia       TEXT NOT NULL,
    possui_avaria            BOOLEAN NOT NULL DEFAULT FALSE,
    divergencia_quantidade   BOOLEAN NOT NULL DEFAULT FALSE,
    actor_id                 TEXT,
    tenant_id                TEXT,
    correlation_id           TEXT NOT NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    schema_version           TEXT NOT NULL DEFAULT '1.0',
    CONSTRAINT uq_recebimento_nota_corr UNIQUE (nota_fiscal_numero, correlation_id)
);

CREATE INDEX IF NOT EXISTS ix_recebimento_nota ON recebimento (nota_fiscal_numero);

CREATE TABLE IF NOT EXISTS recebimento_item (
    recebimento_item_id          TEXT PRIMARY KEY,
    recebimento_id               TEXT NOT NULL REFERENCES recebimento(recebimento_id) ON DELETE CASCADE,
    sku_id                       TEXT NOT NULL REFERENCES sku(sku_id),
    endereco_destino             TEXT NOT NULL REFERENCES endereco(endereco_codigo),
    quantidade_esperada          NUMERIC(18,4) NOT NULL,
    quantidade_conferida         NUMERIC(18,4) NOT NULL,
    divergencia                  BOOLEAN NOT NULL DEFAULT FALSE,
    classificacao_divergencia    TEXT,
    created_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_id               TEXT
);

CREATE INDEX IF NOT EXISTS ix_recebimento_item_rec ON recebimento_item (recebimento_id);
CREATE INDEX IF NOT EXISTS ix_recebimento_item_sku ON recebimento_item (sku_id);

-- =====================================
-- 4) Event store
-- =====================================

CREATE TABLE IF NOT EXISTS event_store (
    event_id                  TEXT PRIMARY KEY,
    event_name                TEXT NOT NULL,
    occurred_at               TIMESTAMPTZ NOT NULL,
    actor_id                  TEXT,
    tenant_id                 TEXT,
    correlation_id            TEXT NOT NULL,
    schema_version            TEXT NOT NULL,
    payload                   JSONB NOT NULL,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_event_store_name_time ON event_store (event_name, occurred_at DESC);
CREATE INDEX IF NOT EXISTS ix_event_store_corr ON event_store (correlation_id);

-- =====================================
-- 5) Idempotencia de comandos (API)
-- =====================================

CREATE TABLE IF NOT EXISTS idempotency_command (
    idempotency_key         TEXT PRIMARY KEY,
    operation_name          TEXT NOT NULL,
    correlation_id          TEXT NOT NULL,
    request_hash            TEXT NOT NULL,
    response_payload        JSONB,
    status                  TEXT NOT NULL DEFAULT 'processing',
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_idempotency_corr ON idempotency_command (correlation_id);
