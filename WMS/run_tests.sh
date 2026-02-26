#!/bin/bash

# Script para execução dos testes XML no ambiente Crostini
# Jade Stock - WMS Module

set -e  # Parar em caso de erro

echo "🚀 Iniciando execução dos testes XML - Jade Stock WMS"
echo "=================================================="

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Verificar se estamos no diretório correto
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}❌ Erro: Execute este script do diretório WMS${NC}"
    echo "Navegue até: /home/yakuzaa/meus_projetos/Jade-stock/WMS"
    exit 1
fi

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 não encontrado${NC}"
    exit 1
fi

# Verificar PostgreSQL
if ! pg_isready -q; then
    echo -e "${YELLOW}⚠️  PostgreSQL não está rodando. Tentando iniciar...${NC}"
    sudo service postgresql start || {
        echo -e "${RED}❌ Não foi possível iniciar o PostgreSQL${NC}"
        echo "Verifique se o serviço está instalado e configurado."
        exit 1
    }
fi

echo -e "${BLUE}📦 Instalando dependências...${NC}"

# Instalar dependências do projeto
pip3 install -r requirements.txt

# Instalar dependências de teste
pip3 install -r requirements-test.txt

echo -e "${BLUE}🗄️  Configurando banco de dados de teste...${NC}"

# Criar banco de dados de teste se não existir
sudo -u postgres psql -c "CREATE DATABASE jadestock_test;" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  Banco jadestock_test já existe${NC}"
}

# Verificar se as variáveis de ambiente estão configuradas
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  Arquivo .env não encontrado. Criando configuração padrão...${NC}"
    cat > .env << EOF
# Configuração de banco de dados - Testes
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/jadestock_test
ASYNC_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/jadestock_test

# Configurações da aplicação
DEBUG=true
LOG_LEVEL=DEBUG
TENANT_ID=default
EOF
    echo -e "${GREEN}✅ Arquivo .env criado${NC}"
fi

echo -e "${BLUE}🧹 Limpando testes anteriores...${NC}"

# Limpar arquivos de cache do pytest
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true

echo -e "${BLUE}🔧 Executando migrações (se necessário)...${NC}"

# Executar migrações se existirem
if [ -d "alembic" ]; then
    export DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/jadestock_test"
    export ASYNC_DATABASE_URL="postgresql+asyncpg://postgres:postgres@localhost:5432/jadestock_test"
    alembic upgrade head || {
        echo -e "${YELLOW}⚠️  Não foi possível executar migrações (pode ser normal em ambiente de teste)${NC}"
    }
fi

echo -e "${BLUE}🧪 Executando testes XML...${NC}"

# Função para executar um arquivo de teste específico
run_test_file() {
    local test_file=$1
    local description=$2
    
    echo -e "\n${BLUE}📋 Testando: ${description}${NC}"
    echo "Arquivo: $test_file"
    echo "----------------------------------------"
    
    if python3 -m pytest "$test_file" -v --tb=short; then
        echo -e "${GREEN}✅ $description - PASSOU${NC}"
        return 0
    else
        echo -e "${RED}❌ $description - FALHOU${NC}"
        return 1
    fi
}

# Contador de testes
total_tests=0
passed_tests=0
failed_tests=0

# Executar testes individuais
echo -e "\n${YELLOW}🎯 Executando testes individuais...${NC}"

run_test_file "tests/test_xml_analise_real.py" "Análise de XML Real" && ((passed_tests++)) || ((failed_tests++))
((total_tests++))

run_test_file "tests/integration/test_xml_import_real_data.py" "Importação XML Dados Reais" && ((passed_tests++)) || ((failed_tests++))
((total_tests++))

run_test_file "tests/test_xml_confirmacao_idempotencia.py" "Confirmação Idempotência" && ((passed_tests++)) || ((failed_tests++))
((total_tests++))

echo -e "\n${BLUE}🔍 Executando testes específicos...${NC}"

