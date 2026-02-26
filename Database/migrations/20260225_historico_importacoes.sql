-- =====================================================
-- Jade-Stock WMS: Schema Histórico de Importações
-- Migration: 20260225_historico_importacoes.sql
-- Responsabilidade: Controle de idempotência e auditoria
-- =====================================================

-- =====================================================
-- TABELA DE HISTÓRICO DE IMPORTAÇÕES
-- =====================================================

CREATE TABLE IF NOT EXISTS wms.historico_importacoes (
    -- Chave primária
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identificação Única (Idempotência)
    chave_acesso VARCHAR(44) NOT NULL,
    
    -- Metadados
    tenant_id UUID NOT NULL,
    fornecedor_id UUID,
    processamento_id VARCHAR(100) NOT NULL,
    confirmacao_id VARCHAR(100),
    
    -- Dados da NF-e
    nota_fiscal VARCHAR(20),
    data_emissao TIMESTAMPTZ,
    valor_total DECIMAL(18,2),
    
    -- Status e Controle
    status VARCHAR(20) NOT NULL DEFAULT 'PENDENTE',
    mensagem TEXT,
    
    -- Auditoria
    criado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    criado_por UUID,
    
    -- Dados adicionais
    dados_adicionais JSONB,
    
    -- Constraints
    CONSTRAINT historico_importacoes_status_check 
        CHECK (status IN ('PENDENTE', 'PROCESSANDO', 'CONCLUIDO', 'ERRO', 'DUPLICADO')),
    
    CONSTRAINT historico_importacoes_tenant_chave_unique 
        UNIQUE(tenant_id, chave_acesso)
);

-- =====================================================
-- ÍNDICES PARA PERFORMANCE
-- =====================================================

-- Índice principal para verificação de idempotência
CREATE UNIQUE INDEX IF NOT EXISTS idx_historico_importacoes_chave_acesso 
    ON wms.historico_importacoes(chave_acesso);

-- Índice para consultas por tenant
CREATE INDEX IF NOT EXISTS idx_historico_importacoes_tenant 
    ON wms.historico_importacoes(tenant_id);

-- Índice para consultas por fornecedor
CREATE INDEX IF NOT EXISTS idx_historico_importacoes_fornecedor 
    ON wms.historico_importacoes(fornecedor_id);

-- Índice para consultas por status
CREATE INDEX IF NOT EXISTS idx_historico_importacoes_status 
    ON wms.historico_importacoes(status);

-- Índice para consultas por data
CREATE INDEX IF NOT EXISTS idx_historico_importacoes_data 
    ON wms.historico_importacoes(criado_em DESC);

-- Índice composto para relatórios
CREATE INDEX IF NOT EXISTS idx_historico_importacoes_relatorio 
    ON wms.historico_importacoes(tenant_id, status, criado_em DESC);

-- =====================================================
-- TRIGGERS PARA AUDITORIA
-- =====================================================

-- Função para atualizar timestamp de atualização
CREATE OR REPLACE FUNCTION wms.fn_atualizar_timestamp_historico()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para atualizar timestamp automaticamente
CREATE TRIGGER trg_historico_importacoes_atualizado
    BEFORE UPDATE ON wms.historico_importacoes
    FOR EACH ROW EXECUTE FUNCTION wms.fn_atualizar_timestamp_historico();

-- =====================================================
-- VIEWS ÚTEIS
-- =====================================================

-- View de importações recentes por tenant
CREATE OR REPLACE VIEW wms.v_importacoes_recentes AS
SELECT 
    hi.id,
    hi.tenant_id,
    f.razao_social as fornecedor_nome,
    f.cnpj as fornecedor_cnpj,
    hi.chave_acesso,
    hi.nota_fiscal,
    hi.status,
    hi.mensagem,
    hi.criado_em,
    hi.valor_total,
    CASE 
        WHEN hi.criado_em >= NOW() - INTERVAL '1 day' THEN 'hoje'
        WHEN hi.criado_em >= NOW() - INTERVAL '7 days' THEN 'esta_semana'
        WHEN hi.criado_em >= NOW() - INTERVAL '30 days' THEN 'este_mes'
        ELSE 'antigo'
    END as categoria_tempo
