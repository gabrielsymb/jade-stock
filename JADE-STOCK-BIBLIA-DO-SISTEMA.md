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

#### Pipeline Profissional Detalhado

**Etapa 1 - Validação de Dependências:**
- Verifica bibliotecas Python nas versões corretas
- Baseado em requirements versionado

**Etapa 2 - Conexão e Validação do Banco:**
- Testa conectividade PostgreSQL
- Verifica permissões necessárias nos schemas

**Etapa 3 - Aplicação de Migrations:**
- Alembic executa migrations pendentes em ordem
- Falha interrompe deploy, mantendo consistência

**Etapa 4 - Testes de Sanidade Pós-Migration:**
- Subconjunto de testes de integração
- Confirma schema atualizado e operacional

**Etapa 5 - Inicialização dos Microserviços:**
- Apenas após validações anteriores
- Módulos WMS, Contábil, IA iniciados

#### Health Check de Startup

Cada microserviço implementa verificação de dependências críticas:
- **WMS:** Schema wms, tabelas críticas, idempotência
- **Contábil:** Schema contabil, acesso event_store
- **IA:** Schema ia, modelos carregados

**Falha de Startup:**
- Recusa inicializar com erro descritivo
- Orquestrador detecta e aciona alertas
- Usuário vê mensagem clara sem detalhes técnicos

#### Integração com Orquestrador de Contêineres

**Docker Compose:**
- PostgreSQL healthy antes das aplicações
- Migrations executam e concluem antes dos serviços
- Deploy inteiro: `docker compose up`

#### Ambientes Separados

**Desenvolvimento:** Novas migrations criadas e testadas localmente
**Homologação:** Réplica exata de produção, release gate executado
**Produção:** Apenas código validado

**Isolamento Inicial:**
- Dois schemas no mesmo servidor PostgreSQL
- Padrão de isolamento já adotado pelos domínios
- Migração para servidores separados facilitada

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

### 5.4 Estratégia de Versionamento de API

**Quando Criar Nova Versão:**
- **Quebra de compatibilidade:** Mudar path de `/v1/` para `/v2/`
- **Backward-compatible:** Manter em `/v1/` com novo campo opcional

**Política de Suporte:**
- **Janela de suporte:** 6 meses após lançamento da v2
- **Depreciação:** Headers `Deprecation: true` + `Sunset: <data>`
- **Remoção:** Apenas após janela de suporte expirar

**Exemplo de Evolução:**
```
v1: POST /v1/movimentacoes (campo "endereco" obrigatório)
v2: POST /v2/movimentacoes (campo "endereco" opcional, novo campo "endereco_id")
```

**Processo de Depreciação:**
1. **Anúncio:** Documentação + headers de aviso
2. **Período:** 6 meses para migração
3. **Remoção:** Desativação completa da v1

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
  "correlation_id": "mov_20260221_001",
  "schema_version": "1.0",
  "payload": {...}
}
```

#### 6.1.1 Persistência em PostgreSQL

**Tabela `event_store.stored_events`**:
```sql
CREATE TABLE event_store.stored_events (
    id BIGSERIAL PRIMARY KEY,
    event_id UUID NOT NULL UNIQUE,
    event_name VARCHAR(255) NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    actor_id VARCHAR(100),
    tenant_id VARCHAR(100) NOT NULL,
    correlation_id VARCHAR(100),
    schema_version VARCHAR(20) NOT NULL DEFAULT '1.0',
    payload JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    processed_at TIMESTAMPTZ,
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('pending', 'processed', 'failed', 'dead_letter')),
    retry_count INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- Índices para performance
    CONSTRAINT idx_stored_events_tenant_occurred UNIQUE (tenant_id, occurred_at, event_id),
    INDEX idx_stored_events_event_name (event_name),
    INDEX idx_stored_events_correlation (correlation_id),
    INDEX idx_stored_events_status (status)
);
```

**Consulta para Debugging**:
```sql
-- Eventos por correlation_id
SELECT * FROM event_store.stored_events 
WHERE correlation_id = 'mov_20260221_001' 
ORDER BY occurred_at;

-- Eventos falhados
SELECT * FROM event_store.stored_events 
WHERE status = 'failed' 
ORDER BY created_at DESC;

-- Eventos por tenant nas últimas 24h
SELECT event_name, COUNT(*) as total 
FROM event_store.stored_events 
WHERE tenant_id = 'lojax' 
  AND occurred_at >= NOW() - INTERVAL '24 hours'
