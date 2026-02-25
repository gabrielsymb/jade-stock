# Jade-stock 📦

 Sistema Integrado de Gestão Empresarial - WMS + Contábil + IA

> **Arquitetura moderna para equipe enxuta** • Monolito Modular + Microserviços Locais • PostgreSQL + Event Store

---

## 🚀 Visão Rápida

O Jade-stock é um sistema de gestão empresarial focado em três domínios principais:

- **🏗️ WMS**: Gestão completa de estoque e operações de depósito
- **📊 Contábil**: Lançamentos financeiros e relatórios (em desenvolvimento)
- **🤖 IA**: Previsões e análises preditivas (planejado)

**Design para**: 1-2 desenvolvedores mantendo robustez empresarial

---

## 📚 Documentação Essencial

### 🎯 Para Começar
| Documento | Para Quem | Propósito |
|-----------|-----------|-----------|
| [📖 Bíblia do Sistema](./JADE-STOCK-BIBLIA-DO-SISTEMA.md) | Todos | Visão completa de arquitetura e negócio |
| [⚙️ Setup WMS](./WMS/README.md) | Desenvolvedores | Instalação e configuração técnica |
| [🗺️ Mapa do Sistema](./WMS/docs_negocio/00_mapa_sistema.md) | Produto/Dev | Visão de negócio do WMS |

### 🔧 Operação Diária
| Documento | Para Quem | Propósito |
|-----------|-----------|-----------|
| [📜 Scripts](./WMS/scripts/README.md) | Operação | Scripts de deploy e manutenção |
| [🧪 Laboratório](./LaboratorioDepositoBebidas/README.md) | QA/Dev | Frontend fake para testes |
| [🔌 SDK](./sdk/README.md) | Frontend | Integração com APIs |

### 🏗️ Arquitetura
| Documento | Para Quem | Propósito |
|-----------|-----------|-----------|
| [🗄️ Database](./Database/README.md) | DBA/Dev | Schema e migrações |
| [🏛️ Código WMS](./WMS/wms/README.md) | Dev | Estrutura do código fonte |
| [📋 Análise](./ANALISE_DOCUMENTACAO.md) | Mantenedores | Estado atual da documentação |

---

## 🛠️ Stack Técnico

### Backend
- **Python 3.11+** com FastAPI
- **PostgreSQL** com schemas segregados
- **Event Store** para comunicação assíncrona
- **Alembic** para migrations versionadas

### Frontend
- **Flutter/Flet** (planejado)
- **HTML/CSS/JS** (laboratório de testes)

### Infraestrutura
- **Docker** (contêinerização progressiva)
- **GitHub Actions** (CI/CD)
- **PostgreSQL** (persistência unificada)

---

## 🚀 Começo Rápido

### Pré-requisitos
```bash
# Python 3.11+
python3 --version

# PostgreSQL 14+
psql --version

# Git
git --version
```

### Setup do Ambiente
```bash
# 1. Clone o repositório
git clone <repo-url>
cd Jade-stock

# 2. Ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# ou .venv\Scripts\activate  # Windows

# 3. Dependências
python -m pip install --upgrade pip
python -m pip install -r WMS/requirements-dev.txt
```

### Subir o WMS
```bash
# API em memória (para desenvolvimento)
cd WMS
WMS_API_BACKEND=inmemory ./scripts/run_api.sh

# API com PostgreSQL (produção)
cp .env.example .env
# Configure WMS_POSTGRES_DSN em .env
docker compose -f docker-compose.postgres.yml --env-file .env up -d
./scripts/run_api.sh
```

### Verificar Saúde
```bash
curl http://127.0.0.1:8001/v1/health
```

---

## 🧪 Testes

### Suite Completa
```bash
cd WMS
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

### Testes de Integração PostgreSQL
```bash
cd WMS
./scripts/run_sql_tests.sh
```

### Release Gate (pré-deploy)
```bash
cd WMS
./scripts/release_gate.sh
```

---

## 📊 Arquitetura em Resumo

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │      SDK        │    │   APIs Locais   │
│  (Flutter/Flet) │◄──►│  (Python)       │◄──►│  (FastAPI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐             │
                       │  Event Store    │◄────────────┤
                       │  (PostgreSQL)   │             │
                       └─────────────────┘             │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Módulo WMS     │    │  Módulo Contábil│    │   Módulo IA     │
│  (porta 8001)   │    │  (porta 8002)   │    │  (porta 8003)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 🔄 Fluxo de Trabalho

### Desenvolvimento
1. **Branch**: `feature/nome-da-feature`
2. **Testes**: Suite completa passando
3. **Documentação**: Atualizar docs relevantes
4. **PR**: Revisão de código + validação

### Deploy
1. **Migration**: Alembic aplica mudanças
2. **Testes**: Release gate automático
3. **API**: Subir com health check
4. **Monitor**: Logs estruturados

---

## 📋 Status dos Módulos

| Módulo | Status | Porta | Testes | Docs |
|--------|--------|-------|--------|------|
| **WMS** | ✅ Produção | 8001 | 91 tests | ✅ Completa |
| **Contábil** | 🔜 Planejado | 8002 | - | 📝 Esboçada |
| **IA** | 🔜 Planejado | 8003 | - | 📝 Esboçada |
| **PDV** | 📝 Documentado | 8004 | - | 📝 Adendos |

---

## 🤝 Contribuição

### Como Contribuir
1. Leia a [Bíblia do Sistema](./JADE-STOCK-BIBLIA-DO-SISTEMA.md)
2. Verifique o [Guia de Contribuição](./CONTRIBUTING.md) (pendente)
3. Abra issue para discussão
4. Submeta PR com testes

### Padrões
- **Código**: PEP 8 + type hints
- **Testes**: unittest + coverage > 80%
- **Docs**: Markdown + seções padronizadas
- **Commits**: Conventional Commits

---

## 📄 Licença

[Informações de licença a serem adicionadas]

---

## 🆘 Suporte

### Documentação
- [📖 Bíblia do Sistema](./JADE-STOCK-BIBLIA-DO-SISTEMA.md) - Arquitetura completa
- [🔧 Guia de Troubleshooting](./WMS/docs_negocio/05_guia_de_perguntas_do_dono_do_produto.md) - Perguntas frequentes
- [📋 Análise de Docs](./ANALISE_DOCUMENTACAO.md) - Estado atual da documentação

### Comandos Úteis
```bash
# Health check
curl http://127.0.0.1:8001/v1/health

# Verificar logs (se configurado)
docker compose logs -f wms-api

# Debug erro 409 (idempotência)
SELECT * FROM idempotency_command 
WHERE correlation_id = 'SEU_CORRELATION_ID';
```

---

## 🗺️ Roadmap

### Fase A ✅ (WMS Produção)
- [x] Base estável com migrations
- [x] Deploy automatizado
- [x] Release gate funcional

### Fase B 🔜 (Operação)
- [ ] Logs estruturados
- [ ] Métricas básicas
- [ ] Alertas operacionais

### Fase C 🔜 (IA)
- [ ] Processamento estatístico
- [ ] Redes neurais para previsão
- [ ] Recomendações consumíveis

### Fase D 🔜 (Contábil)
- [ ] Consumidor de eventos
- [ ] Lançamentos básicos
- [ ] Retry + DLQ

### Fase E 🔜 (IAM)
- [ ] OAuth (Google)
- [ ] Licenciamento progressivo

---

**Jade-stock** • *Sistema moderno para gestão empresarial*  
Versão: 1.0 • Atualizado: 2026-02-25