FROM wms.historico_importacoes hi
LEFT JOIN fornecedor f ON hi.fornecedor_id = f.id
WHERE hi.criado_em >= NOW() - INTERVAL '30 days'
ORDER BY hi.criado_em DESC;

-- View de estatísticas por fornecedor
CREATE OR REPLACE VIEW wms.v_estatisticas_importacoes_fornecedor AS
SELECT 
    hi.tenant_id,
    hi.fornecedor_id,
    f.razao_social as fornecedor_nome,
    COUNT(*) as total_importacoes,
    COUNT(CASE WHEN hi.status = 'CONCLUIDO' THEN 1 END) as importacoes_concluidas,
    COUNT(CASE WHEN hi.status = 'ERRO' THEN 1 END) as importacoes_com_erro,
    COUNT(CASE WHEN hi.status = 'DUPLICADO' THEN 1 END) as importacoes_duplicadas,
    SUM(COALESCE(hi.valor_total, 0)) as valor_total_importado,
    MAX(hi.criado_em) as ultima_importacao,
    AVG(EXTRACT(EPOCH FROM (hi.atualizado_em - hi.criado_em))) as tempo_medio_processamento_seg
FROM wms.historico_importacoes hi
LEFT JOIN fornecedor f ON hi.fornecedor_id = f.id
GROUP BY hi.tenant_id, hi.fornecedor_id, f.razao_social
ORDER BY valor_total_importado DESC;

-- View de importações com erro
CREATE OR REPLACE VIEW wms.v_importacoes_com_erro AS
SELECT 
    hi.id,
    hi.tenant_id,
    f.razao_social as fornecedor_nome,
    hi.chave_acesso,
    hi.nota_fiscal,
    hi.status,
    hi.mensagem,
    hi.criado_em,
    hi.dados_adicionais
FROM wms.historico_importacoes hi
LEFT JOIN fornecedor f ON hi.fornecedor_id = f.id
WHERE hi.status = 'ERRO'
ORDER BY hi.criado_em DESC;

-- =====================================================
-- FUNÇÕES ÚTEIS
-- =====================================================

-- Função para verificar se chave de acesso já foi processada
CREATE OR REPLACE FUNCTION wms.fn_verificar_chave_acesso(
    p_tenant_id UUID,
    p_chave_acesso VARCHAR(44)
) RETURNS BOOLEAN AS $$
DECLARE
    v_existe BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM wms.historico_importacoes 
        WHERE tenant_id = p_tenant_id 
        AND chave_acesso = p_chave_acesso
    ) INTO v_existe;
    
    RETURN v_existe;
END;
$$ LANGUAGE plpgsql;