GROUP BY event_name;
```
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

#### Deploy Inicial: Servidor Único

Na fase inicial, todos os microserviços podem coexistir em um único servidor, comunicando-se via localhost. Essa configuração simplifica radicalmente a operação: um único servidor para monitorar, um único conjunto de logs para analisar e um único ponto de deploy para gerenciar.

**Mitigação de Risco:**
- Restart automático dos serviços (systemd/PM2)
- Backups periódicos em armazenamento separado
- Health check de startup

#### Contêinerização Detalhada

À medida que o sistema cresce, a contêinerização via Docker se torna estratégica:

**Benefícios Específicos:**
- **Módulo IA:** Versões específicas de bibliotecas sem conflito
- **Módulo Contábil:** Reindependente sem interromper WMS
- **Persistência:** Docker Volumes separados dos contêineres

**Decisão de Adoção:**
- Guiada por necessidade concreta, não tendência
- Overhead vs benefícios para equipe enxuta
- Momento ideal: múltiplos ambientes ou clientes

#### Orquestrador de Atualizações

**Shadow Update:**
- Nova versão baixada em segundo plano
- Troca em momento de baixo impacto
- Downtime < 5 segundos

**Fluxo de Atualização:**
1. Detectar nova imagem no registro
2. Download em segundo plano (camadas alteradas apenas)
3. Armazenar como inativa
4. Aplicar: `docker stop <antigo> && docker run <novo>`

**Ferramentas:**
- **Watchtower:** Automação simples
- **SDK Integration:** Controle fino via API

#### Escalabilidade Horizontal

- **Load Balancers:** APIs RESTful prontas
- **Event Store:** Migrável para RabbitMQ/Kafka
- **Kubernetes:** Evolução natural, apenas quando justificável

### 9.3 Orquestrador de Licenças

**Validação Dinâmica:**
- Consulta a servidor de licenças
- Grace period offline (7 dias)
- Controle remoto de revogação
- Telemetria de uso

#### Funcionamento

O orquestrador valida licenças antes de iniciar contêineres:

**Estados da Licença:**
- **Ativa:** Prossegue normalmente
- **Expirada:** Bloqueia novos contêineres, mantém ativos até fim do expediente
- **Revogada:** Derruba todos imediatamente

#### Licença Amarrada ao Registro

**Proteção Adicional:**
- Registro privado exige token de licença
- Download bloqueado sem token válido
- Propriedade intelectual protegida

#### Operação Offline

**Grace Period:**
- 7 dias padrão, renovável por validação
- Token criptografado localmente
- Avisos progressivos antes do bloqueio

#### Controle Remoto e Telemetria

**Capacidades:**
- Suspensão imediata por inadimplência
- Migração entre máquinas
- Detecção de uso anômalo
- Métricas: sessões ativas, módulos, instalação

### 9.4 Autenticação via OAuth 2.0

O Jade-stock delega autenticação a provedores consolidados (Google, Microsoft, Apple), eliminando gerenciamento de senhas.

#### Fluxo OAuth 2.0

1. Usuário clica "Entrar com Google"
2. Cliente abre navegador/webview para login
3. Google redireciona com token autorização
4. Backend valida token junto à API Google
5. Backend extrai identificador único e e-mail
6. Verifica/cria usuário no banco
7. Retorna token de sessão Jade-stock

#### Integração com Licenciamento

**Pipeline Duplo:**
1. **Identidade:** OAuth (responsabilidade do provedor)
2. **Autorização:** Licença (responsabilidade Jade-stock)

#### Provedores Suportados

- **Google:** Maior cobertura, um clique
- **Microsoft:** Ambientes corporativos (Azure AD)
- **Apple:** Obrigatório para App Store

#### Dados Armazenados

**Apenas o necessário:**
- Identificador único do provedor (sub)
- E-mail para comunicações
- Nome de exibição
- Provedor de origem
- Datas de acesso
- Vínculo com licença

#### Tokens

- **Access Token:** Curta duração (1h), não persistido
- **Refresh Token:** Longa duração, criptografado em BD
- **Sessão Interna:** JWT, armazenado localmente seguro

#### Experiência do Usuário

- **Primeiro uso:** Um clique (sessão Google ativa)
- **Usos subsequentes:** Acesso direto sem re-login
- **Similar ao:** Creative Cloud, Figma, Notion

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

#### 12.2.1 Métricas e Observabilidade (Fase B)

**Métricas Chave para Implementar:**
```yaml
# Métricas de Negócio
wms_movimentacoes_total{tenant="lojax"} 45
wms_estoque_atual{sku="SKU-001"} 150.5
wms_recebimentos_pendentes{tenant="lojax"} 12

# Métricas de Performance
wms_request_duration_seconds{endpoint="/v1/movimentacoes",method="POST"} 0.245
wms_requests_total{status="200",endpoint="/v1/movimentacoes"} 1023
wms_concurrent_connections 15

# Métricas de Infraestrutura
wms_database_connections_active 8
wms_event_store_pending_events 5
wms_idempotency_cache_size 1024
```

**Implementação Simples com Prometheus:**
```python
# Exemplo de middleware de métricas
from prometheus_client import Counter, Histogram, Gauge
import time
import logging

