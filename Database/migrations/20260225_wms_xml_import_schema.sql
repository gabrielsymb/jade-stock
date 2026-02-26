-- =====================================================
-- Jade-Stock WMS: Schema de Importação XML NF-e
-- Migration: 20260225_wms_xml_import_schema.sql
-- Responsabilidade: Importação de NF-e com vinculação inteligente
-- =====================================================

-- Schema WMS já deve existir (ver migrations anteriores)
-- Este arquivo adiciona tabelas específicas para importação XML

-- =====================================================
-- TABELA DE VÍNCULOS FORNECEDOR-PRODUTO
-- =====================================================
-- Propósito: Traduzir códigos externos para produtos internos
-- Permite aprendizado contínuo e múltiplos fornecedores por produto

CREATE TABLE IF NOT EXISTS wms.vinculo_fornecedor_produto (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id),
    fornecedor_id UUID NOT NULL REFERENCES fornecedor(id),
    codigo_fornecedor VARCHAR(100) NOT NULL,
    produto_id_interno UUID NOT NULL REFERENCES produto(id),
    
    -- Conversão de unidades (ex: 1 CX = 12 UN)
    fator_conversao DECIMAL(10,4) NOT NULL DEFAULT 1.0,
    unidade_origem VARCHAR(10),
    unidade_destino VARCHAR(10),
    
    -- Metadados de auditoria e aprendizado
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    ultima_importacao TIMESTAMP,
    criado_por UUID REFERENCES usuario(id),
    
    -- Estatísticas de uso
    vezes_utilizado INTEGER DEFAULT 0,
    
    -- Constraints de integridade
    CONSTRAINT vinculo_fornecedor_produto_unique 
        UNIQUE(tenant_id, fornecedor_id, codigo_fornecedor),
    CONSTRAINT fator_conversao_positivo 
        CHECK (fator_conversao > 0)
);

-- Índices para performance nas consultas de importação
CREATE INDEX IF NOT EXISTS idx_vinculo_fornecedor_produto_fornecedor 
    ON wms.vinculo_fornecedor_produto(fornecedor_id, codigo_fornecedor);
CREATE INDEX IF NOT EXISTS idx_vinculo_fornecedor_produto_produto 
    ON wms.vinculo_fornecedor_produto(produto_id_interno);
CREATE INDEX IF NOT EXISTS idx_vinculo_fornecedor_produto_tenant 
    ON wms.vinculo_fornecedor_produto(tenant_id);

-- =====================================================
-- TABELA DE IMPORTAÇÕES XML
-- =====================================================
-- Propósito: Controlar o ciclo de vida de importações XML
-- Mantém rastreabilidade completa e previne duplicidades

CREATE TABLE IF NOT EXISTS wms.xml_importacao (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id),
    
    -- Metadados da NF-e
    chave_acesso VARCHAR(44) NOT NULL UNIQUE,
    numero_nota VARCHAR(9) NOT NULL,
    serie VARCHAR(3) NOT NULL,
    data_emissao DATE NOT NULL,
    data_recebimento TIMESTAMP DEFAULT NOW(),
    
    -- Dados do emitente
    emitente_cnpj VARCHAR(14) NOT NULL,
    emitente_razao_social VARCHAR(150) NOT NULL,
    emitente_nome_fantasia VARCHAR(100),
    
    -- Controle do processo
    status VARCHAR(20) NOT NULL DEFAULT 'analisando' 
        CHECK (status IN ('analisando', 'confirmado', 'cancelado', 'erro')),
    
    -- Arquivo XML original
    xml_conteudo TEXT NOT NULL,
    xml_hash VARCHAR(64) NOT NULL UNIQUE, -- SHA-256 para integridade
    
    -- Auditoria
    criado_por UUID REFERENCES usuario(id),
    criado_em TIMESTAMP DEFAULT NOW(),
    atualizado_em TIMESTAMP DEFAULT NOW(),
    confirmado_em TIMESTAMP,
    
    -- Idempotência
    correlation_id VARCHAR(100),
    
    -- Resumo da importação
    total_itens INTEGER DEFAULT 0,
    total_valor DECIMAL(15,2) DEFAULT 0,
    itens_vinculados_automaticamente INTEGER DEFAULT 0,
    itens_ambiguos INTEGER DEFAULT 0,
    itens_novos INTEGER DEFAULT 0,
    itens_avariados INTEGER DEFAULT 0
);

-- Índices para performance e consultas
CREATE INDEX IF NOT EXISTS idx_xml_importacao_chave_acesso 
    ON wms.xml_importacao(chave_acesso);
