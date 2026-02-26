#!/usr/bin/env bash
set -euo pipefail

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

cd "$(dirname "$0")/.."
PROJECT_DIR="$(pwd)"
SCHEMA_CORE_PATH="$PROJECT_DIR/../Database/schema_core.sql"

echo -e "${BLUE}🐘 Setup PostgreSQL para Testes do Jade Stock${NC}"
echo -e "${BLUE}=============================================${NC}"

# 1. Verificar Docker
echo -e "${YELLOW}🐳 Verificando Docker...${NC}"
if ! command -v docker &> /dev/null; then
  echo -e "${RED}❌ Docker não encontrado. Instale Docker primeiro.${NC}"
  exit 1
fi

if ! command -v docker compose &> /dev/null; then
  echo -e "${RED}❌ Docker Compose não encontrado. Instale Docker Compose primeiro.${NC}"
  exit 1
fi

echo -e "${GREEN}✅ Docker e Docker Compose encontrados${NC}"

# 2. Verificar .env
echo -e "${YELLOW}📋 Verificando configuração .env...${NC}"
if [[ ! -f .env ]]; then
  echo -e "${YELLOW}📝 Criando .env a partir de .env.example...${NC}"
  cp .env.example .env
  echo -e "${GREEN}✅ Arquivo .env criado${NC}"
else
  echo -e "${GREEN}✅ Arquivo .env já existe${NC}"
fi

# 3. Parar containers existentes
echo -e "${YELLOW}🛑 Parando containers PostgreSQL existentes...${NC}"
docker compose -f docker-compose.postgres.yml down --remove-orphans 2>/dev/null || true

# 4. Iniciar PostgreSQL
echo -e "${YELLOW}🚀 Iniciando PostgreSQL...${NC}"
docker compose -f docker-compose.postgres.yml up -d

# 5. Aguardar PostgreSQL estar pronto
echo -e "${YELLOW}⏳ Aguardando PostgreSQL ficar pronto...${NC}"
max_attempts=30
attempt=1

while [[ $attempt -le $max_attempts ]]; do
  if docker compose -f docker-compose.postgres.yml exec -T postgres pg_isready -U wms &>/dev/null; then
    echo -e "${GREEN}✅ PostgreSQL está pronto!${NC}"
    break
  fi
  
  echo -e "${YELLOW}   Tentativa $attempt/$max_attempts...${NC}"
  sleep 2
  ((attempt++))
done

if [[ $attempt -gt $max_attempts ]]; then
  echo -e "${RED}❌ PostgreSQL não ficou pronto a tempo${NC}"
  echo -e "${YELLOW}💡 Verifique os logs: docker compose -f docker-compose.postgres.yml logs postgres${NC}"
  exit 1
fi

# 6. Aplicar schema
echo -e "${YELLOW}🗄️ Aplicando schema do banco...${NC}"
if [[ -f "$SCHEMA_CORE_PATH" ]]; then
  # Copiar schema para dentro do container
  docker compose -f docker-compose.postgres.yml cp "$SCHEMA_CORE_PATH" postgres:/tmp/schema_core.sql
  
  # Aplicar schema
  docker compose -f docker-compose.postgres.yml exec -T postgres psql -U wms -d wms -f /tmp/schema_core.sql
  
  echo -e "${GREEN}✅ Schema aplicado com sucesso${NC}"
else
  echo -e "${YELLOW}⚠️ Arquivo $SCHEMA_CORE_PATH não encontrado${NC}"
fi

# 7. Verificar tabelas
echo -e "${YELLOW}🔍 Verificando tabelas criadas...${NC}"
tables=$(docker compose -f docker-compose.postgres.yml exec -T postgres psql -U wms -d wms -t -c "
  SELECT COUNT(*) 
  FROM information_schema.tables 
  WHERE table_schema = 'public' 
  AND table_name IN ('saldo_estoque', 'movimentacao_estoque', 'event_store');
" | tr -d ' ')

if [[ $tables -ge 3 ]]; then
  echo -e "${GREEN}✅ Tabelas essenciais criadas ($tables tabelas encontradas)${NC}"
else
  echo -e "${RED}❌ Tabelas essenciais não encontradas ($tables tabelas encontradas)${NC}"
  exit 1
fi

# 8. Testar conexão Python
echo -e "${YELLOW}🐍 Testando conexão Python...${NC}"
export PYTHONPATH=.
set -a
source .env
set +a

if python3 -c "
import psycopg2
import os

try:
    dsn = os.getenv('WMS_POSTGRES_DSN')
    conn = psycopg2.connect(dsn)
    cursor = conn.cursor()
    
    # Testar consulta simples
    cursor.execute('SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = %s', ('public',))
    table_count = cursor.fetchone()[0]
    
    print(f'✅ Conexão Python funcionando! {table_count} tabelas encontradas')
    
    conn.close()
except Exception as e:
    print(f'❌ Erro na conexão Python: {e}')
    exit(1)
"; then
  echo -e "${GREEN}✅ Conexão Python validada${NC}"
else
  echo -e "${RED}❌ Falha na conexão Python${NC}"
  exit 1
fi

# 9. Resumo final
echo -e "${BLUE}📊 RESUMO DO SETUP${NC}"
echo -e "   ✅ Docker: OK"
echo -e "   ✅ PostgreSQL: Rodando"
echo -e "   ✅ Schema: Aplicado"
echo -e "   ✅ Tabelas: Criadas"
echo -e "   ✅ Python: Conectado"

echo -e ""
echo -e "${GREEN}🎉 Setup PostgreSQL concluído com sucesso!${NC}"
echo -e ""
echo -e "${BLUE}🧪 Para rodar os testes:${NC}"
echo -e "   ./scripts/run_all_tests_with_postgres.sh"
echo -e ""
echo -e "${BLUE}🐘 Para rodar apenas testes SQL:${NC}"
echo -e "   ./scripts/run_sql_tests.sh"
echo -e ""
echo -e "${BLUE}🛑 Para parar PostgreSQL:${NC}"
echo -e "   docker compose -f docker-compose.postgres.yml down"