REQUEST_COUNT = Counter('wms_requests_total', 'Total requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = Histogram('wms_request_duration_seconds', 'Request duration')
ACTIVE_CONNECTIONS = Gauge('wms_database_connections_active', 'Active DB connections')

class MetricsMiddleware:
    def __init__(self, app):
        self.app = app
    
    def __call__(self, environ, start_response):
        start_time = time.time()
        
        def custom_start_response(status, headers, exc_info=None):
            REQUEST_COUNT.labels(
                method=environ['REQUEST_METHOD'],
                endpoint=environ['PATH_INFO'],
                status=status.split()[0]
            ).inc()
            
            REQUEST_DURATION.observe(time.time() - start_time)
            return start_response(status, headers, exc_info)
        
        return self.app(environ, custom_start_response)
```

**Coleta com Agentes Leves:**
```bash
# Node Exporter para métricas do sistema
docker run -d --net="host" \
  --pid="host" \
  --mounts="host:/host" \
  quay.io/prometheus/node-exporter

# PostgreSQL Exporter para métricas do banco
docker run -d --net="host" \
  -e DATA_SOURCE_NAME="postgresql://wms:wms@localhost:5432/wms" \
  prometheuscommunity/postgres-exporter

# Custom exporter para métricas WMS
python3 -m wms.infrastructure.metrics.prometheus_exporter
```

**Configuração Prometheus:**
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'wms-api'
    static_configs:
      - targets: ['localhost:8001']
    metrics_path: '/metrics'
    
  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']
      
  - job_name: 'postgres'
    static_configs:
      - targets: ['localhost:9187']
```

**Alertas Essenciais:**
```yaml
# alerts.yml
groups:
  - name: wms_alerts
    rules:
      - alert: WMSHighErrorRate
        expr: rate(wms_requests_total{status="5xx"}[5m]) > 0.1
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Taxa de erro alta na API WMS"
          
      - alert: WMSHighResponseTime
        expr: histogram_quantile(0.95, rate(wms_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Tempo de resposta acima de 2 segundos (P95)"
          
      - alert: WMSEventStoreBacklog
        expr: wms_event_store_pending_events > 100
        for: 10m
        labels:
          severity: critical
        annotations:
          summary: "Event Store com acúmulo de eventos não processados"
```

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

**Erro 5xx (Erro Interno do Servidor)**:
```bash
# Verificar logs do serviço
tail -f ./WMS/logs/api.log

# Verificar status dos containers Docker
docker compose ps
docker compose logs wms-api
```

**Falha na Release Gate**:
```bash
# Executar testes manualmente para identificar falha específica
cd WMS
python3 -m unittest discover -s tests -p 'test_*.py' -v

# Verificar qual teste específico falhou
python3 -m unittest tests.test_api_postgres_integration.TestRegistrarMovimentacao -v
```

**Evento Não Processado**:
```sql
-- Verificar eventos falhados
SELECT * FROM event_store.stored_events 
WHERE status = 'failed' 
ORDER BY created_at DESC;

-- Verificar Dead-Letter Queue
SELECT * FROM event_store.stored_events 
WHERE status = 'dead_letter' 
ORDER BY created_at DESC;

-- Analisar causa da falha
SELECT event_name, error_message, retry_count 
FROM event_store.stored_events 
WHERE status = 'failed' 
  AND correlation_id = 'SEU_CORRELATION_ID';
```

**Timeout de Conexão**:
```bash
# Verificar se PostgreSQL está rodando
docker compose ps postgres

# Testar conexão manualmente
psql "postgresql://wms:wms@localhost:5432/wms"

# Verificar configuração de rede
docker network ls
docker network inspect jade-stock_wms-network
```

### 13.4 Testes de Idempotência - Exemplo Prático

**Como Testar Manualmente**:
```bash
# Primeira requisição (deve retornar 201)
curl -X POST http://localhost:8001/v1/movimentacoes \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-123" \
  -d '{
    "correlation_id": "test-123",
    "sku_id": "SKU-001",
    "quantidade": 10.0,
    "tipo": "entrada",
    "endereco_destino": "DEP-A-01"
  }'

# Segunda requisição igual (deve retornar 409)
curl -X POST http://localhost:8001/v1/movimentacoes \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-123" \
  -d '{
    "correlation_id": "test-123",
    "sku_id": "SKU-001",
    "quantidade": 10.0,
    "tipo": "entrada",
    "endereco_destino": "DEP-A-01"
  }'

# Terceira requisição com payload diferente (deve retornar 409)
curl -X POST http://localhost:8001/v1/movimentacoes \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-123" \
  -d '{
    "correlation_id": "test-123",
    "sku_id": "SKU-001",
    "quantidade": 15.0,  # Payload diferente!
    "tipo": "entrada",
    "endereco_destino": "DEP-A-01"
  }'
```

**Verificação no Banco**:
```sql
-- Apenas um registro deve existir
SELECT COUNT(*) as total, 
       request_payload::json->>'quantidade' as quantidade
FROM idempotency_command 
WHERE correlation_id = 'test-123';

-- Resultado esperado: COUNT = 1, quantidade = 10.0
```

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
