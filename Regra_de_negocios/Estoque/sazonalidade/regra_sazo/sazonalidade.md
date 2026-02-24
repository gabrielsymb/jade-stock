# Regra de Negócio: Sazonalidade

## 1. Objetivo

Detectar padrões sazonais de demanda e ajustar previsão e cobertura com antecedência, reduzindo ruptura em períodos de alta e excesso em períodos de baixa.

## 2. Entradas Mínimas

- histórico de vendas mensal ou semanal;
- janela mínima de 24 meses;
- classe ABC do item;
- lead time;
- variáveis exógenas disponíveis (clima, feriados, eventos, preço, promoção).

## 3. Regras de Detecção

- Comparar períodos equivalentes entre anos (YoY).
- Marcar como sazonal quando houver repetição consistente de direção e magnitude de desvio.
- Exigir pelo menos dois ciclos anuais completos para ativar sinal sazonal.

## 4. Regras de Validação Estatística

- Separar tendência, sazonalidade e ruído por decomposição temporal.
- Validar desempenho em backtest temporal.
- Ativar automação somente se o modelo sazonal superar baseline sem sazonalidade de forma consistente.
- Rebaixar confiança quando houver mudança estrutural de padrão.

## 5. Sazonalidade vs Variabilidade

- **Classe A:** maior confiabilidade para ajuste automático sazonal.
- **Classe C:** exigir evidência mais forte para evitar confundir ruído com sazonalidade.
- Em itens de alta variabilidade, permitir modo semiautomático com revisão humana.

## 6. Regras de Execução Operacional

- Antecipar aumento de cobertura antes da janela de alta sazonal, respeitando lead time.
- Reduzir cobertura antes da janela de baixa sazonal para evitar excesso.
- Manter limites de shelf life, capital e capacidade operacional.

## 7. Uso de Variáveis Exógenas

- Fatores externos devem entrar como variáveis explicativas do modelo.
- Não hardcodar regras específicas de item, clima ou evento.
- Registrar impacto estimado de cada variável nas recomendações.

## 8. Alertas Obrigatórios

- `sinal_sazonal_baixa_confianca`
- `mudanca_estrutural_detectada`
- `conflito_sazonalidade_vs_shelf_life`
- `revisao_manual_recomendada`

## 9. Saídas Esperadas do Módulo

- status de sazonalidade (`ativo`, `inativo`, `baixa_confianca`);
- fator sazonal por período;
- cobertura recomendada pré e pós ajuste sazonal;
- justificativa da recomendação;
- alertas acionados.

## 10. Diretriz Final

Sazonalidade deve virar ação automática apenas quando houver evidência estatística e viabilidade operacional. Sem esses critérios, o sistema deve adotar política conservadora.
