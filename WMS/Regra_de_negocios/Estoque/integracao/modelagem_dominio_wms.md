# Modelagem de Dominio WMS (Sem Codigo)

## 1. Objetivo

Transformar as regras de negocio ja documentadas em um modelo de dominio unico, claro e implementavel pelo time tecnico.

## 2. Escopo de Dominio

Este modelo cobre o dominio de estoque/logistica do WMS enxuto:

- cadastro e identificacao de SKU;
- localizacao e enderecamento;
- recebimento, movimentacao e contagem;
- perdas/avarias;
- reposicao (curva, giro, sazonalidade, kanban);
- governanca de compra por orcamento.

## 3. Entidades Principais

## SKU

Representa a menor unidade de controle de estoque.

Campos minimos:

- `sku_id`
- `sku_codigo`
- `sku_nome`
- `item_master_id`
- `ean`
- `unidade_medida`
- `status_ativo`

## Endereco

Representa a localizacao fisica/logica do estoque.

Campos minimos:

- `endereco_codigo`
- `zona_codigo`
- `prateleira_codigo`
- `posicao_codigo`
- `tipo_endereco` (`venda`, `reserva`, `avariado`, `bloqueado`)

## SaldoEstoque

Representa saldo por SKU e por endereco.

Campos minimos:

- `sku_id`
- `endereco_codigo`
- `saldo_disponivel`
- `saldo_avariado`
- `saldo_bloqueado`
- `saldo_total`

## LoteValidade

Representa controle de validade quando aplicavel.

Campos minimos:

- `lote_id`
- `sku_id`
- `validade_data`
- `shelf_life_dias`
- `risco_vencimento`

## MovimentacaoEstoque

Representa qualquer mudanca de saldo (entrada, saida, transferencia, ajuste, avaria).

Campos minimos:

- `movimentacao_id`
- `tipo_movimentacao`
- `sku_id`
- `endereco_origem`
- `endereco_destino`
- `quantidade`
- `motivo`
- `created_at`
- `created_by`
- `correlation_id`

## Recebimento

Representa entrada de nota e conferencia fisica.

Campos minimos:

- `recebimento_id`
- `nota_fiscal_numero`
- `fornecedor_id`
- `status_conferencia`
- `possui_avaria`
- `divergencia_quantidade`

## PoliticaReposicao

Representa parametros de decisao por SKU/classe.

Campos minimos:

- `sku_id`
- `classe_abc`
- `giro_periodo`
- `cobertura_dias`
- `lead_time_dias`
- `fator_sazonal`
- `kanban_ativo`
- `faixa_kanban`

## OrcamentoCompra

Representa limite financeiro para reposicao.

Campos minimos:

- `orcamento_total_periodo`
- `orcamento_categoria_periodo`
- `consumo_orcamento`
- `aporte_externo_valor`

## 4. Regras de Negocio (Invariantes)

1. Nao pode haver estoque negativo em nenhuma operacao.
2. Toda movimentacao deve gerar historico auditavel.
3. SKU inativo nao pode receber movimentacao de venda/reposicao.
4. SKU nao pode existir sem identificacao unica (`sku_id` + `sku_codigo`).
5. Endereco deve ser valido e ativo para receber saldo.
6. Avaria deve ter motivo obrigatorio e mover saldo para endereco/tipo bloqueado.
7. Recebimento com divergencia exige classificacao (ok, falta, sobra, avaria).
8. Reposicao deve respeitar validade, cobertura e lead time.
9. Recomendacao de compra deve respeitar governanca orcamentaria.
10. Kanban so pode ser ativado para SKU elegivel (recorrencia e baixa variabilidade).

## 5. Agregados (limites de consistencia)

- `CadastroSKU`: SKU + variacoes obrigatorias.
- `EstoqueLocalizado`: SaldoEstoque + Endereco.
- `RecebimentoConferencia`: Recebimento + itens conferidos + divergencias.
- `AvariaPerda`: registro de avaria + destino bloqueado + impacto de saldo.
- `Reposicao`: PoliticaReposicao + sugestao + validacoes de risco e orcamento.

## 6. Casos de Uso Prioritarios

1. Cadastrar SKU.
2. Enderecar SKU.
3. Registrar recebimento com conferencia.
4. Registrar avaria com motivo.
5. Transferir estoque entre enderecos.
6. Executar inventario ciclico e ajustar divergencia.
7. Gerar sugestao de reposicao.
8. Validar sugestao por orcamento.
9. Operar quadro kanban para SKUs elegiveis.

## 7. Ordem de Implementacao (recomendada)

1. Congelar este modelo de dominio.
2. Validar invariantes com operacao.
3. Detalhar casos de uso com entrada/saida/erro.
4. Desenhar contratos de API/eventos.
5. Implementar aplicacao.
6. Persistir banco alinhado ao dominio.

## 8. Criterio de Qualidade

Se um endpoint, tabela ou tela nao se conectar a estas entidades/regras, ele nao entra no MVP.

## 9. Fronteira WMS (Deterministico) x Estatistica/ML (Probabilistico)

1. O WMS executa apenas logica deterministica baseada em regras explicitas.
2. O WMS pode agregar, transformar e aplicar politicas operacionais sem inferencia estatistica.
3. O WMS nao faz deteccao automatica de padroes, previsao ou classificacao probabilistica.
4. Motores de estatistica/ML sao responsaveis por sazonalidade, anomalias, previsoes e recomendacoes probabilisticas.
5. Motores externos consomem dados do WMS e retornam sinais/parametros.
6. O WMS consome esses sinais como entrada de politica e executa a operacao.
7. Essa separacao e obrigatoria para evitar acoplamento indevido e perda de manutenibilidade.
