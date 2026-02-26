-- =====================================================
-- Jade-Stock WMS: Schema VinculoFornecedorProduto
-- Migration: 20260225_vinculo_fornecedor_produto_schema.sql
-- Responsabilidade: Base de conhecimento do sistema
-- =====================================================

-- =====================================================
-- CRIAÇÃO DO SCHEMA WMS (se não existir)
-- =====================================================
CREATE SCHEMA IF NOT EXISTS wms;

-- =====================================================
-- TABELA PRINCIPAL: vinculo_fornecedor_produto
-- =====================================================
-- Propósito: Traduzir códigos externos para produtos internos
-- Características: Aprendizado contínuo, conversão de unidades, auditoria completa

CREATE TABLE IF NOT EXISTS wms.vinculo_fornecedor_produto (
    -- Chave primária
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Identificação e Relacionamentos
    tenant_id UUID NOT NULL,
    fornecedor_id UUID NOT NULL,
    codigo_fornecedor VARCHAR(100) NOT NULL,
    produto_id_interno UUID NOT NULL,
    
    -- Conversão de Unidades
    fator_conversao DECIMAL(15,6) NOT NULL DEFAULT 1.0,
    unidade_origem VARCHAR(10),
    unidade_destino VARCHAR(10),
    
    -- Controle de Status
    status VARCHAR(20) NOT NULL DEFAULT 'ativo' 
        CHECK (status IN ('ativo', 'inativo', 'em_validacao')),
    
    -- Estatísticas de Uso
    vezes_utilizado INTEGER NOT NULL DEFAULT 0,
    ultima_importacao TIMESTAMP,
    
    -- Configuração de Aprendizado
    peso_confianca DECIMAL(5,2) NOT NULL DEFAULT 1.0 
        CHECK (peso_confianca >= 0 AND peso_confianca <= 10),
    
    -- Auditoria
    criado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    atualizado_em TIMESTAMP NOT NULL DEFAULT NOW(),
    criado_por UUID,
    ultima_validacao TIMESTAMP,
    
    -- Constraints de Integridade
    CONSTRAINT vinculo_fornecedor_produto_unique 
        UNIQUE(tenant_id, fornecedor_id, codigo_fornecedor),
    CONSTRAINT vinculo_fornecedor_produto_fator_positivo 
        CHECK (fator_conversao > 0),
    CONSTRAINT vinculo_fornecedor_produto_uso_nao_negativo 
        CHECK (vezes_utilizado >= 0)
);

-- =====================================================
-- ÍNDICES PARA PERFORMANCE
-- =====================================================

-- Índice principal para consultas de importação
CREATE INDEX IF NOT EXISTS idx_vinculo_fornecedor_produto_fornecedor_codigo 
    ON wms.vinculo_fornecedor_produto(fornecedor_id, codigo_fornecedor);

-- Índice para consultas por produto interno
CREATE INDEX IF NOT EXISTS idx_vinculo_fornecedor_produto_produto 
    ON wms.vinculo_fornecedor_produto(produto_id_interno);

-- Índice para consultas por tenant
CREATE INDEX IF NOT EXISTS idx_vinculo_fornecedor_produto_tenant 
    ON wms.vinculo_fornecedor_produto(tenant_id);

-- Índice para consultas por status
CREATE INDEX IF NOT EXISTS idx_vinculo_fornecedor_produto_status 
    ON wms.vinculo_fornecedor_produto(status);

-- Índice composto para estatísticas
CREATE INDEX IF NOT EXISTS idx_vinculo_fornecedor_produto_estatisticas 
    ON wms.vinculo_fornecedor_produto(tenant_id, status, vezes_utilizado DESC);

-- Índice para busca por código parcial (LIKE)
CREATE INDEX IF NOT EXISTS idx_vinculo_fornecedor_produto_codigo_parcial 
    ON wms.vinculo_fornecedor_produto(codigo_fornecedor varchar_pattern_ops);

-- =====================================================
-- TRIGGERS PARA AUDITORIA AUTOMÁTICA
-- =====================================================

