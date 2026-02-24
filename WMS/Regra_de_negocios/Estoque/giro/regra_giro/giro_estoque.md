# Regra de Negócio: Giro de Estoque

## 1. Objetivo

Medir eficiência de renovação de estoque e usar o indicador como gatilho automático para reposição e controle de capital.

## 2. Definições

- **Cobertura:** por quantos dias o estoque atual sustenta a demanda prevista.
- **Giro:** quantas vezes o estoque médio foi renovado em um período.
- **Relação prática:** giro alto tende a corresponder a cobertura baixa; giro baixo tende a cobertura alta.

## 3. Entradas Mínimas

- estoque atual;
- venda média diária prevista;
- total vendido no período;
- estoque médio do período;
- classe ABC do item.

## 4. Fórmulas Oficiais

- `cobertura_dias = estoque_atual / venda_media_diaria_prevista`
- `giro_periodo = total_vendido_periodo / estoque_medio_periodo`

## 5. Regras por Classe

- **Classe A:** alvo de giro alto e cobertura baixa.
- **Classe B:** faixa intermediária de giro e cobertura.
- **Classe C:** giro mais baixo aceitável, com cobertura maior para reduzir risco de ruptura por variabilidade.

## 6. Gatilhos de Reposição

- Quando giro de item A cair abaixo da meta, reduzir tamanho de lote.
- Quando giro de item A cair abaixo da meta, aumentar frequência de compra.
- Quando giro de item A cair abaixo da meta, emitir alerta de capital imobilizado.
- Quando item C apresentar ruptura recorrente, elevar cobertura dentro dos limites de validade e orçamento.
- Quando item C apresentar ruptura recorrente, ajustar parâmetro de segurança.

## 7. Alertas Obrigatórios

- `giro_abaixo_meta_classe_a`
- `capital_imobilizado_excessivo`
- `ruptura_recorrente_item_c`
- `revisao_politica_reposicao`

## 8. Saídas Esperadas do Módulo

- giro calculado por item e período;
- cobertura calculada e alvo recomendado;
- desvio frente à meta da classe;
- ação sugerida de reposição;
- alertas acionados.

## 9. Diretriz Final

O indicador de giro não é apenas descritivo. Ele deve dirigir decisões de compra para equilibrar disponibilidade e eficiência financeira, respeitando o perfil de cada classe.
