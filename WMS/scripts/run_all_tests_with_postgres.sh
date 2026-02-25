#!/usr/bin/env bash
set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

cd "$(dirname "$0")/.."

echo -e "${BLUE}🚀 Iniciando suite completa de testes com PostgreSQL...${NC}"

# 1. Verificar se .env existe e carregar variáveis
if [[ -f .env ]]; then
  echo -e "${YELLOW}📋 Carregando variáveis do .env...${NC}"
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
else
  echo -e "${RED}❌ Erro: Arquivo .env não encontrado.${NC}"
  echo -e "${YELLOW}💡 Copie .env.example para .env e configure as variáveis.${NC}"
  exit 1
fi

# 2. Verificar DSN PostgreSQL
if [[ -z "${WMS_POSTGRES_DSN:-}" ]]; then
  echo -e "${RED}❌ Erro: WMS_POSTGRES_DSN não definido.${NC}"
  exit 1
fi

echo -e "${GREEN}✅ DSN PostgreSQL configurado: ${WMS_POSTGRES_DSN}${NC}"

# 3. Verificar se PostgreSQL está rodando
echo -e "${BLUE}🔍 Verificando conexão com PostgreSQL...${NC}"
if ! python3 -c "
import psycopg2
import os
dsn = os.getenv('WMS_POSTGRES_DSN')
try:
    conn = psycopg2.connect(dsn)
    conn.close()
    print('✅ Conexão PostgreSQL estabelecida')
except Exception as e:
    print(f'❌ Falha na conexão: {e}')
    exit(1)
" 2>/dev/null; then
  echo -e "${RED}❌ Falha na conexão com PostgreSQL${NC}"
  echo -e "${YELLOW}💡 Verifique se o container está rodando: docker compose -f docker-compose.postgres.yml ps${NC}"
  exit 1
fi

# 4. Aplicar schema do banco (se necessário)
echo -e "${BLUE}🗄️ Aplicando schema do banco...${NC}"
if [[ -f "Database/schema_core.sql" ]]; then
  python3 -c "
import psycopg2
import os

dsn = os.getenv('WMS_POSTGRES_DSN')
try:
    conn = psycopg2.connect(dsn)
    cursor = conn.cursor()
    
    # Verificar se tabelas existem
    cursor.execute(\"\"\"
        SELECT COUNT(*) FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'saldo_estoque'
    \"\"\")
    tables_exist = cursor.fetchone()[0] > 0
    
    if not tables_exist:
        print('📝 Aplicando schema_core.sql...')
        with open('Database/schema_core.sql', 'r') as f:
            cursor.execute(f.read())
        conn.commit()
        print('✅ Schema aplicado com sucesso')
    else:
        print('✅ Schema já existe no banco')
    
    conn.close()
except Exception as e:
    print(f'❌ Erro ao aplicar schema: {e}')
    exit(1)
"
else
  echo -e "${YELLOW}⚠️ Arquivo Database/schema_core.sql não encontrado${NC}"
fi

# 5. Rodar testes unitários (in-memory)
echo -e "${BLUE}🧪 Rodando testes unitários (in-memory)...${NC}"
unit_test_result=0
python3 -m unittest discover -s tests -p 'test_*.py' -v 2>&1 | grep -E "(test_|OK|FAILED|ERROR|skipped|Ran)" || unit_test_result=$?

if [[ $unit_test_result -eq 0 ]]; then
  echo -e "${GREEN}✅ Testes unitários passaram${NC}"
else
  echo -e "${RED}❌ Testes unitários falharam${NC}"
fi

# 6. Rodar testes de integração PostgreSQL
echo -e "${BLUE}🐘 Rodando testes de integração PostgreSQL...${NC}"
integration_test_result=0

# Lista de todos os testes PostgreSQL
postgres_tests=(
  "tests.test_postgres_core_integration"
  "tests.test_postgres_transactional_behavior"
  "tests.test_postgres_curva_abcd_integration"
  "tests.test_postgres_giro_integration"
  "tests.test_postgres_governanca_orcamentaria_integration"
  "tests.test_postgres_inventario_integration"
  "tests.test_postgres_kanban_integration"
  "tests.test_postgres_sazonalidade_integration"
)

for test_module in "${postgres_tests[@]}"; do
  echo -e "${BLUE}   📝 Executando $test_module...${NC}"
  if python3 -m unittest "$test_module" -v; then
    echo -e "${GREEN}   ✅ $test_module passou${NC}"
  else
    echo -e "${RED}   ❌ $test_module falhou${NC}"
    integration_test_result=1
  fi
done

# 7. Resumo final
echo -e "${BLUE}📊 RESUMO DOS TESTES${NC}"
echo -e "   Testes Unitários: $([[ $unit_test_result -eq 0 ]] && echo '✅ PASSOU' || echo '❌ FALHOU')"
echo -e "   Testes PostgreSQL: $([[ $integration_test_result -eq 0 ]] && echo '✅ PASSOU' || echo '❌ FALHOU')"

if [[ $unit_test_result -eq 0 && $integration_test_result -eq 0 ]]; then
  echo -e "${GREEN}🎉 TODOS OS TESTES PASSARAM! Sistema pronto para produção.${NC}"
  exit 0
else
  echo -e "${RED}💥 ALGUNS TESTES FALHARAM! Verifique os erros acima.${NC}"
  exit 1
fi