CREATE INDEX IF NOT EXISTS idx_xml_importacao_tenant_status 
    ON wms.xml_importacao(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_xml_importacao_emitente_cnpj 
    ON wms.xml_importacao(emitente_cnpj);
CREATE INDEX IF NOT EXISTS idx_xml_importacao_data_emissao 
    ON wms.xml_importacao(data_emissao);

-- =====================================================
-- TABELA DE ITENS DA IMPORTAÇÃO XML
-- =====================================================
-- Propósito: Detalhar cada item da NF-e e sua vinculação

CREATE TABLE IF NOT EXISTS wms.xml_importacao_item (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    xml_importacao_id UUID NOT NULL REFERENCES wms.xml_importacao(id) ON DELETE CASCADE,
    
    -- Dados originais do XML
    item_numero INTEGER NOT NULL,
    codigo_fornecedor VARCHAR(100) NOT NULL,
    descricao_fornecedor VARCHAR(300) NOT NULL,
    gtin VARCHAR(14),
    ncm VARCHAR(8),
    
    -- Quantidades e valores
    quantidade_comercial DECIMAL(15,4) NOT NULL,
    unidade_comercial VARCHAR(3) NOT NULL,
    valor_unitario DECIMAL(15,4) NOT NULL,
    valor_total DECIMAL(15,2) NOT NULL,
    
    -- Vinculação com produto interno
    produto_id_interno UUID REFERENCES produto(id),
    status_vinculacao VARCHAR(20) NOT NULL DEFAULT 'NEW'
        CHECK (status_vinculacao IN ('MATCHED', 'AMBIGUOUS', 'NEW')),
    pontuacao_vinculacao DECIMAL(5,2),
    
    -- Decisão do operador (pós-análise)
    quantidade_avariada DECIMAL(15,4) DEFAULT 0,
    endereco_destino VARCHAR(50),
    
    -- Controle de processamento
    processado_em TIMESTAMP,
    processado_por UUID REFERENCES usuario(id),
    
    -- Constraints
    CONSTRAINT xml_item_quantidade_avariada_valida 
        CHECK (quantidade_avariada <= quantidade_comercial),
    CONSTRAINT xml_item_pontuacao_valida 
        CHECK (pontuacao_vinculacao BETWEEN 0 AND 100)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_xml_importacao_item_importacao 
    ON wms.xml_importacao_item(xml_importacao_id);
CREATE INDEX IF NOT EXISTS idx_xml_importacao_item_produto 
    ON wms.xml_importacao_item(produto_id_interno);
CREATE INDEX IF NOT EXISTS idx_xml_importacao_item_status 
    ON wms.xml_importacao_item(status_vinculacao);
CREATE INDEX IF NOT EXISTS idx_xml_importacao_item_codigo_fornecedor 
    ON wms.xml_importacao_item(codigo_fornecedor);

-- =====================================================
-- TABELA DE HISTÓRICO DE VÍNCULOS (APRENDIZADO)
-- =====================================================
-- Propósito: Registrar decisões de vinculação para aprendizado futuro

CREATE TABLE IF NOT EXISTS wms.vinculo_historico (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenant(id),
    
    -- Contexto da decisão
    fornecedor_id UUID NOT NULL REFERENCES fornecedor(id),
    codigo_fornecedor VARCHAR(100) NOT NULL,
    descricao_fornecedor VARCHAR(300) NOT NULL,
    
    -- Decisão tomada
    produto_id_interno UUID NOT NULL REFERENCES produto(id),
    tipo_decisao VARCHAR(20) NOT NULL 
        CHECK (tipo_decisao IN ('vinculo_manual', 'confirmacao_automatica', 'correcao_vinculo')),
    
    -- Metadados para aprendizado
    xml_importacao_id UUID REFERENCES wms.xml_importacao(id),
    peso_decisao DECIMAL(3,2) DEFAULT 1.0, -- Peso para algoritmo futuro
    
    -- Auditoria
    decidido_em TIMESTAMP DEFAULT NOW(),
    decidido_por UUID REFERENCES usuario(id),
    
    -- Evita duplicação de decisões idênticas
    CONSTRAINT vinculo_historico_unique 
        UNIQUE(tenant_id, fornecedor_id, codigo_fornecedor, produto_id_interno, decidido_em)
);

-- Índices para consultas de aprendizado
CREATE INDEX IF NOT EXISTS idx_vinculo_historico_fornecedor_codigo 
    ON wms.vinculo_historico(fornecedor_id, codigo_fornecedor);
CREATE INDEX IF NOT EXISTS idx_vinculo_historico_produto 
    ON wms.vinculo_historico(produto_id_interno);
CREATE INDEX IF NOT EXISTS idx_vinculo_historico_decisao 
    ON wms.vinculo_historico(tipo_decisao);

-- =====================================================
-- VIEWS PARA CONSULTAS CONVENIENTES
-- =====================================================

-- View de importações recentes com status
CREATE OR REPLACE VIEW wms.v_importacoes_recentes AS
SELECT 
    i.id,
    i.tenant_id,
    i.chave_acesso,
    i.numero_nota,
    i.emitente_razao_social,
    i.status,
    i.total_itens,
    i.total_valor,
    i.criado_em,
    COUNT(it.id) as itens_processados,
    COUNT(CASE WHEN it.status_vinculacao = 'MATCHED' THEN 1 END) as itens_match,
    COUNT(CASE WHEN it.status_vinculacao = 'AMBIGUOUS' THEN 1 END) as itens_ambiguous,
    COUNT(CASE WHEN it.status_vinculacao = 'NEW' THEN 1 END) as itens_new
FROM wms.xml_importacao i
LEFT JOIN wms.xml_importacao_item it ON i.id = it.xml_importacao_id
WHERE i.criado_em >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY i.id, i.tenant_id, i.chave_acesso, i.numero_nota, 
         i.emitente_razao_social, i.status, i.total_itens, 
         i.total_valor, i.criado_em
ORDER BY i.criado_em DESC;

-- View de vínculos mais utilizados
CREATE OR REPLACE VIEW wms.v_vinculos_mais_utilizados AS
SELECT 
    vf.id,
    vf.tenant_id,
    f.razao_social as fornecedor_nome,
    vf.codigo_fornecedor,
    p.nome as produto_nome,
    vf.fator_conversao,
    vf.vezes_utilizado,
    vf.ultima_importacao,
    vf.criado_em
FROM wms.vinculo_fornecedor_produto vf
JOIN fornecedor f ON vf.fornecedor_id = f.id
JOIN produto p ON vf.produto_id_interno = p.id
WHERE vf.vezes_utilizado > 0
ORDER BY vf.vezes_utilizado DESC;

-- =====================================================
-- TRIGGERS PARA AUDITORIA
-- =====================================================

-- Atualiza campo atualizado_em
CREATE OR REPLACE FUNCTION wms.fn_atualizar_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.atualizado_em = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para vinculo_fornecedor_produto
CREATE TRIGGER trg_vinculo_fornecedor_produto_atualizado
    BEFORE UPDATE ON wms.vinculo_fornecedor_produto
    FOR EACH ROW EXECUTE FUNCTION wms.fn_atualizar_timestamp();

-- Trigger para xml_importacao
CREATE TRIGGER trg_xml_importacao_atualizado
    BEFORE UPDATE ON wms.xml_importacao
    FOR EACH ROW EXECUTE FUNCTION wms.fn_atualizar_timestamp();

-- =====================================================
-- COMENTÁRIOS EXPLICATIVOS
-- =====================================================

COMMENT ON TABLE wms.vinculo_fornecedor_produto IS 
    'Tabela N:N que traduz códigos de fornecedores para produtos internos. ' ||
    'Essencial para aprendizado contínuo e importação automática.';

COMMENT ON TABLE wms.xml_importacao IS 
    'Controla o ciclo de vida completo de importações XML NF-e. ' ||
    'Previne duplicidades via chave_acesso e xml_hash.';

COMMENT ON TABLE wms.xml_importacao_item IS 
    'Detalha cada item da NF-e com sua vinculação e decisão final. ' ||
    'Permite rastreabilidade completa da linha do produto.';

COMMENT ON TABLE wms.vinculo_historico IS 
    'Registro histórico de decisões de vinculação para alimentar ' ||
    'algoritmo de aprendizado e melhorar acurácia futura.';

-- =====================================================
-- DADOS DE EXEMPLO (APENAS PARA DESENVOLVIMENTO)
-- =====================================================

-- Inserir dados apenas se ambiente for de desenvolvimento
-- Isso deve ser removido ou comentado em produção

-- Exemplo de fornecedor (se não existir)
INSERT INTO fornecedor (id, tenant_id, cnpj, razao_social, nome_fantasia, ativo)
SELECT 
    gen_random_uuid(),
    (SELECT id FROM tenant LIMIT 1),
    '12345678901234',
    'Distribuidora Bebidas Solar LTDA',
    'Solar Distribuidora',
    true
WHERE NOT EXISTS (SELECT 1 FROM fornecedor WHERE cnpj = '12345678901234')
LIMIT 1;

-- =====================================================
-- VALIDAÇÕES FINAIS
-- =====================================================

-- Verificar se todas as tabelas foram criadas
DO $$
DECLARE
    table_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO table_count
    FROM information_schema.tables 
    WHERE table_schema = 'wms' 
    AND table_name IN ('vinculo_fornecedor_produto', 'xml_importacao', 'xml_importacao_item', 'vinculo_historico');
    
    IF table_count < 4 THEN
        RAISE EXCEPTION 'Erro: Nem todas as tabelas foram criadas. Esperado: 4, Encontrado: %', table_count;
    END IF;
    
    RAISE NOTICE 'Migration XML Import concluída com sucesso. % tabelas criadas.', table_count;
END $$;
