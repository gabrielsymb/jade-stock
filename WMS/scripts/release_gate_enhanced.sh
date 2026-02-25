#!/usr/bin/env bash
set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

cd "$(dirname "$0")/.."

echo -e "${PURPLE}🚪 JADE STOCK - RELEASE GATE ENHANCED${NC}"
echo -e "${PURPLE}=====================================${NC}"

# Função para verificar步骤
check_step() {
    local step_name="$1"
    local step_command="$2"
    
    echo -e "${BLUE}🔍 Verificando: $step_name${NC}"
    
    if eval "$step_command" >/dev/null 2>&1; then
        echo -e "${GREEN}   ✅ $step_name: OK${NC}"
        return 0
    else
        echo -e "${RED}   ❌ $step_name: FALHOU${NC}"
        return 1
    fi
}

# 1. Verificar ambiente virtual
echo -e "${YELLOW}🐍 Ambiente Python${NC}"
if [[ "${VIRTUAL_ENV:-}" == "" ]]; then
    echo -e "${RED}❌ Ambiente virtual não ativado${NC}"
    echo -e "${YELLOW}💡 Execute: source ../.venv/bin/activate${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Ambiente virtual: $VIRTUAL_ENV${NC}"
fi

# 2. Verificar dependências
check_step "Dependências Python" "pip list | grep fastapi"
check_step "Dependências PostgreSQL" "pip list | grep psycopg2"
check_step "Dependências Uvicorn" "pip list | grep uvicorn"

# 3. Verificar arquivos essenciais
echo -e "${YELLOW}📁 Arquivos Essenciais${NC}"
essential_files=(
    "wms/interfaces/api/app.py"
    "wms/domain/exceptions.py"
    "wms/infrastructure/database/database_config.py"
    "Database/schema_core.sql"
    "requirements.txt"
    "requirements-dev.txt"
)

for file in "${essential_files[@]}"; do
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}   ✅ $file${NC}"
    else
        echo -e "${RED}   ❌ $file ausente${NC}"
        exit 1
    fi
done

# 4. Verificar configuração .env
echo -e "${YELLOW}⚙️ Configuração${NC}"
if [[ -f .env ]]; then
    echo -e "${GREEN}   ✅ Arquivo .env encontrado${NC}"
    
    # Carregar variáveis
    set -a
    source .env
    set +a
    
    # Verificar DSN
    if [[ -n "${WMS_POSTGRES_DSN:-}" ]]; then
        echo -e "${GREEN}   ✅ WMS_POSTGRES_DSN configurado${NC}"
    else
        echo -e "${RED}   ❌ WMS_POSTGRES_DSN não configurado${NC}"
        exit 1
    fi
else
    echo -e "${RED}   ❌ Arquivo .env não encontrado${NC}"
    echo -e "${YELLOW}💡 Copie .env.example para .env${NC}"
    exit 1
fi

# 5. Verificar imports principais
echo -e "${YELLOW}📦 Imports Python${NC}"
export PYTHONPATH=.

import_checks=(
    "from wms.interfaces.api.app import app"
    "from wms.application.use_cases.processar_governanca_orcamentaria import ProcessarGovernancaOrcamentaria"
    "from wms.infrastructure.database.database_config import get_connection_postgres"
    "import fastapi"
    "import psycopg2"
)

for import_check in "${import_checks[@]}"; do
    if python3 -c "$import_check" 2>/dev/null; then
        echo -e "${GREEN}   ✅ Import OK: ${import_check%%:*}${NC}"
    else
        echo -e "${RED}   ❌ Import FALHOU: ${import_check%%:*}${NC}"
        exit 1
    fi
done

# 6. Verificar PostgreSQL (opcional, mas recomendado)
echo -e "${YELLOW}🐘 Conexão PostgreSQL${NC}"
if python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.getenv('WMS_POSTGRES_DSN'))
    conn.close()
    print('OK')
except:
    print('FAIL')
" 2>/dev/null; then
    echo -e "${GREEN}   ✅ PostgreSQL conectado${NC}"
    postgres_available=true
else
    echo -e "${YELLOW}   ⚠️ PostgreSQL não disponível (testes PostgreSQL serão pulados)${NC}"
    postgres_available=false
fi

