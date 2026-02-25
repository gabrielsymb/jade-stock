# 🚀 Scripts de Automação - Jade Stock WMS

Este diretório contém scripts para automação de testes, setup e deploy do sistema Jade Stock WMS.

## 📋 Índice

- [🧪 Testes](#-testes)
- [🐘 PostgreSQL Setup](#-postgresql-setup)
- [🚪 Release Gate](#-release-gate)
- [🚀 Deploy](#-deploy)

---

## 🧪 Testes

### `run_all_tests_with_postgres.sh`
**Propósito**: Executar suite completa de testes (unitários + PostgreSQL)

**Uso**:
```bash
./scripts/run_all_tests_with_postgres.sh
```

**O que faz**:
1. ✅ Verifica configuração .env
2. ✅ Testa conexão PostgreSQL
3. ✅ Aplica schema do banco (se necessário)
4. ✅ Roda todos os testes unitários (67 testes)
5. ✅ Roda todos os testes PostgreSQL (30 testes)
6. ✅ Gera relatório detalhado

**Pré-requisitos**:
- PostgreSQL rodando (veja setup abaixo)
- Arquivo `.env` configurado
- Dependências Python instaladas

### `run_sql_tests.sh` (existente)
**Propósito**: Executar apenas testes de integração PostgreSQL

**Uso**:
```bash
./scripts/run_sql_tests.sh
```

---

## 🐘 PostgreSQL Setup

### `setup_postgres_tests.sh`
**Propósito**: Configurar ambiente PostgreSQL para testes

**Uso**:
```bash
./scripts/setup_postgres_tests.sh
```

**O que faz**:
1. ✅ Verifica Docker/Docker Compose
2. ✅ Cria arquivo `.env` (se não existir)
3. ✅ Inicia container PostgreSQL
4. ✅ Aguarda PostgreSQL ficar pronto
5. ✅ Aplica schema do banco
6. ✅ Verifica tabelas criadas
7. ✅ Testa conexão Python

**Resultado final**:
- PostgreSQL rodando em `localhost:5432`
- Schema aplicado e tabelas criadas
- Conexão Python validada

---

## 🚪 Release Gate

### `release_gate_enhanced.sh`
**Propósito**: Validação completa pré-deploy

**Uso**:
```bash
./scripts/release_gate_enhanced.sh
```

**Verificações**:
1. ✅ Ambiente virtual ativado
2. ✅ Dependências instaladas
3. ✅ Arquivos essenciais presentes
4. ✅ Configuração .env OK
5. ✅ Imports Python funcionando
6. ✅ Testes unitários passando
7. ✅ Testes PostgreSQL (se disponível)
8. ✅ API health check

**Status final**:
- ✅ **APROVADO**: Sistema pronto para deploy
- ❌ **REPROVADO**: Corrigir problemas antes de prosseguir

---

## 🚀 Deploy

### `run_api.sh` (existente)
**Propósito**: Subir API em modo desenvolvimento

**Uso**:
```bash
# Modo in-memory (padrão)
./scripts/run_api.sh

# Modo PostgreSQL
WMS_API_BACKEND=postgres ./scripts/run_api.sh
```

---

## 🔄 Fluxo Recomendado

### Para Desenvolvimento Local

```bash
# 1. Setup inicial (uma vez)
./scripts/setup_postgres_tests.sh

# 2. Release gate (antes de cada commit importante)
./scripts/release_gate_enhanced.sh

# 3. Testes completos (antes de PR)
./scripts/run_all_tests_with_postgres.sh

# 4. Subir API para desenvolvimento
./scripts/run_api.sh
```

### Para CI/CD (GitHub Actions)

O workflow `.github/workflows/ci-cd.yml` executa automaticamente:

1. **Setup**: Python + PostgreSQL
2. **Testes Unitários**: 67 testes in-memory
3. **Testes PostgreSQL**: 30 testes de integração
4. **API Health Check**: Valida endpoints
5. **Code Quality**: Lint e formatação
6. **Deploy**: Automatico em main (se tudo passar)

---

## 📊 Status dos Testes

### Testes Unitários (67 testes)
- `test_registrar_movimentacao_estoque`: 6 testes
- `test_registrar_ajuste_estoque`: 6 testes
- `test_registrar_avaria_estoque`: 6 testes
- `test_registrar_recebimento`: 8 testes
- `test_registrar_inventario_ciclico`: 3 testes
- `test_registrar_politica_kanban`: 6 testes
- `test_processar_curva_abcd`: 4 testes
- `test_processar_giro_estoque`: 5 testes
- `test_processar_sazonalidade_operacional`: 4 testes
- `test_processar_governanca_orcamentaria`: 7 testes
- `test_api_inmemory`: 12 testes

### Testes PostgreSQL (30 testes)
- `test_postgres_core_integration`: 4 testes
- `test_postgres_transactional_behavior`: 6 testes
- `test_postgres_curva_abcd_integration`: 4 testes
- `test_postgres_giro_integration`: 4 testes
- `test_postgres_governanca_orcamentaria_integration`: 4 testes
- `test_postgres_inventario_integration`: 3 testes
- `test_postgres_kanban_integration`: 3 testes
- `test_postgres_sazonalidade_integration`: 2 testes

**Total**: 97 testes automatizados

---

## 🛠️ Troubleshooting

### PostgreSQL não conecta
```bash
# Verificar container
docker compose -f docker-compose.postgres.yml ps

# Verificar logs
docker compose -f docker-compose.postgres.yml logs postgres

# Reiniciar
docker compose -f docker-compose.postgres.yml restart
```

### Testes falhando
```bash
# Verificar ambiente virtual
echo $VIRTUAL_ENV

# Reinstalar dependências
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Verificar PYTHONPATH
export PYTHONPATH=.
```

### API não sobe
```bash
# Verificar porta
lsof -i :8001

# Verificar logs
./scripts/run_api.sh
```

---

## 📝 Variáveis de Ambiente

Essenciais para `.env`:
```bash
WMS_POSTGRES_USER=wms
WMS_POSTGRES_PASSWORD=wms
WMS_POSTGRES_DB=wms
WMS_POSTGRES_PORT=5432
WMS_POSTGRES_DSN=postgresql://wms:wms@localhost:5432/wms

WMS_API_BACKEND=inmemory  # ou postgres
WMS_API_TENANT_ID=loja_demo
WMS_API_LOG_LEVEL=warning
WMS_API_ACCESS_LOG=false
```

---

## 🎯 Próximos Passos

1. **Configurar PostgreSQL**: `./scripts/setup_postgres_tests.sh`
2. **Validar sistema**: `./scripts/release_gate_enhanced.sh`
3. **Rodar todos testes**: `./scripts/run_all_tests_with_postgres.sh`
4. **Fazer PR**: CI/CD vai validar automaticamente
5. **Merge**: Deploy automático para produção

---

*Última atualização: 2026-02-25*