-- Função para obter estatísticas de importação
CREATE OR REPLACE FUNCTION wms.fn_estatisticas_importacao(
    p_tenant_id UUID,
    p_data_inicio TIMESTAMPTZ DEFAULT NULL,
    p_data_fim TIMESTAMPTZ DEFAULT NULL
) RETURNS TABLE (
    total_importacoes BIGINT,
    importacoes_concluidas BIGINT,
    importacoes_com_erro BIGINT,
    importacoes_duplicadas BIGINT,
    taxa_sucesso DECIMAL(5,2),
    valor_total_importado DECIMAL(18,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_importacoes,
        COUNT(CASE WHEN status = 'CONCLUIDO' THEN 1 END) as importacoes_concluidas,
        COUNT(CASE WHEN status = 'ERRO' THEN 1 END) as importacoes_com_erro,
        COUNT(CASE WHEN status = 'DUPLICADO' THEN 1 END) as importacoes_duplicadas,
        ROUND(
            COUNT(CASE WHEN status = 'CONCLUIDO' THEN 1 END) * 100.0 / 
            NULLIF(COUNT(*), 0), 2
        ) as taxa_sucesso,
        SUM(COALESCE(valor_total, 0)) as valor_total_importado
    FROM wms.historico_importacoes 
    WHERE tenant_id = p_tenant_id
    AND (p_data_inicio IS NULL OR criado_em >= p_data_inicio)
    AND (p_data_fim IS NULL OR criado_em <= p_data_fim);
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- POLÍTICAS DE SEGURANÇA (RLS)
-- =====================================================

-- Habilitar Row Level Security
ALTER TABLE wms.historico_importacoes ENABLE ROW LEVEL SECURITY;

-- Política: Usuários só podem ver importações do seu tenant
CREATE POLICY historico_importacoes_tenant_isolation ON wms.historico_importacoes
    FOR ALL
    TO app_user
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- =====================================================
-- COMENTÁRIOS EXPLICATIVOS
-- =====================================================

COMMENT ON TABLE wms.historico_importacoes IS 
    'Tabela de controle de idempotência e auditoria de importações XML. ' ||
    'Garante que cada NF-e seja processada apenas uma vez, mesmo com reenvios.';

COMMENT ON COLUMN wms.historico_importacoes.chave_acesso IS 
    'Chave de acesso da NF-e (44 dígitos). Identificador único para idempotência.';

COMMENT ON COLUMN wms.historico_importacoes.status IS 
    'Status da importação: PENDENTE, PROCESSANDO, CONCLUIDO, ERRO, DUPLICADO';

COMMENT ON COLUMN wms.historico_importacoes.dados_adicionais IS 
    'Dados adicionais em JSON para auditoria e debugging';

COMMENT ON CONSTRAINT historico_importacoes_tenant_chave_unique IS 
    'Garante idempotência: mesma NF-e não pode ser importada duas vezes no mesmo tenant.';

COMMENT ON INDEX idx_historico_importacoes_chave_acesso IS 
    'Índice principal para verificação rápida de idempotência';

-- =====================================================
-- DADOS DE EXEMPLO (APENAS PARA DESENVOLVIMENTO)
-- =====================================================

DO $$
DECLARE
    is_dev BOOLEAN;
BEGIN
    -- Verificar se estamos em ambiente de desenvolvimento
    SELECT EXISTS (
        SELECT 1 FROM information_schema.schemata 
        WHERE schema_name = 'wms'
    ) INTO is_dev;
    
    IF is_dev THEN
        -- Inserir dados de exemplo
        INSERT INTO wms.historico_importacoes (
            chave_acesso,
            tenant_id,
            fornecedor_id,
            processamento_id,
            confirmacao_id,
            nota_fiscal,
            status,
            valor_total,
            dados_adicionais
        ) VALUES (
            '3523021234567890123456789012345678901234', -- Chave de acesso exemplo
            (SELECT id FROM tenant LIMIT 1),
            (SELECT id FROM fornecedor WHERE cnpj LIKE '%12345678901234%' LIMIT 1),
            'proc_001',
            'conf_001',
            '123456',
            'CONCLUIDO',
            558.00,
            '{"items": 3, "tempo_ms": 1250}'
        ) ON CONFLICT (tenant_id, chave_acesso) DO NOTHING;
    END IF;
END $$;

-- =====================================================
-- VALIDAÇÕES FINAIS
-- =====================================================

-- Verificar se tabela foi criada corretamente
DO $$
DECLARE
    table_exists BOOLEAN;
    constraint_count INTEGER;
BEGIN
    -- Verificar existência da tabela
    SELECT EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'wms' 
        AND table_name = 'historico_importacoes'
    ) INTO table_exists;
    
    IF NOT table_exists THEN
        RAISE EXCEPTION 'Erro: Tabela wms.historico_importacoes não foi criada';
    END IF;
    
    -- Verificar constraints
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.check_constraints 
    WHERE constraint_schema = 'wms'
    AND constraint_name LIKE '%historico_importacoes%';
    
    IF constraint_count < 2 THEN
        RAISE EXCEPTION 'Erro: Constraints não foram criadas corretamente. Esperado: 2, Encontrado: %', constraint_count;
    END IF;
    
    RAISE NOTICE 'Migration Histórico de Importações concluída com sucesso.';
    RAISE NOTICE 'Tabela: wms.historico_importacoes';
    RAISE NOTICE 'Constraints: % verificadas', constraint_count;
END $$;