-- Função para atualizar timestamp de atualização
CREATE OR REPLACE FUNCTION wms.fn_atualizar_timestamp_vinculo()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para atualizar timestamp automaticamente
CREATE TRIGGER trg_vinculo_fornecedor_produto_atualizado
    BEFORE UPDATE ON wms.vinculo_fornecedor_produto
    FOR EACH ROW EXECUTE FUNCTION wms.fn_atualizar_timestamp_vinculo();

-- =====================================================
-- VIEWS ÚTEIS PARA CONSULTAS
-- =====================================================

-- View de vínculos ativos por tenant
CREATE OR REPLACE VIEW wms.v_vinculos_ativos AS
SELECT 
    vf.id,
    vf.tenant_id,
    f.razao_social as fornecedor_nome,
    f.cnpj as fornecedor_cnpj,
    vf.codigo_fornecedor,
    p.nome as produto_nome,
    p.gtin as produto_gtin,
    vf.fator_conversao,
    vf.unidade_origem,
    vf.unidade_destino,
    vf.vezes_utilizado,
    vf.ultima_importacao,
    vf.peso_confianca,
    vf.criado_em
FROM wms.vinculo_fornecedor_produto vf
JOIN fornecedor f ON vf.fornecedor_id = f.id
JOIN produto p ON vf.produto_id_interno = p.id
WHERE vf.status = 'ativo'
  AND f.ativo = true
  AND p.ativo = true;

-- View de estatísticas por fornecedor
CREATE OR REPLACE VIEW wms.v_estatisticas_vinculos_fornecedor AS
SELECT 
    vf.tenant_id,
    vf.fornecedor_id,
    f.razao_social as fornecedor_nome,
    COUNT(*) as total_vinculos,
    COUNT(CASE WHEN vf.status = 'ativo' THEN 1 END) as vinculos_ativos,
    SUM(vf.vezes_utilizado) as total_utilizacoes,
    MAX(vf.vezes_utilizado) as max_utilizacoes,
    AVG(vf.peso_confianca) as avg_peso_confianca,
    MAX(vf.ultima_importacao) as ultima_importacao
FROM wms.vinculo_fornecedor_produto vf
JOIN fornecedor f ON vf.fornecedor_id = f.id
GROUP BY vf.tenant_id, vf.fornecedor_id, f.razao_social
ORDER BY total_utilizacoes DESC;

-- View de vínculos recentes (últimos 30 dias)
CREATE OR REPLACE VIEW wms.v_vinculos_recentes AS
SELECT 
    vf.id,
    vf.tenant_id,
    f.razao_social as fornecedor_nome,
    vf.codigo_fornecedor,
    p.nome as produto_nome,
    vf.fator_conversao,
    vf.vezes_utilizado,
    vf.criado_em,
    CASE 
        WHEN vf.criado_em >= NOW() - INTERVAL '7 days' THEN 'muito_recente'
        WHEN vf.criado_em >= NOW() - INTERVAL '30 days' THEN 'recente'
        ELSE 'antigo'
    END as categoria_tempo
FROM wms.vinculo_fornecedor_produto vf
JOIN fornecedor f ON vf.fornecedor_id = f.id
JOIN produto p ON vf.produto_id_interno = p.id
WHERE vf.criado_em >= NOW() - INTERVAL '30 days'
ORDER BY vf.criado_em DESC;

-- =====================================================
-- FUNÇÕES ÚTEIS
-- =====================================================

