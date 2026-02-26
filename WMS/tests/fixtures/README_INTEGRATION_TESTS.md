# Testes de Integração - Importação XML NF-e

## Visão Geral

Este diretório contém testes de integração baseados em **dados reais de negócio** para validar o fluxo completo de importação XML NF-e no módulo WMS.

## Cenários de Teste

### 1. Vinculação Perfeita (EAN Existente)
**Arquivo:** `test_xml_import_real_data.py::test_cenario_1_vinculacao_perfeita_ean_existente`

**Cenário Real:**
- Fornecedor: Distribuidora Solar
- Produto: Coca-Cola 2L
- EAN: 7891000316003 (já cadastrado)
- Quantidade: 12 unidades

**Validação:**
- Sistema reconhece automaticamente (MATCHED ≥ 95%)
- Pontuação: EAN (40pts) + Descrição similar (~30pts) = ~70pts
- Nenhuma intervenção manual necessária

### 2. Conversão de Unidades (CX → UN)
**Arquivo:** `test_xml_import_real_data.py::test_cenario_2_vinculacao_parcial_conversao_unidade`

**Cenário Real:**
- Fornecedor envia: 2 CX (caixas) de Guaraná
- Sistema controla: UN (unidades)
- Fator conversão: 1 CX = 12 UN
- Resultado esperado: 24 unidades no estoque

**Validação:**
- Vínculo existente aplicado automaticamente
- Conversão realizada corretamente
- Estoque atualizado com unidades convertidas

### 3. Produto Novo (Sem Vínculo)
**Arquivo:** `test_xml_import_real_data.py::test_cenario_3_produto_novo_sem_vinculo`

**Cenário Real:**
- Novo fornecedor ou produto
- EAN não encontrado no catálogo
- Descrição não corresponde a produtos existentes
- NCM: 22021000 (bebidas)

**Validação:**
- Status: NEW (pontuação < 50)
- Sistema sugere cadastro manual
- Dados pré-preenchidos para facilitar operação

### 4. Registro de Avarias
**Arquivo:** `test_xml_import_real_data.py::test_cenario_4_avarias_na_importacao`

**Cenário Real:**
- NF-e: 12 unidades de Coca-Cola
- Realidade: 3 unidades chegaram danificadas
- Operador registra avaria na importação

**Validação:**
- 12 unidades entram no estoque (obrigação fiscal)
- 3 unidades movidas para quarentena de avarias
- Eventos: `recebimento_xml_confirmado` + `avaria_registrada`

### 5. Idempotência (Retry em Falha)
**Arquivo:** `test_xml_import_real_data.py::test_cenario_5_idempotencia_retrabalho`

**Cenário Real:**
- Primeira requisição: timeout de rede
- Cliente retry com mesmo Idempotency-Key
- Sistema deve evitar duplicação

**Validação:**
- Primeira chamada: 201 Created
- Retry: 200 OK (idempotente)
- Mesmo recebimento_id retornado
- Sem duplicação no banco

## Dados de Teste

### Estrutura de XMLs
Os XMLs seguem o padrão SEFAZ NF-e v4.00 com:
- Cabeçalho completo (emitente, destinatário)
- Itens detalhados (EAN, NCM, quantidades)
- Protocolo de autorização
- Totais e impostos

### Anonimização
Todos os dados sensíveis são anonimizados:
- CNPJs: números fictícios
- Endereços: genéricos
- Chaves de acesso: formatadas mas inválidas

## Como Executar

### Pré-requisitos
```bash
# Ambiente virtual ativado
source .venv/bin/activate

# Dependencies instaladas
pip install -r WMS/requirements-dev.txt

# PostgreSQL rodando
docker compose -f docker-compose.postgres.yml up -d
```

### Executar Todos os Testes
```bash
cd WMS
python -m pytest tests/integration/test_xml_import_real_data.py -v
```

### Executar Cenário Específico
```bash
# Apenas vinculação perfeita
python -m pytest tests/integration/test_xml_import_real_data.py::TestXmlImportRealData::test_cenario_1_vinculacao_perfeita_ean_existente -v

# Com coverage
python -m pytest tests/integration/test_xml_import_real_data.py --cov=wms --cov-report=html
```

### Debug Mode
```bash
# Com prints detalhados
python -m pytest tests/integration/test_xml_import_real_data.py -v -s --tb=long
```

## Fixtures Utilizadas

### `sample_xml_cocacola`
XML NF-e real de Coca-Cola com:
- 2 itens (Coca-Cola e Guaraná)
- Dados completos de fornecedor
- Estrutura SEFAZ válida

### `tenant_test`
Tenant básico para testes:
- ID: UUID gerado
- Nome: "Loja Teste"
- CNPJ: fictício

### `fornecedor_solar`
Fornecedor Distribuidora Solar:
- CNPJ: 12345678901234
- Razão Social completa
- Endereço completo

### `produtos_existentes`
Produtos pré-cadastrados:
- Coca-Cola 2L (EAN: 7891000316003)
- Guaraná Antártica 2L (EAN: 7891000150013)

## Validações Realizadas

### Validação de Schema
- XML bem formado
- Namespace SEFAZ correto
- Campos obrigatórios presentes

### Validação de Negócio
- Chave de acesso única
- CNPJ do emitente válido
- Quantidades positivas
- Valores monetários consistentes

### Validação de Integração
- Comunicação com PostgreSQL
- Transações ACID
- Event Store funcionando
- Idempotency respeitada

## Performance

### Métricas Esperadas
- Parse XML: < 1 segundo
- Análise completa: < 5 segundos
- Confirmação: < 2 segundos
- Total end-to-end: < 10 segundos

### Volume de Teste
- XML médio: ~10KB, 2-5 itens
- XML grande: ~100KB, 50+ itens
- Limite atual: 5MB por upload

## Troubleshooting

### Erros Comuns

**403 Forbidden**
- Verificar token de autenticação
- Confirmar tenant ativo

**422 Unprocessable Entity**
- XML malformado
- Namespace incorreto
- Campos obrigatórios faltando

**409 Conflict**
- NF-e já importada
- Idempotency-Key reutilizada com payload diferente

**500 Internal Server Error**
- Verificar logs da API
- Confirmar PostgreSQL rodando
- Validar migrations aplicadas

### Debug de Banco
```sql
-- Verificar importações recentes
SELECT * FROM wms.xml_importacao 
WHERE tenant_id = 'UUID_TENANT' 
ORDER BY criado_em DESC LIMIT 5;

-- Verificar itens processados
SELECT * FROM wms.xml_importacao_item 
WHERE xml_importacao_id = 'UUID_IMPORTACAO';

-- Verificar vínculos criados
SELECT * FROM wms.vinculo_fornecedor_produto 
WHERE fornecedor_id = 'UUID_FORNECEDOR';
```

## Próximos Passos

1. **Adicionar mais cenários reais**
   - Múltiplos fornecedores
   - Produtos com EAN inválido
   - Unidades complexas (KG, L, M)

2. **Testes de carga**
   - 100 importações simultâneas
   - XMLs grandes (500+ itens)
   - Concorrência de usuários

3. **Testes de borda**
   - XML corrompido
   - Rede instável
   - Banco indisponível

4. **Automatização CI/CD**
   - Execução em pipeline
   - Geração de relatórios
   - Performance baseline
