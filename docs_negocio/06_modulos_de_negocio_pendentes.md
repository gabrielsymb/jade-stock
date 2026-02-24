# Módulos de Negócio Pendentes (Passo 1)

Objetivo deste documento: congelar o que falta no WMS além do core já pronto, com ordem de execução e definição de pronto.

## Status atual já pronto

- Movimentação
- Ajuste
- Recebimento
- Inventário Cíclico
- Avarias
- Kanban de Reposição
- Curva ABCD operacional
- Giro operacional
- Sazonalidade operacional
- Governança Orçamentária operacional

## Ordem recomendada de implementação

Sem módulos pendentes no escopo atual.

## 1) Avarias (concluído)

Base de regra: `Regra_de_negocios/Estoque/avarias/regra_avarias/avarias.md`

Contrato de caso de uso (proposto):

- Entrada:
  - `sku_id`
  - `endereco_codigo`
  - `quantidade_avariada`
  - `tipo_avaria` (`degustacao`, `movimentacao`, `outros`)
  - `origem_processo`
  - `motivo`
  - `operador`
  - `correlation_id`
- Regras:
  - motivo obrigatório;
  - quantidade > 0;
  - SKU ativo e endereço válido;
  - não permitir baixa maior que saldo disponível;
  - registrar perda com rastreabilidade.
- Saída:
  - `avaria_id`
  - `movimentacao_id`
  - `evento_emitido`

Eventos mínimos:

- `avaria_registrada`
- `estoque_ajustado_por_avaria`

Implementado:

- use case `RegistrarAvariaEstoque` com validações de:
  - motivo obrigatório;
  - quantidade > 0;
  - SKU ativo;
  - endereço válido;
  - saldo suficiente.
- endpoint `POST /v1/avarias` (e alias `/avarias`);
- persistência via `movimentacao_estoque` + `event_store`;
- testes unitários (`tests/test_registrar_avaria_estoque.py`);
- testes de API `inmemory` e `postgres`.

## 2) Kanban de Reposição (concluído)

Base de regra: `Regra_de_negocios/Estoque/kanban/regra_kanban/kanban.md`

Contrato de caso de uso (proposto):

- Entrada:
  - `sku_id`
  - parâmetros de faixa (verde/amarelo/vermelho)
  - `operador`
  - `correlation_id`
- Regras:
  - SKU elegível para Kanban;
  - faixas válidas e consistentes;
  - transição de faixa auditável.
- Saída:
  - status do cartão (`verde|amarelo|vermelho`)
  - `evento_emitido`

Eventos mínimos:

- `kanban_faixa_atualizada`
- `kanban_reposicao_disparada`

Implementado:

- use case `RegistrarPoliticaKanban` com validações de:
  - SKU ativo;
  - elegibilidade para Kanban ativo;
  - motivo obrigatório;
  - consistência de faixas (`verde >= amarela >= vermelha`).
- endpoint `POST /v1/kanban/politicas` (e alias `/kanban/politicas`);
- persistência em `kanban_politica` e `kanban_historico`;
- eventos:
  - `kanban_politica_atualizada`;
  - `kanban_faixa_atualizada`;
  - `kanban_reposicao_disparada` (amarelo/vermelho).
- testes unitários + API (`inmemory` e `postgres`) e integração Postgres de caso de uso.

## 3) Curva ABCD operacional (concluído)

Base de regra: `Regra_de_negocios/Estoque/curva/regra_abc/curva_abcd.md`

Objetivo técnico:

- sair de documentação para cálculo efetivo de classe por SKU e recomendação de cobertura.

Implementado:

- use case `ProcessarCurvaABCD` com processamento determinístico em lote;
- classificação por participação acumulada de impacto econômico (`A/B/C/D`);
- aplicação de regras:
  - cobertura por classe;
  - colchão de variabilidade;
  - limitação por shelf life;
  - contenção por baixo giro crítico;
- persistência em `politica_reposicao`;
- endpoint `POST /v1/curva-abcd/processar` (alias `/curva-abcd/processar`);
- testes unitários + API (`inmemory` e `postgres`) + integração PostgreSQL de caso de uso.

## 4) Giro operacional (concluído)

Base de regra: `Regra_de_negocios/Estoque/giro/regra_giro/giro_estoque.md`

Objetivo técnico:

- calcular giro/cobertura por período e emitir alertas de desvio.

Implementado:

- use case `ProcessarGiroEstoque` com fórmulas oficiais:
  - `cobertura_dias = estoque_atual / venda_media_diaria_prevista`
  - `giro_periodo = total_vendido_periodo / estoque_medio_periodo`
- regras por classe com alertas obrigatórios:
  - `giro_abaixo_meta_classe_a`
  - `capital_imobilizado_excessivo`
  - `ruptura_recorrente_item_c`
  - `revisao_politica_reposicao`
- persistência em `politica_reposicao`;
- endpoint `POST /v1/giro/processar` (alias `/giro/processar`);
- testes unitários + API (`inmemory` e `postgres`) + integração PostgreSQL de caso de uso.

## 5) Sazonalidade operacional (concluído)

Base de regra: `Regra_de_negocios/Estoque/sazonalidade/regra_sazo/sazonalidade.md`

Observação de arquitetura:

- no WMS, apenas aplicação determinística dos sinais.
- detecção estatística/ML permanece desacoplada.

Implementado:

- use case `ProcessarSazonalidadeOperacional`;
- ingestão de sinal externo via `sinal_externo` (sem inferência no WMS);
- aplicação determinística sobre `politica_reposicao` com guardrails:
  - baixa confiança;
  - mudança estrutural;
  - conflito com shelf life;
- endpoint `POST /v1/sazonalidade/processar` (alias `/sazonalidade/processar`);
- eventos:
  - `sazonalidade_item_processada`
  - `sazonalidade_processada`;
- testes unitários + API (`inmemory` e `postgres`) + integração PostgreSQL de caso de uso.

## 6) Governança Orçamentária operacional (concluído)

Base de regra: `Regra_de_negocios/Estoque/governanca_orcamentaria/regra_orcamentaria.md`

Objetivo técnico:

- validar viabilidade financeira antes de confirmar reposição.

Implementado:

- use case `ProcessarGovernancaOrcamentaria` com simulação e decisão;
- persistência em:
  - `orcamento_periodo`
  - `orcamento_categoria`
  - `aporte_externo`
  - `compra_excecao`
- alertas obrigatórios:
  - `compra_acima_orcamento_categoria`
  - `compra_acima_orcamento_total`
  - `canibalizacao_entre_categorias`
  - `excecao_sem_aprovacao`
  - `aporte_externo_sem_rastreabilidade`
- endpoint `POST /v1/orcamento/simular` (alias `/orcamento/simular`);
- testes unitários + API (`inmemory` e `postgres`) + integração PostgreSQL de caso de uso.

## Critério de conclusão do Passo 1

Passo 1 será considerado concluído quando este backlog estiver aprovado por você (ordem, escopo e definição de pronto).