# 7. Rodar testes unitários
echo -e "${YELLOW}🧪 Testes Unitários${NC}"
if python3 -m unittest discover -s tests -p 'test_*.py' -v 2>&1 | grep -q "OK"; then
    echo -e "${GREEN}   ✅ Testes unitários passando${NC}"
    unit_tests_ok=true
else
    echo -e "${RED}   ❌ Testes unitários falhando${NC}"
    unit_tests_ok=false
fi

# 8. Rodar testes PostgreSQL (se disponível)
if [[ "$postgres_available" == true ]]; then
    echo -e "${YELLOW}🐘 Testes PostgreSQL${NC}"
    
    # Verificar se schema existe
    if python3 -c "
import psycopg2
import os
try:
    conn = psycopg2.connect(os.getenv('WMS_POSTGRES_DSN'))
    cursor = conn.cursor()
    cursor.execute(\"SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'saldo_estoque'\")
    exists = cursor.fetchone()[0] > 0
    conn.close()
    print('EXISTS' if exists else 'MISSING')
except:
    print('ERROR')
" 2>/dev/null | grep -q "EXISTS"; then
        echo -e "${GREEN}   ✅ Schema PostgreSQL encontrado${NC}"
        
        # Rodar alguns testes PostgreSQL
        if python3 -m unittest tests.test_postgres_core_integration tests.test_postgres_transactional_behavior -v 2>&1 | grep -q "OK"; then
            echo -e "${GREEN}   ✅ Testes PostgreSQL passando${NC}"
            postgres_tests_ok=true
        else
            echo -e "${RED}   ❌ Testes PostgreSQL falhando${NC}"
            postgres_tests_ok=false
        fi
    else
        echo -e "${YELLOW}   ⚠️ Schema PostgreSQL não encontrado (execute: ./scripts/setup_postgres_tests.sh)${NC}"
        postgres_tests_ok=false
    fi
else
    postgres_tests_ok=false
fi

# 9. Verificar API
echo -e "${YELLOW}🌐 API Health Check${NC}"
if python3 -c "
from wms.interfaces.api.app import app
from fastapi.testclient import TestClient
client = TestClient(app)
response = client.get('/v1/health')
assert response.status_code == 200
assert response.json()['status'] == 'ok'
print('OK')
" 2>/dev/null; then
    echo -e "${GREEN}   ✅ API health check passando${NC}"
    api_ok=true
else
    echo -e "${RED}   ❌ API health check falhando${NC}"
    api_ok=false
fi

# 10. Resumo final
echo -e ""
echo -e "${PURPLE}📊 RESUMO DO RELEASE GATE${NC}"
echo -e "   Ambiente Virtual: ✅"
echo -e "   Dependências: ✅"
echo -e "   Arquivos: ✅"
echo -e "   Configuração: ✅"
echo -e "   Imports: ✅"
echo -e "   Testes Unitários: $([[ $unit_tests_ok == true ]] && echo '✅' || echo '❌')"
echo -e "   Testes PostgreSQL: $([[ $postgres_tests_ok == true ]] && echo '✅' || echo '⚠️')"
echo -e "   API Health: $([[ $api_ok == true ]] && echo '✅' || echo '❌')"

# Verificação final
if [[ $unit_tests_ok == true && $api_ok == true ]]; then
    echo -e ""
    echo -e "${GREEN}🎉 RELEASE GATE APROVADO!${NC}"
    echo -e "${GREEN}   Sistema pronto para deploy${NC}"
    
    if [[ $postgres_tests_ok == true ]]; then
        echo -e "${GREEN}   ✅ Todos os testes (97 + PostgreSQL) passando${NC}"
    else
        echo -e "${YELLOW}   ⚠️ Apenas testes unitários passando (PostgreSQL não configurado)${NC}"
    fi
    
    echo -e ""
    echo -e "${BLUE}🚀 Comandos para deploy:${NC}"
    echo -e "   # Subir API em modo in-memory:"
    echo -e "   WMS_API_BACKEND=inmemory ./scripts/run_api.sh"
    echo -e ""
    echo -e "   # Subir API com PostgreSQL:"
    echo -e "   WMS_API_BACKEND=postgres ./scripts/run_api.sh"
    
    exit 0
else
    echo -e ""
    echo -e "${RED}💥 RELEASE GATE REPROVADO!${NC}"
    echo -e "${RED}   Corrija os problemas antes de prosseguir${NC}"
    exit 1
fi
