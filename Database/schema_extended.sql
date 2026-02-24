-- =====================================================
-- WMS - Schema EXTENDED (fase futura)
-- Aplicar somente apos schema_core.sql
--
-- Regras:
-- - Sem trigger/procedure
-- - Sem logica de negocio no SQL
-- =====================================================

-- =====================================
-- 1) Cadastro/operacao avancada
-- =====================================

CREATE TABLE IF NOT EXISTS sku_endereco (
    sku_endereco_id          TEXT PRIMARY KEY,
    sku_id                   TEXT NOT NULL REFERENCES sku(sku_id),
    endereco_codigo          TEXT NOT NULL REFERENCES endereco(endereco_codigo),
    endereco_principal       BOOLEAN NOT NULL DEFAULT FALSE,
    ativo                    BOOLEAN NOT NULL DEFAULT TRUE,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by               TEXT,
    correlation_id           TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_sku_endereco_ativo
    ON sku_endereco (sku_id, endereco_codigo)
    WHERE ativo = TRUE;

CREATE TABLE IF NOT EXISTS lote_validade (
    lote_id                  TEXT PRIMARY KEY,
    sku_id                   TEXT NOT NULL REFERENCES sku(sku_id),
    validade_data            DATE NOT NULL,
    shelf_life_dias          INTEGER,
    risco_vencimento         TEXT,
    quantidade_lote          NUMERIC(18,4) NOT NULL DEFAULT 0,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_id           TEXT
);

CREATE INDEX IF NOT EXISTS ix_lote_sku_validade ON lote_validade (sku_id, validade_data);

-- =====================================
-- 2) Perdas e inventario
-- =====================================

