# Regra de Negócio: Shelf Life e Cobertura

## 1. Objetivo

Garantir que recomendações de estoque respeitem prazo de validade, evitando perda por vencimento sem comprometer totalmente o nível de serviço.

## 2. Princípio Central

O shelf life define o limite superior de cobertura. Nenhuma recomendação de cobertura pode ultrapassar a janela de validade útil do item.

## 3. Entradas Mínimas

- shelf life em dias;
- data de fabricação/entrada (quando aplicável);
- histórico de vendas;
- classe ABC do item;
- lead time de reposição.

## 4. Regras Obrigatórias

- `cobertura_recomendada <= shelf_life_util`.
- `shelf_life_util` deve considerar margem de segurança operacional (ex.: transporte, conferência e exposição).
- Em caso de conflito entre regra ABC e validade, prevalece a validade.

## 5. Conflito Típico com Classe C

- Itens C tendem a pedir cobertura mais alta por variabilidade.
- Se o shelf life for curto, a cobertura deve ser reduzida ao limite seguro.
- O sistema deve registrar que houve redução por perecibilidade.

## 6. Comportamento Esperado por Classe

- **Classe A:** normalmente já opera com baixa cobertura e alto giro, com menor risco de vencimento.
- **Classe C:** exige regra explícita de contenção para evitar compra acima da validade.

## 7. Alertas Obrigatórios

- `alerta_perecibilidade`: quando cobertura calculada pela demanda excede validade útil.
- `alerta_risco_ruptura_por_validade`: quando redução por validade aumenta risco de falta.
- `alerta_perda_potencial`: quando estoque atual já excede consumo projetado dentro da validade.

## 8. Saídas Esperadas do Módulo

- cobertura final ajustada por validade;
- motivo do ajuste (`limitado_por_shelf_life`);
- risco residual estimado (ruptura vs perda);
- recomendação de compra revisada.

## 9. Diretriz Final

Validade é restrição física e financeira. Quando houver conflito entre "segurança de cobertura" e "risco de vencimento", o sistema deve operar de forma conservadora e transparente, priorizando estoque vendável.