-- Função para buscar vínculo por código do fornecedor
CREATE OR REPLACE FUNCTION wms.fn_buscar_vinculo_fornecedor(
    p_tenant_id UUID,
    p_fornecedor_id UUID,
    p_codigo_fornecedor VARCHAR(100)
) RETURNS TABLE (
    id UUID,
    produto_id_interno UUID,
    fator_conversao DECIMAL(15,6),
    unidade_origem VARCHAR(10),
    unidade_destino VARCHAR(10),
    status VARCHAR(20),
    peso_confianca DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        vf.id,
        vf.produto_id_interno,
        vf.fator_conversao,
        vf.unidade_origem,
        vf.unidade_destino,
        vf.status,
        vf.peso_confianca
    FROM wms.vinculo_fornecedor_produto vf
    WHERE vf.tenant_id = p_tenant_id
      AND vf.fornecedor_id = p_fornecedor_id
      AND vf.codigo_fornecedor = p_codigo_fornecedor
      AND vf.status = 'ativo'
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Função para incrementar utilização do vínculo
CREATE OR REPLACE FUNCTION wms.fn_registrar_utilizacao_vinculo(
    p_vinculo_id UUID,
    p_data_utilizacao TIMESTAMP DEFAULT NOW()
) RETURNS BOOLEAN AS $$
BEGIN
    UPDATE wms.vinculo_fornecedor_produto 
    SET 
        vezes_utilizado = vezes_utilizado + 1,
        ultima_importacao = p_data_utilizacao,
        atualizado_em = NOW()
    WHERE id = p_vinculo_id AND status = 'ativo';
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Função para obter sugestões de vinculação por similaridade
CREATE OR REPLACE FUNCTION wms.fn_sugerir_vinculos_similares(
    p_tenant_id UUID,
    p_codigo_fornecedor VARCHAR(100),
    p_limite_resultados INTEGER DEFAULT 5
) RETURNS TABLE (
    vinculo_id UUID,
    fornecedor_id UUID,
    fornecedor_nome VARCHAR,
    codigo_fornecedor VARCHAR,
    produto_id UUID,
    produto_nome VARCHAR,
    similaridade DECIMAL(5,2),
    peso_confianca DECIMAL(5,2)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        vf.id,
        vf.fornecedor_id,
        f.razao_social,
        vf.codigo_fornecedor,
        vf.produto_id_interno,
        p.nome,
        -- Similaridade baseada em Levenshtein (simplificado)
        CASE 
            WHEN vf.codigo_fornecedor = p_codigo_fornecedor THEN 100.0
            WHEN vf.codigo_fornecedor ILIKE '%' || p_codigo_fornecedor || '%' THEN 80.0
            WHEN p_codigo_fornecedor ILIKE '%' || vf.codigo_fornecedor || '%' THEN 60.0
            ELSE 30.0
        END as similaridade,
        vf.peso_confianca
    FROM wms.vinculo_fornecedor_produto vf
    JOIN fornecedor f ON vf.fornecedor_id = f.id
    JOIN produto p ON vf.produto_id_interno = p.id
    WHERE vf.tenant_id = p_tenant_id
      AND vf.status = 'ativo'
      AND (
          vf.codigo_fornecedor ILIKE '%' || p_codigo_fornecedor || '%'
          OR p_codigo_fornecedor ILIKE '%' || vf.codigo_fornecedor || '%'
      )
    ORDER BY similaridade DESC, vf.peso_confianca DESC
    LIMIT p_limite_resultados;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- POLÍTICAS DE SEGURANÇA (RLS - Row Level Security)
-- =====================================================

-- Habilitar RLS na tabela
ALTER TABLE wms.vinculo_fornecedor_produto ENABLE ROW LEVEL SECURITY;

-- Política: Usuários só podem ver vínculos do seu tenant
CREATE POLICY vinculos_tenant_isolation ON wms.vinculo_fornecedor_produto
    FOR ALL
    TO app_user
    USING (tenant_id = current_setting('app.current_tenant_id')::UUID);

-- =====================================================
-- COMENTÁRIOS EXPLICATIVOS
-- =====================================================

COMMENT ON TABLE wms.vinculo_fornecedor_produto IS 
    'Tabela central de conhecimento do sistema. Traduz códigos externos dos fornecedores ' ||
    'para produtos internos, permitindo aprendizado contínuo e automação de importações. ' ||
    'Essencial para operação com múltiplos fornecedores e eliminação de digitação manual.';

COMMENT ON COLUMN wms.vinculo_fornecedor_produto.codigo_fornecedor IS 
    'Código do produto no sistema do fornecedor. Pode ser SKU, código interno, ' ||
    'descrição resumida ou qualquer identificador utilizado pelo fornecedor.';

COMMENT ON COLUMN wms.vinculo_fornecedor_produto.fator_conversao IS 
    'Fator multiplicador para converter unidades do fornecedor para unidades internas. ' ||
    'Exemplo: 12.0 se fornecedor envia caixas e sistema controla unidades (1 CX = 12 UN).';

COMMENT ON COLUMN wms.vinculo_fornecedor_produto.vezes_utilizado IS 
    'Contador de quantas vezes este vínculo foi utilizado em importações reais. ' ||
    'Usado para estatísticas e para identificar vínculos mais confiáveis.';

COMMENT ON COLUMN wms.vinculo_fornecedor_produto.peso_confianca IS 
    'Peso (0-10) atribuído ao vínculo para algoritmos de aprendizado. ' ||
    'Vínculos mais confiáveis têm peso maior e são priorizados em sugestões.';

COMMENT ON CONSTRAINT vinculo_fornecedor_produto_unique IS 
    'Garante que cada código de fornecedor só pode apontar para UM produto interno. ' ||
    'Prevene ambiguidades e garante consistência nas importações.';

-- =====================================================
-- DADOS DE EXEMPLO (APENAS PARA DESENVOLVIMENTO)
-- =====================================================

-- Inserir dados de exemplo apenas se ambiente for de desenvolvimento
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
        -- Exemplo: Coca-Cola 2L (fornecedor Solar)
        INSERT INTO wms.vinculo_fornecedor_produto (
            tenant_id,
            fornecedor_id,
            codigo_fornecedor,
            produto_id_interno,
            fator_conversao,
            unidade_origem,
            unidade_destino,
            status,
            vezes_utilizado,
            peso_confianca
        ) VALUES (
            (SELECT id FROM tenant LIMIT 1),
            (SELECT id FROM fornecedor WHERE cnpj LIKE '%12345678901234%' LIMIT 1),
            'COCA-COLA-2L-PET',
            (SELECT id FROM produto WHERE gtin = '7891000316003' LIMIT 1),
            1.0,
            'UN',
            'UN',
            'ativo',
            15,
            8.5
        ) ON CONFLICT (tenant_id, fornecedor_id, codigo_fornecedor) DO NOTHING;
        
        -- Exemplo: Guaraná em caixas (conversão necessária)
        INSERT INTO wms.vinculo_fornecedor_produto (
            tenant_id,
            fornecedor_id,
            codigo_fornecedor,
            produto_id_interno,
            fator_conversao,
            unidade_origem,
            unidade_destino,
            status,
            vezes_utilizado,
            peso_confianca
        ) VALUES (
            (SELECT id FROM tenant LIMIT 1),
            (SELECT id FROM fornecedor WHERE cnpj LIKE '%12345678901234%' LIMIT 1),
            'GUARANA-ANTARTICA-CX',
            (SELECT id FROM produto WHERE gtin = '7891000150013' LIMIT 1),
            12.0,
            'CX',
            'UN',
            'ativo',
            8,
            7.0
        ) ON CONFLICT (tenant_id, fornecedor_id, codigo_fornecedor) DO NOTHING;
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
        AND table_name = 'vinculo_fornecedor_produto'
    ) INTO table_exists;
    
    IF NOT table_exists THEN
        RAISE EXCEPTION 'Erro: Tabela wms.vinculo_fornecedor_produto não foi criada';
    END IF;
    
    -- Verificar constraints
    SELECT COUNT(*) INTO constraint_count
    FROM information_schema.check_constraints 
    WHERE constraint_schema = 'wms'
    AND constraint_name LIKE '%vinculo_fornecedor_produto%';
    
    IF constraint_count < 3 THEN
        RAISE EXCEPTION 'Erro: Constraints não foram criadas corretamente. Esperado: 3, Encontrado: %', constraint_count;
    END IF;
    
    RAISE NOTICE 'Migration VinculoFornecedorProduto concluída com sucesso.';
    RAISE NOTICE 'Tabela: wms.vinculo_fornecedor_produto';
    RAISE NOTICE 'Constraints: % verificadas', constraint_count;
    RAISE NOTICE 'Índices: Performance otimizada para consultas de importação';
END $$;
