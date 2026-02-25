# JADE-STOCK - A BÍBLIA DO SISTEMA
## Documentação Completa de Arquitetura, Negócio e Engenharia

> **"Este documento é o mapa completo do labirinto, a engenharia reversa do quebra-cabeça, e o guia definitivo para montar e entender todo o ecossistema Jade-stock."**

---

## ÍNDICE COMPLETO

1. [Visão Geral e Filosofia](#1-visão-geral-e-filosofia)
2. [Arquitetura Técnica](#2-arquitetura-técnica)
3. [Módulos do Sistema](#3-módulos-do-sistema)
4. [Banco de Dados e Persistência](#4-banco-de-dados-e-persistência)
5. [APIs e Endpoints](#5-apis-e-endpoints)
6. [Event Store e Comunicação](#6-event-store-e-comunicação)
7. [SDK e Integração](#7-sdk-e-integração)
8. [Frontend e Interface](#8-frontend-e-interface)
9. [Deploy e Operação](#9-deploy-e-operação)
10. [Testes e Qualidade](#10-testes-e-qualidade)
11. [Regras de Negócio](#11-regras-de-negócio)
12. [Roadmap e Evolução](#12-roadmap-e-evolução)
13. [Guia de Sobrevivência](#13-guia-de-sobrevivência)

---

## 1. VISÃO GERAL E FILOSOFIA

### 1.1 O Que É o Jade-stock

O Jade-stock é um sistema integrado de gestão empresarial focado em três domínios principais:
- **WMS (Warehouse Management System)**: Gestão completa de estoque
- **Contábil**: Gestão financeira e lançamentos
- **IA (Analytics)**: Previsões e análises preditivas

### 1.2 Filosofia de Design

**Equilíbrio Quádruplo**:
- **Modularidade**: Cada domínio evolui independentemente
- **Segurança de Execução**: Falhas não propagam entre módulos
- **Facilidade de Manutenção**: Padrões consistentes para equipe enxuta
- **Tolerância a Inconsistências**: Outputs de IA são validados antes de afetar dados críticos

### 1.3 Time Ideal

Projetado para **1-2 desenvolvedores** mantendo robustez empresarial.

---

## 2. ARQUITETURA TÉCNICA

### 2.1 Monolito Modular + Microserviços Locais

**Monolito Modular**:
- Código organizado por domínios em pastas separadas
- Comunicação direta via chamadas de função
- Padronização de código e revisão simplificada

**Microserviços Locais**:
- Cada domínio expõe API RESTful em porta dedicada
- Comunicação via localhost (baixa latência)
- Isolamento de falhas e reinício independente

**Portas Padrão**:
- WMS: 8001
- Contábil: 8002
- IA: 8003
- PDV: 8004

### 2.2 Arquitetura Baseada em Eventos

**Event Store Central**:
- Todos os módulos emitem eventos para a Event Store
- Consumidores processam eventos de forma assíncrona
- Desacoplamento total entre produtor e consumidor

**Fluxo Típico**:
```
WMS emite evento → Event Store → Módulo Contábil consome → Processa financeiro
```

### 2.3 SDK como Camada de Abstração

**Propósito**:
- Interface única para front-end consumir todas as APIs
- Centraliza autenticação, logging e tratamento de erros
- Versionamento semântico para evolução segura

**Exemplo de Uso**:
```python
from jadestock_sdk import JadeStockClient

client = JadeStockClient(base_url="http://127.0.0.1:8001")
client.registrar_movimentacao({...})
```

---

## 3. MÓDULOS DO SISTEMA

### 3.1 WMS - Warehouse Management System

**Responsabilidades**:
- Recebimento e conferência de mercadorias
- Endereçamento e movimentação de estoque
- Inventário cíclico e ajustes
- Avarias e perdas
- Kanban de reposição
- Curva ABC e giro de estoque

**Estrutura de Pastas**:
```
WMS/
├── wms/
│   ├── domain/           # Entidades de domínio
│   ├── application/      # Casos de uso
│   ├── infrastructure/   # Adapters e persistência
│   └── interfaces/       # APIs e interfaces externas
├── tests/               # Suíte completa de testes
├── scripts/             # Scripts de deploy e operação
└── docs_negocio/        # Documentação de negócio
```

**Casos de Uso Implementados**:
- RegistrarMovimentacaoEstoque
- RegistrarAjusteEstoque
- RegistrarAvariaEstoque
- RegistrarRecebimento
- RegistrarInventarioCiclico
- RegistrarPoliticaKanban
- ProcessarCurvaABCD
- ProcessarGiroEstoque
- ProcessarSazonalidadeOperacional
- ProcessarGovernancaOrcamentaria

### 3.2 Contábil

**Status**: Planejado (consumidor de eventos)

**Responsabilidades Futuras**:
- Consumir eventos do WMS
- Gerar lançamentos contábeis
- Conciliação bancária
- DRE e relatórios financeiros

### 3.3 IA - Analytics

**Status**: Planejado

**Responsabilidades Futuras**:
- Previsão de demanda
- Recomendações operacionais
- Análise de sazonalidade
- Detecção de anomalias

**Regra de Ouro**: IA nunca executa movimentos, apenas recomenda.

### 3.4 PDV - Ponto de Venda

**Status**: Documentado nos adendos

**Responsabilidades**:
- Frente de caixa
- Registro de vendas
- Integração com WMS para baixa de estoque
- Emissão de comprovantes

---

## 4. BANCO DE DADOS E PERSISTÊNCIA

### 4.1 PostgreSQL com Schemas Segregados

**Único Banco, Múltiplos Schemas**:
- `wms`: Tabelas de movimentação de estoque
- `contabil`: Lançamentos e conciliações
- `ia`: Históricos e modelos
- `event_store`: Eventos centralizados

**Vantagens**:
- Backup único
- Monitoramento centralizado
- Isolamento lógico via permissões

### 4.2 Schema Core vs Extended

**Schema Core** (uso imediato):
```sql
-- Tabelas essenciais para operação
item_master, sku, endereco, saldo_estoque
movimentacao_estoque, recebimento, recebimento_item
event_store, idempotency_command
```

**Schema Extended** (fases futuras):
```sql
-- Funcionalidades avançadas
sku_endereco, lote_validade, avaria_registro
inventario_contagem, politica_reposicao
kanban_politica, orcamento_periodo
```

### 4.3 Migrations com Alembic

**Pipeline de Deploy**:
1. Validação de dependências
2. Conexão e validação do banco
3. Aplicação de migrations pendentes
4. Testes de sanidade pós-migration
5. Inicialização dos microserviços

**Comando de Deploy**:
```bash
cd WMS
./scripts/release_gate.sh
```

---

## 5. APIS E ENDPOINTS

### 5.1 Padrão RESTful

**Semântica HTTP**:
- Status codes com propósito claro
- Erros padronizados com correlation_id
- Idempotência via Idempotency-Key header

### 5.2 Endpoints WMS v1

**Movimentação**:
- `POST /v1/movimentacoes` - Registrar movimentação
- `POST /v1/ajustes` - Ajustes de estoque
- `POST /v1/avarias` - Registro de avarias

**Recebimento**:
- `POST /v1/recebimentos` - Conferência de recebimento
- `POST /v1/recebimentos/xml/analisar` - Análise de NF-e XML
- `POST /v1/recebimentos/xml/confirmar` - Confirmação de importação

**Inventário**:
- `POST /v1/inventarios/ciclico` - Contagem cíclica

**Analytics**:
- `POST /v1/curva-abcd/processar` - Processar curva ABC
- `POST /v1/giro/processar` - Calcular giro
- `POST /v1/sazonalidade/processar` - Análise sazonal
- `POST /v1/kanban/politicas` - Políticas de kanban
- `POST /v1/orcamento/simular` - Simulação orçamentária

**Sistema**:
- `GET /v1/health` - Health check

### 5.3 Contrato de Erros

**Estrutura Padrão**:
```json
{
  "status_code": 409,
  "code": "IDEMPOTENCY_VIOLATION",
  "message": "Correlation ID já utilizado com payload diferente",
  "details": {...},
  "correlation_id": "corr_001"
}
```

---

## 6. EVENT STORE E COMUNICAÇÃO

### 6.1 Estrutura do Evento

**Contrato Padrão**:
```json
{
  "event_name": "movimentacao_estoque_registrada",
  "event_id": "uuid-v4",
  "occurred_at": "2026-02-21T12:00:00Z",
  "actor_id": "op_42",
  "tenant_id": "lojax",
  "correlation_id": "mov_001",
  "schema_version": "1.0",
  "payload": {...}
}
```

### 6.2 Catálogo de Eventos WMS

**Recebimento**:
- `recebimento_conferido`
- `recebimento_divergente`
- `xml_analisado`
- `recebimento_xml_confirmado`

**Movimentação**:
- `movimentacao_estoque_registrada`
- `ajuste_estoque_registrado`

**Avarias**:
- `avaria_registrada`
- `avaria_aprovada`

**Inventário**:
- `contagem_iniciada`
- `contagem_confirmada`
- `divergencia_identificada`

**Analytics**:
- `curva_abcd_processada`
- `giro_estoque_calculado`
- `sazonalidade_analisada`

### 6.3 Retry e Dead-Letter Queue

**Estratégia de Retry**:
- 1ª falha: retry em 30 segundos
- 2ª falha: retry em 2 minutos
- 3ª falha: retry em 10 minutos
- Após 5 falhas: Dead-Letter Queue

---

## 7. SDK E INTEGRAÇÃO

### 7.1 JadeStockClient

**Instalação**:
```python
from jadestock_sdk import JadeStockClient

client = JadeStockClient(
    base_url="http://127.0.0.1:8001",
    timeout_seconds=10.0,
    retries=2,
    auto_correlation_id=True
)
```

**Idempotência Automática**:
```python
# Gera correlation_id automaticamente
client.registrar_movimentacao({...})
```

**Tratamento de Erros**:
```python
try:
    client.registrar_movimentacao({...})
except JadeStockSDKError as exc:
    print(exc.status_code, exc.message)
```

### 7.2 Laboratório de Testes

**Frontend Fake**:
- Interface visual em `LaboratorioDepositoBebidas/`
- Testes práticos dos endpoints
- Templates de payload prontos

**Como Rodar**:
```bash
cd ~/meus_projetos/Jade-stock
source .venv/bin/activate
PYTHONPATH=. python3 -m uvicorn LaboratorioDepositoBebidas.app:app --reload --port 8700
```

---

## 8. FRONTEND E INTERFACE

### 8.1 Cliente Rico Flutter/Flet

**Tecnologias**:
- **Flutter**: Multi-plataforma nativo
- **Flet**: Python + Flutter (redução de barreira)

**Responsabilidades**:
- Interface de usuário rica
- Integração com hardware (impressoras, scanners)
- Dashboards analíticos
- Consumo via SDK

### 8.2 Hot Reload Parcial

**Funcionalidade**:
- Novas telas carregadas dinamicamente
- Atualizações sem reiniciar aplicação
- Manifesto remoto de rotas

---

## 9. DEPLOY E OPERAÇÃO

### 9.1 Pipeline Profissional

**Etapas Automatizadas**:
1. Validação de dependências
2. Aplicação de migrations
3. Testes de sanidade
4. Health check de startup
5. Inicialização dos serviços

### 9.2 Contêinerização Progressiva

**Fase 1: Servidor Único**
- Todos os serviços em localhost
- Simplicidade operacional máxima

**Fase 2: Docker**
- Imagens independentes por módulo
- Docker Compose para orquestração
- Volumes para persistência

**Fase 3: Múltiplos Servidores**
- Load balancers
- Kubernetes/Docker Swarm
- Escalabilidade horizontal

### 9.3 Orquestrador de Licenças

**Validação Dinâmica**:
- Consulta a servidor de licenças
- Grace period offline (7 dias)
- Controle remoto de revogação
- Telemetria de uso

---

## 10. TESTES E QUALIDADE

### 10.1 Suíte Completa de Testes

**Tipos de Testes**:
- **Unitários**: Lógica de domínio isolada
- **Integração**: API + PostgreSQL
- **Transacionais**: Comportamento ACID
- **Idempotência**: Repetição de operações

**Execução**:
```bash
cd WMS
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

### 10.2 Release Gate

**Checklist Automático**:
- 91 testes passando
- Conexão PostgreSQL
- Schema aplicado
- Idempotência funcionando
- Health check positivo

---

## 11. REGRAS DE NEGÓCIO

### 11.1 WMS Enxuto MVP

**Foco em Operação Pequena** (3-4 pessoas):
- Recebimento com conferência simples
- Endereçamento mínimo útil
- Inventário cíclico guiado
- Avarias com motivo obrigatório
- Alertas de ruptura/excesso

### 11.2 Endereçamento

**Estrutura Mínima**:
```
zona-prateleira-posicao
ex: DEP-A-01 (Depósito-A-Prateleira-01)
```

### 11.3 Kanban de Reposição

**Faixas de Controle**:
- **Verde**: Estoque seguro
- **Amarela**: Alerta de reposição
- **Vermelha**: Ruptura iminente

### 11.4 Curva ABC

**Classificação**:
- **Classe A**: Alto impacto econômico
- **Classe B**: Impacto médio
- **Classe C**: Baixo impacto
- **Classe D**: Muito baixo impacto

### 11.5 Importação de NF-e

**Fluxo Inteligente**:
1. Upload do XML
2. Parse e validação
3. Vinculação automática de produtos
4. Revisão manual de ambiguidades
5. Confirmação com dedução de estoque

**Algoritmo de Matching**:
- EAN/GTIN: 40% de peso
- NCM: 20% de peso
- Similaridade de descrição: 30%
- Histórico do fornecedor: 10%

---

## 12. ROADMAP E EVOLUÇÃO

### 12.1 Fases de Execução

**Fase A - WMS Produção** ✅
- Base estável com migrations reais
- Deploy automatizado
- Release gate funcional

**Fase B - Operação e Observabilidade** 
- Logs estruturados
- Métricas básicas
- Alertas operacionais

**Fase C - Módulo IA**
- Processamento estatístico
- Redes neurais para previsão
- Recomendações consumíveis

**Fase D - Contábil MVP**
- Consumidor de eventos
- Lançamentos básicos
- Retry + DLQ

**Fase E - IAM e Comercial**
- OAuth (Google primeiro)
- Licenciamento progressivo

### 12.2 Ordem Final Oficial

```
A → B → C → D → E
```

---

## 13. GUIA DE SOBREVIVÊNCIA

### 13.1 Setup Inicial

**Ambiente Virtual**:
```bash
cd ~/meus_projetos/Jade-stock
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r WMS/requirements-dev.txt
```

### 13.2 Operação Diária

**Subir API WMS**:
```bash
cd WMS
./scripts/run_api.sh
```

**Verificar Saúde**:
```bash
curl http://127.0.0.1:8001/v1/health
```

### 13.3 Debugging

**Erro 409 (Idempotência)**:
```sql
SELECT * FROM idempotency_command 
WHERE correlation_id = 'SEU_CORRELATION_ID';
```

**Solução**:
- Use o mesmo payload para retry
- Gere novo correlation_id para nova operação

### 13.4 Testes Rápidos

**API In-Memory**:
```bash
WMS_API_BACKEND=inmemory ./scripts/run_api.sh
```

**PostgreSQL Completo**:
```bash
cd WMS
cp .env.example .env
docker compose -f docker-compose.postgres.yml --env-file .env up -d
./scripts/run_sql_tests.sh
```

### 13.5 Comandos Essenciais

| Comando | Propósito |
|---------|----------|
| `./scripts/release_gate.sh` | Validação completa pré-deploy |
| `./scripts/run_api.sh` | Sobe API local |
| `./scripts/run_sql_tests.sh` | Testes com PostgreSQL |
| `python3 -m unittest discover` | Todos os testes |

### 13.6 Mapa Mental do Sistema

**Fluxo Principal**:
```
Usuário → Frontend → SDK → API WMS → PostgreSQL → Event Store → [Contábil/IA]
```

**Pontos Críticos**:
- **Event Store**: Coração da resiliência
- **Idempotência**: Garantia de consistência
- **SDK**: Interface única de integração
- **PostgreSQL**: Fonte da verdade

---

## CONCLUSÃO

O Jade-stock representa uma arquitetura moderna equilibrada entre robustez empresarial e simplicidade operacional. Cada decisão técnica foi tomada para permitir que uma equipe enxuta mantenha um sistema complexo sem sacrificar qualidade ou capacidade de evolução.

**Princípios Fundamentais**:
1. **Clareza antes de otimização prematura**
2. **Automação em todo pipeline crítico**
3. **Documentação como código vivo**
4. **Testes como rede de segurança**
5. **Eventos como cola do sistema**

Este documento é a referência definitiva para entender, operar e evoluir o Jade-stock. Ele deve ser mantido atualizado junto com o código, servindo como "a bíblia do sistema" para qualquer pessoa que interaja com o projeto.

---

*Jade-stock - A Bíblia do Sistema - v1.0 - 2026*
*"O mapa completo do labirinto, a engenharia reversa do quebra-cabeça"*