# Executar testes específicos que estavam falhando
echo -e "\n${YELLOW}📋 Testando: Health Check do endpoint${NC}"
if python3 -m pytest "tests/test_xml_analise_real.py::TestXMLAnaliseReal::test_endpoint_health_check" -v --tb=short; then
    echo -e "${GREEN}✅ Health Check - PASSOU${NC}"
    ((passed_tests++))
else
    echo -e "${RED}❌ Health Check - FALHOU${NC}"
    ((failed_tests++))
fi
((total_tests++))

echo -e "\n${YELLOW}📋 Testando: Validação XML endpoint${NC}"
if python3 -m pytest "tests/test_xml_analise_real.py::TestXMLAnaliseReal::test_endpoint_validar_xml" -v --tb=short; then
    echo -e "${GREEN}✅ Validação XML - PASSOU${NC}"
    ((passed_tests++))
else
    echo -e "${RED}❌ Validação XML - FALHOU${NC}"
    ((failed_tests++))
fi
((total_tests++))

echo -e "\n${YELLOW}📋 Testando: XML inválido (deve retornar 422)${NC}"
if python3 -m pytest "tests/test_xml_analise_real.py::TestXMLAnaliseReal::test_endpoint_analisar_xml_invalido" -v --tb=short; then
    echo -e "${GREEN}✅ XML inválido - PASSOU${NC}"
    ((passed_tests++))
else
    echo -e "${RED}❌ XML inválido - FALHOU${NC}"
    ((failed_tests++))
fi
((total_tests++))

echo -e "\n${BLUE}📊 Executando todos os testes XML em modo verbose...${NC}"

# Executar todos os testes XML juntos
if python3 -m pytest tests/test_xml_analise_real.py tests/integration/test_xml_import_real_data.py tests/test_xml_confirmacao_idempotencia.py -v --tb=short --maxfail=3; then
    echo -e "${GREEN}✅ Todos os testes XML - PASSARAM${NC}"
else
    echo -e "${YELLOW}⚠️  Alguns testes XML falharam (verifique detalhes acima)${NC}"
fi

echo -e "\n${BLUE}📈 Gerando relatório de cobertura...${NC}"

# Gerar relatório de cobertura se disponível
if command -v coverage &> /dev/null; then
    coverage run -m pytest tests/test_xml_analise_real.py -v
    coverage report -m --include="wms/interfaces/api_xml_analise.py,wms/application/xml_analise_service.py"
    coverage html
    echo -e "${GREEN}✅ Relatório de cobertura gerado em htmlcov/${NC}"
else
    echo -e "${YELLOW}⚠️  Coverage não instalado. Para instalar: pip3 install coverage${NC}"
fi

echo -e "\n${BLUE}📋 Resumo da Execução${NC}"
echo "=================================================="
echo -e "Total de testes executados: ${BLUE}$total_tests${NC}"
echo -e "Testes passaram: ${GREEN}$passed_tests${NC}"
echo -e "Testes falharam: ${RED}$failed_tests${NC}"

if [ $failed_tests -eq 0 ]; then
    echo -e "\n${GREEN}🎉 Todos os testes passaram! Sistema está funcionando corretamente.${NC}"
    exit_code=0
else
    echo -e "\n${YELLOW}⚠️  Alguns testes falharam. Verifique os logs acima para detalhes.${NC}"
    echo -e "${YELLOW}💡 Dica: Verifique se o banco de dados está acessível e se as dependências estão instaladas.${NC}"
    exit_code=1
fi

echo -e "\n${BLUE}🔧 Comandos úteis para debugging:${NC}"
echo "  # Executar apenas um teste específico:"
echo "  python3 -m pytest tests/test_xml_analise_real.py::TestXMLAnaliseReal::test_endpoint_health_check -v"
echo ""
echo "  # Executar com modo debug:"
echo "  python3 -m pytest tests/test_xml_analise_real.py -v -s --tb=long"
echo ""
echo "  # Verificar variáveis de ambiente:"
echo "  cat .env"
echo ""
echo "  # Verificar logs do PostgreSQL:"
echo "  sudo tail -f /var/log/postgresql/postgresql-*.log"

echo -e "\n${GREEN}✨ Execução concluída!${NC}"

exit $exit_code
