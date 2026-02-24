# Regras de Negócio de Estoque

Este diretório concentra as regras de negócio para o produto de estoque (WMS enxuto), com foco em operação pequena, integração entre módulos e base para API.

> **Nota de neutralidade:** exemplos de produtos nos documentos são ilustrativos; não devem ser hardcoded.

## Navegação Rápida

- [Guia Git e GitHub](GUIA_GIT_GITHUB.md)
- [Política de Versionamento da API](API_VERSIONING.md)
- [SDK Jade-stock](../sdk/README.md)
- [Hub de Negócio (HTML)](docs_negocio/index.html)
- [Mapa de Negócio do Sistema](docs_negocio/00_mapa_sistema.md)
- [Módulos e Responsabilidades](docs_negocio/01_modulos_responsabilidades.md)
- [Mapa de Módulos em HTML](docs_negocio/mapa_modulos.html)
- [Fluxos Reais em HTML](docs_negocio/fluxos_reais.html)
- [Fluxos Reais do Dia a Dia](docs_negocio/02_fluxos_reais_do_dia_a_dia.md)
- [Decisões Traduzidas em HTML](docs_negocio/decisoes_traduzidas.html)
- [Endpoints Sem Jargão](docs_negocio/03_endpoints_sem_jargao.md)
- [Decisões Técnicas Traduzidas](docs_negocio/04_decisoes_tecnicas_traduzidas.md)
- [Perguntas do Dono do Produto](docs_negocio/05_guia_de_perguntas_do_dono_do_produto.md)
- [Mapa de documentação](#mapa-de-documentação)
- [Trilha recomendada](#trilha-recomendada-com-paginação)
- [Mídias de treinamento](#mídias-de-treinamento)
- [Escopo do produto](#escopo-do-produto-wms-enxuto-mvp)
- [Diretrizes gerais](#diretrizes-gerais-de-implementação)

## Mapa de Documentação

- [WMS Enxuto MVP](Regra_de_negocios/Estoque/wms_enxuto/caso_de_uso/wms_enxuto_mvp.md)
- [Matriz de Integração (abas/API/mídias)](Regra_de_negocios/Estoque/integracao/matriz_conceitual_abas_api.md)
- [Modelagem de Domínio WMS (sem código)](Regra_de_negocios/Estoque/integracao/modelagem_dominio_wms.md)
- [Casos de Uso WMS (sem código)](Regra_de_negocios/Estoque/integracao/casos_de_uso_wms.md)
- [Caso de Uso Executável: RegistrarRecebimento](Regra_de_negocios/Estoque/integracao/caso_de_uso_executavel_registrar_recebimento.md)
- [Caso de Uso Executável: RegistrarAjusteEstoque](Regra_de_negocios/Estoque/integracao/caso_de_uso_executavel_registrar_ajuste_estoque.md)
- [Contrato de Eventos](Regra_de_negocios/Estoque/integracao/contrato_eventos.md)
- [Dicionário de Campos Compartilhados](Regra_de_negocios/Estoque/integracao/dicionario_campos_compartilhados.md)
- [Schema Core (fase atual)](../Database/schema_core.sql)
- [Schema Extended (fase futura)](../Database/schema_extended.sql)
- [Governança Orçamentária](Regra_de_negocios/Estoque/governanca_orcamentaria/regra_orcamentaria.md)
- [Recebimento e Conferência](Regra_de_negocios/Estoque/recebimento/caso_de_uso/recebimento_conferencia.md)
- [Address (Endereçamento Operacional) - Regra Principal](Regra_de_negocios/Estoque/address/address_regra/address.md)
- [Endereçamento Básico - Caso de Uso](Regra_de_negocios/Estoque/enderecamento/caso_de_uso/enderecamento_basico.md)
- [Regra de SKU](Regra_de_negocios/Estoque/sku/regra_sku/sku.md)
- [Cadastro de SKU (caso de uso)](Regra_de_negocios/Estoque/sku/caso_de_uso/cadastro_sku.md)
- [Avarias](Regra_de_negocios/Estoque/avarias/regra_avarias/avarias.md)
- [Kanban de Reposição](Regra_de_negocios/Estoque/kanban/regra_kanban/kanban.md)
- [Curva ABCD](Regra_de_negocios/Estoque/curva/regra_abc/curva_abcd.md)
- [Shelf Life](Regra_de_negocios/Estoque/curva/regra_abc/shelf_life.md)
- [Giro de Estoque](Regra_de_negocios/Estoque/giro/regra_giro/giro_estoque.md)
- [Sazonalidade](Regra_de_negocios/Estoque/sazonalidade/regra_sazo/sazonalidade.md)
- [Inventário Cíclico](Regra_de_negocios/Estoque/ciclico/regra_ciclico/ciclico.md)

## Trilha Recomendada com Paginação

Ordem de leitura sugerida para onboarding de operador, produto e API:

1. [WMS Enxuto MVP](Regra_de_negocios/Estoque/wms_enxuto/caso_de_uso/wms_enxuto_mvp.md)
2. [SKU](Regra_de_negocios/Estoque/sku/regra_sku/sku.md)
3. [Cadastro de SKU](Regra_de_negocios/Estoque/sku/caso_de_uso/cadastro_sku.md)
4. [Address (Endereçamento Operacional)](Regra_de_negocios/Estoque/address/address_regra/address.md)
5. [Endereçamento Básico (caso de uso)](Regra_de_negocios/Estoque/enderecamento/caso_de_uso/enderecamento_basico.md)
6. [Recebimento e Conferência](Regra_de_negocios/Estoque/recebimento/caso_de_uso/recebimento_conferencia.md)
7. [Avarias](Regra_de_negocios/Estoque/avarias/regra_avarias/avarias.md)
8. [Kanban de Reposição](Regra_de_negocios/Estoque/kanban/regra_kanban/kanban.md)
9. [Inventário Cíclico](Regra_de_negocios/Estoque/ciclico/regra_ciclico/ciclico.md)
10. [Curva ABCD](Regra_de_negocios/Estoque/curva/regra_abc/curva_abcd.md)
11. [Shelf Life](Regra_de_negocios/Estoque/curva/regra_abc/shelf_life.md)
12. [Giro de Estoque](Regra_de_negocios/Estoque/giro/regra_giro/giro_estoque.md)
13. [Sazonalidade](Regra_de_negocios/Estoque/sazonalidade/regra_sazo/sazonalidade.md)
14. [Governança Orçamentária](Regra_de_negocios/Estoque/governanca_orcamentaria/regra_orcamentaria.md)
15. [Matriz de Integração](Regra_de_negocios/Estoque/integracao/matriz_conceitual_abas_api.md)
16. [Modelagem de Domínio WMS](Regra_de_negocios/Estoque/integracao/modelagem_dominio_wms.md)
17. [Casos de Uso WMS](Regra_de_negocios/Estoque/integracao/casos_de_uso_wms.md)
18. [Caso de Uso Executável: RegistrarRecebimento](Regra_de_negocios/Estoque/integracao/caso_de_uso_executavel_registrar_recebimento.md)
19. [Caso de Uso Executável: RegistrarAjusteEstoque](Regra_de_negocios/Estoque/integracao/caso_de_uso_executavel_registrar_ajuste_estoque.md)
20. [Contrato de Eventos](Regra_de_negocios/Estoque/integracao/contrato_eventos.md)
21. [Dicionário de Campos](Regra_de_negocios/Estoque/integracao/dicionario_campos_compartilhados.md)
22. [Schema Core](../Database/schema_core.sql)
23. [Schema Extended](../Database/schema_extended.sql)

## Mídias de Treinamento

- Vídeo Curva ABC: `estoque_midia/curva_abc_midia/curva_abcd.mp4`
- Vídeo Inventário Cíclico: `estoque_midia/Ciclica_midia/Inventário_Cíclico.mp4`
- Imagem Curva ABC: `estoque_img/Curva_ABC_img/Curva_abc.png`
- Imagem SKU: `estoque_img/sku_img/sku.png`

Uso recomendado:

- botão `Como funciona` dentro da aba;
- card `Treinamento rápido`;
- exibição contextual na primeira utilização da tela.

## Escopo do Produto: WMS Enxuto (MVP)

Para operação pequena (3 a 4 pessoas), priorizar:

- recebimento com conferência simples;
- endereçamento mínimo útil (`zona-prateleira-posicao`);
- inventário cíclico guiado;
- avarias/perdas com motivo obrigatório;
- alertas de ruptura, excesso e validade;
- reposição sugerida sem complexidade excessiva.

## Diretrizes Gerais de Implementação

- decisões orientadas por dados históricos e parâmetros configuráveis;
- regras devem respeitar shelf life, lead time, capital e nível de serviço;
- alertas quando houver conflito entre recomendação e viabilidade;
- apontamento de avaria obrigatório quando houver divergência.

## Estado Técnico Atual

- casos de uso implementados: `RegistrarMovimentacaoEstoque`, `RegistrarAjusteEstoque`, `RegistrarAvariaEstoque`, `RegistrarRecebimento`, `RegistrarInventarioCiclico`, `RegistrarPoliticaKanban`, `ProcessarCurvaABCD`, `ProcessarGiroEstoque`, `ProcessarSazonalidadeOperacional`, `ProcessarGovernancaOrcamentaria`;
- testes automatizados: suíte completa em `WMS/tests` (unitário + integração API + integração PostgreSQL);
- persistência atual: adapters `in_memory_*` para desenvolvimento e teste;
- migração iniciada: adapters Postgres core em `wms/infrastructure/postgres`;
- banco faseado: `schema_core.sql` (agora) e `schema_extended.sql` (depois).

## Leitura Web

Também está disponível uma versão em HTML/CSS para leitura visual:

- `index.html`

## Execução Rápida (Terminal)

Setup recomendado (ambiente único do projeto na raiz `Jade-stock/.venv`):

```bash
cd ~/meus_projetos/Jade-stock
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r WMS/requirements-dev.txt
```

Rodar testes:

```bash
cd WMS
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Subir API minima:

```bash
cd WMS
./scripts/run_api.sh
```

Endpoints v1 (padrao):

- `GET /v1/health`
- `POST /v1/movimentacoes`
- `POST /v1/ajustes`
- `POST /v1/avarias`
- `POST /v1/recebimentos`
- `POST /v1/inventarios/ciclico`
- `POST /v1/kanban/politicas`
- `POST /v1/curva-abcd/processar`
- `POST /v1/giro/processar`
- `POST /v1/sazonalidade/processar`
- `POST /v1/orcamento/simular`

Persistencia da API:

- `WMS_API_BACKEND=inmemory` (padrao): grava em memoria para desenvolvimento.
- `WMS_API_BACKEND=postgres`: grava no PostgreSQL.

Idempotencia (backend Postgres):

- toda escrita usa chave `endpoint + correlation_id`;
- repeticao do mesmo request retorna a mesma resposta, sem duplicar saldo/movimentacao/evento;
- se repetir o mesmo `correlation_id` com payload diferente, a API retorna `409`.

## Trava Final de Release (pre-deploy)

Checklist rapido:

1. `.venv` ativo e dependencias instaladas (`requirements-dev.txt`);
2. `.env` carregado com `WMS_POSTGRES_DSN`;
3. schema aplicado com tabela `idempotency_command`;
4. testes transacionais e de API Postgres verdes;
5. testes de dominio verdes.

Comando unico:

```bash
cd WMS
./scripts/release_gate.sh
```

Se terminar com `OK - trava final concluida.`, o pacote esta pronto para deploy.

## Como depurar erro 409 (idempotencia)

Quando ocorre:

- mesma rota + mesmo `correlation_id` com payload diferente.

Fluxo de correcao:

1. mantenha o mesmo payload se for retry de rede;
2. se a operacao mudou de fato, gere novo `correlation_id`;
3. consulte a chave no banco para auditar:

```sql
SELECT idempotency_key, operation_name, correlation_id, status, created_at, updated_at
FROM idempotency_command
WHERE correlation_id = 'SEU_CORRELATION_ID';
```

Exemplos JSON oficiais (Swagger `/docs`):

`POST /v1/movimentacoes`

```json
{
  "sku_id": "sku_001",
  "tipo_movimentacao": "entrada",
  "quantidade": 10,
  "endereco_origem": null,
  "endereco_destino": "DEP-A-01",
  "operador": "op_01",
  "correlation_id": "corr_api_mov_001",
  "motivo": "Carga inicial"
}
```

`POST /v1/ajustes`

```json
{
  "sku_id": "sku_001",
  "endereco_codigo": "DEP-A-01",
  "quantidade_ajuste": -2,
  "operador": "op_01",
  "correlation_id": "corr_api_ajuste_001",
  "motivo": "Quebra operacional"
}
```

`POST /v1/recebimentos`

```json
{
  "nota_fiscal": "NF-API-001",
  "fornecedor_id": "forn_01",
  "itens": [
    {
      "sku_codigo": "sku_001",
      "quantidade_esperada": 8,
      "quantidade_conferida": 7,
      "endereco_destino": "DEP-A-01",
      "classificacao_divergencia": "falta"
    }
  ],
  "operador": "op_01",
  "correlation_id": "corr_api_rec_001"
}
```

`POST /v1/avarias`

```json
{
  "sku_id": "sku_001",
  "endereco_codigo": "DEP-A-01",
  "quantidade_avaria": 2,
  "operador": "op_01",
  "correlation_id": "corr_api_avaria_001",
  "motivo": "Quebra operacional"
}
```

`POST /v1/kanban/politicas`

```json
{
  "sku_id": "sku_001",
  "elegivel": true,
  "kanban_ativo": true,
  "faixa_atual": "amarela",
  "faixa_verde_min": 20,
  "faixa_amarela_min": 10,
  "faixa_vermelha_min": 5,
  "operador": "op_01",
  "correlation_id": "corr_api_kanban_001",
  "motivo": "Politica inicial"
}
```

`POST /v1/curva-abcd/processar`

```json
{
  "operador": "op_01",
  "correlation_id": "corr_api_abcd_001",
  "itens": [
    {
      "sku_id": "sku_001",
      "impacto_economico": 1000,
      "variabilidade": 0.1,
      "shelf_life_dias": 60,
      "dias_sem_venda": 10,
      "giro_periodo": 12,
      "lead_time_dias": 2
    }
  ]
}
```

`POST /v1/giro/processar`

```json
{
  "operador": "op_01",
  "correlation_id": "corr_api_giro_001",
  "itens": [
    {
      "sku_id": "sku_001",
      "classe_abc": "A",
      "estoque_atual": 100,
      "venda_media_diaria_prevista": 5,
      "total_vendido_periodo": 40,
      "estoque_medio_periodo": 10,
      "ruptura_recorrente": false,
      "lead_time_dias": 2,
      "shelf_life_dias": 60
    }
  ]
}
```

`POST /v1/sazonalidade/processar`

```json
{
  "operador": "op_01",
  "correlation_id": "corr_api_sazo_001",
  "itens": [
    {
      "sku_id": "sku_001",
      "fator_sazonal": 1.2,
      "confianca_modelo": 0.9,
      "janela_analise_meses": 24,
      "mudanca_estrutural": false,
      "origem_motor": "stats_engine",
      "versao_modelo": "v1"
    }
  ]
}
```

`POST /v1/orcamento/simular`

```json
{
  "operador": "op_01",
  "correlation_id": "corr_api_orc_001",
  "periodo_referencia": "2026-02-01",
  "categoria_id": "cat_a",
  "valor_compra_sugerida": 700,
  "orcamento_total_periodo": 1000,
  "orcamento_categoria_periodo": 600,
  "consumo_atual_total": 500,
  "consumo_atual_categoria": 100,
  "aprovacao_excecao": {
    "aprovado_por": "gestor_01",
    "motivo": "Item critico",
    "valor_aprovado": 700
  }
}
```

Rodar testes de integração SQL:

```bash
cd WMS
cp .env.example .env
docker compose -f docker-compose.postgres.yml --env-file .env up -d
./scripts/run_sql_tests.sh
```