CREATE TABLE IF NOT EXISTS avaria_registro (
    avaria_id                TEXT PRIMARY KEY,
    sku_id                   TEXT NOT NULL REFERENCES sku(sku_id),
    recebimento_id           TEXT REFERENCES recebimento(recebimento_id),
    tipo_avaria              TEXT NOT NULL,
    origem_processo          TEXT NOT NULL,
    quantidade_avariada      NUMERIC(18,4) NOT NULL,
    observacao               TEXT,
    evidencia_url            TEXT,
    actor_id                 TEXT,
    correlation_id           TEXT NOT NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_avaria_sku ON avaria_registro (sku_id, created_at DESC);

CREATE TABLE IF NOT EXISTS inventario_contagem (
    contagem_id              TEXT PRIMARY KEY,
    sku_id                   TEXT NOT NULL REFERENCES sku(sku_id),
    endereco_codigo          TEXT NOT NULL REFERENCES endereco(endereco_codigo),
    quantidade_sistemica     NUMERIC(18,4) NOT NULL,
    quantidade_contada       NUMERIC(18,4) NOT NULL,
    divergencia              BOOLEAN NOT NULL DEFAULT FALSE,
    divergencia_valor        NUMERIC(18,4) NOT NULL DEFAULT 0,
    snapshot_url             TEXT,
    actor_id                 TEXT,
    correlation_id           TEXT NOT NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_contagem_sku_endereco ON inventario_contagem (sku_id, endereco_codigo, created_at DESC);

-- =====================================
-- 3) Politicas de reposicao
-- =====================================

CREATE TABLE IF NOT EXISTS politica_reposicao (
    politica_reposicao_id    TEXT PRIMARY KEY,
    sku_id                   TEXT NOT NULL UNIQUE REFERENCES sku(sku_id),
    classe_abc               TEXT,
    cobertura_dias           NUMERIC(10,2),
    giro_periodo             NUMERIC(18,6),
    lead_time_dias           NUMERIC(10,2),
    fator_sazonal            NUMERIC(18,6),
    sazonalidade_status      TEXT,
    janela_analise_meses     INTEGER,
    shelf_life_dias          INTEGER,
    risco_vencimento         TEXT,
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by               TEXT,
    correlation_id           TEXT
);

CREATE TABLE IF NOT EXISTS kanban_politica (
    kanban_politica_id       TEXT PRIMARY KEY,
    sku_id                   TEXT NOT NULL UNIQUE REFERENCES sku(sku_id),
    elegivel                 BOOLEAN NOT NULL DEFAULT FALSE,
    kanban_ativo             BOOLEAN NOT NULL DEFAULT FALSE,
    faixa_atual              TEXT,
    faixa_verde_min          NUMERIC(18,4),
    faixa_amarela_min        NUMERIC(18,4),
    faixa_vermelha_min       NUMERIC(18,4),
    updated_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by               TEXT,
    correlation_id           TEXT
);

CREATE TABLE IF NOT EXISTS kanban_historico (
    kanban_historico_id      TEXT PRIMARY KEY,
    sku_id                   TEXT NOT NULL REFERENCES sku(sku_id),
    faixa_anterior           TEXT,
    faixa_nova               TEXT,
    motivo                   TEXT,
    actor_id                 TEXT,
    correlation_id           TEXT NOT NULL,
    created_at               TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_kanban_hist_sku ON kanban_historico (sku_id, created_at DESC);

-- =====================================
-- 4) Governanca orcamentaria
-- =====================================

CREATE TABLE IF NOT EXISTS orcamento_periodo (
    orcamento_periodo_id         TEXT PRIMARY KEY,
    periodo_referencia           DATE NOT NULL,
    orcamento_total_periodo      NUMERIC(18,2) NOT NULL,
    consumo_orcamento            NUMERIC(18,2) NOT NULL DEFAULT 0,
    created_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by                   TEXT,
    correlation_id               TEXT,
    CONSTRAINT uq_orcamento_periodo UNIQUE (periodo_referencia)
);

CREATE TABLE IF NOT EXISTS orcamento_categoria (
    orcamento_categoria_id        TEXT PRIMARY KEY,
    orcamento_periodo_id          TEXT NOT NULL REFERENCES orcamento_periodo(orcamento_periodo_id) ON DELETE CASCADE,
    categoria_id                  TEXT NOT NULL,
    orcamento_categoria_periodo   NUMERIC(18,2) NOT NULL,
    consumo_categoria             NUMERIC(18,2) NOT NULL DEFAULT 0,
    created_at                    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at                    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_id                TEXT,
    CONSTRAINT uq_orcamento_categoria_periodo UNIQUE (orcamento_periodo_id, categoria_id)
);

CREATE TABLE IF NOT EXISTS aporte_externo (
    aporte_externo_id         TEXT PRIMARY KEY,
    orcamento_periodo_id      TEXT NOT NULL REFERENCES orcamento_periodo(orcamento_periodo_id) ON DELETE CASCADE,
    valor                     NUMERIC(18,2) NOT NULL,
    origem                    TEXT NOT NULL,
    destino                   TEXT,
    validade_ate              DATE,
    aprovado_por              TEXT,
    observacao                TEXT,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_id            TEXT
);

CREATE TABLE IF NOT EXISTS compra_excecao (
    compra_excecao_id         TEXT PRIMARY KEY,
    orcamento_periodo_id      TEXT NOT NULL REFERENCES orcamento_periodo(orcamento_periodo_id) ON DELETE CASCADE,
    categoria_id              TEXT,
    valor_solicitado          NUMERIC(18,2) NOT NULL,
    valor_aprovado            NUMERIC(18,2),
    motivo                    TEXT NOT NULL,
    aprovado_por              TEXT,
    status                    TEXT NOT NULL,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_id            TEXT
);

-- =====================================
-- 5) Integracao externa (estatistica/ML)
-- =====================================

CREATE TABLE IF NOT EXISTS sinal_externo (
    sinal_externo_id          TEXT PRIMARY KEY,
    sku_id                    TEXT REFERENCES sku(sku_id),
    origem_motor              TEXT NOT NULL,
    tipo_sinal                TEXT NOT NULL,
    versao_modelo             TEXT,
    valor_sinal               NUMERIC(18,6),
    payload                   JSONB,
    validade_ate              TIMESTAMPTZ,
    received_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    correlation_id            TEXT
);

CREATE INDEX IF NOT EXISTS ix_sinal_externo_sku_time ON sinal_externo (sku_id, received_at DESC);
