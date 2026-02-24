# Casos de Uso WMS (Sem Codigo)

## 1. Objetivo

Descrever o comportamento esperado do sistema em operacao real, com foco em decisao de negocio e consistencia entre modulos.

## 2. Formato Padrao

Para cada caso:

- problema de negocio;
- gatilho;
- entradas;
- regra de decisao;
- saidas;
- excecoes;
- metricas.

## 3. Casos de Uso Prioritarios

## UC-01 Cadastrar SKU

- Problema: falta de identificacao por variacao gera ruptura oculta e excesso.
- Gatilho: novo item/variacao entra no portifolio.
- Entradas: `sku_codigo`, `sku_nome`, variacoes, `ean` (opcional), unidade.
- Regra: toda variacao fisica distinta deve virar SKU distinto.
- Saidas: SKU ativo e apto a receber saldo.
- Excecoes: codigo duplicado, variacao incompleta.
- Metricas: integridade de cadastro SKU.

## UC-02 Enderecar SKU

- Problema: sem localizacao valida, operacao perde produtividade e acuracidade.
- Gatilho: cadastro de SKU ou recebimento sem endereco definido.
- Entradas: `sku_id`, `endereco_codigo`, `tipo_endereco`.
- Regra: nao permitir SKU vendavel sem endereco ativo.
- Saidas: vinculo SKU-endereco registrado.
- Excecoes: endereco inexistente, endereco inativo, ocupacao invalida.
- Metricas: taxa de acerto de localizacao.

## UC-03 Receber e Conferir Nota

- Problema: entrada sem conferencia distorce saldo e compra futura.
- Gatilho: chegada de nota fiscal.
- Entradas: nota, itens, quantidades esperadas e conferidas.
- Regra: divergencia exige classificacao (`falta`, `sobra`, `avaria`).
- Saidas: saldo atualizado + historico de divergencia.
- Excecoes: item nao cadastrado, SKU sem endereco, nota inconsistente.
- Metricas: divergencia no recebimento.

## UC-04 Registrar Avaria

- Problema: perda nao registrada gera saldo vendavel falso.
- Gatilho: deteccao de dano em recebimento, armazenagem ou degustacao.
- Entradas: `sku_id`, quantidade, motivo, origem.
- Regra: motivo obrigatorio e movimentacao para tipo `avariado`/`bloqueado`.
- Saidas: saldo vendavel reduzido + perda registrada.
- Excecoes: motivo ausente, quantidade invalida.
- Metricas: perda por avaria.

## UC-05 Transferir Estoque

- Problema: saldo correto no total, mas errado por endereco.
- Gatilho: reposicao interna ou reorganizacao fisica.
- Entradas: `sku_id`, endereco origem/destino, quantidade.
- Regra: validar saldo na origem e elegibilidade do destino.
- Saidas: saldo por endereco atualizado + historico.
- Excecoes: estoque insuficiente, endereco invalido.
- Metricas: acuracidade por endereco.

## UC-06 Inventario Ciclico

- Problema: divergencia fisico x sistemico ao longo do tempo.
- Gatilho: agenda ciclica por classe/criticidade.
- Entradas: SKU, endereco, quantidade contada, evidencia da contagem.
- Regra: toda divergencia gera ajuste auditavel.
- Saidas: saldo conciliado e trilha de ajuste.
- Excecoes: contagem duplicada, item bloqueado sem permissao.
- Metricas: acuracidade de inventario.

## UC-07 Sugerir Reposicao

- Problema: compra por intuicao causa excesso ou ruptura.
- Gatilho: janela de reposicao aberta.
- Entradas: giro, cobertura, lead time, sazonalidade, validade.
- Regra: sugestao deve respeitar risco de vencimento e politica por classe.
- Saidas: lista sugerida por prioridade.
- Excecoes: historico insuficiente, conflito de parametros.
- Metricas: ruptura evitada e excesso evitado.

## UC-08 Validar Orcamento

- Problema: sugestao boa operacionalmente, inviavel financeiramente.
- Gatilho: confirmacao de compra.
- Entradas: valor sugerido, orcamento disponivel, aporte externo.
- Regra: bloquear ou reescalar quando exceder limite.
- Saidas: compra aprovada, parcial ou bloqueada.
- Excecoes: sem parametros de orcamento.
- Metricas: consumo orcamentario e aderencia ao plano.

## UC-09 Operar Kanban

- Problema: falta de prioridade visual para itens recorrentes.
- Gatilho: consumo muda faixa do SKU (verde/amarelo/vermelho).
- Entradas: saldo atual, faixa parametrizada, elegibilidade do SKU.
- Regra: kanban so para SKU recorrente e previsivel.
- Saidas: quadro visual + fila de reposicao.
- Excecoes: SKU nao elegivel, parametrizacao invalida.
- Metricas: ruptura evitada por kanban.

## 4. Regra Arquitetural de Execucao

1. Casos de uso do WMS executam apenas decisoes deterministicas.
2. Quando houver necessidade de previsao/inferencia, o caso de uso deve consumir parametro externo (estatistica/ML), nunca inferir internamente.
3. O WMS deve registrar qual sinal externo foi aplicado (versao, data e origem) para auditoria.
