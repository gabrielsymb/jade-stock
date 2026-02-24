# Regra de Negócio: Curva ABCD

## 1. Objetivo

Classificar itens por importância econômica e comportamento de demanda para definir políticas automáticas de cobertura, reposição e risco.

## 2. Premissas de Negócio

- Itens citados como exemplo são apenas didáticos e não devem ser hardcoded.
- A classificação deve ser orientada por dados do usuário.
- A decisão não depende apenas de preço unitário; depende de impacto total e variabilidade.

## 3. Entradas Mínimas

- histórico de vendas por item;
- valor unitário ou margem;
- estoque atual;
- parâmetros de período de análise;
- regras de cobertura por classe.

## 4. Regras de Classificação

- **Classe A:** poucos SKUs, maior impacto no faturamento, menor variabilidade, alta previsibilidade.
- **Classe B:** intermediária entre A e C.
- **Classe C:** muitos SKUs, menor contribuição individual, maior variabilidade, menor previsibilidade.
- **Classe D/E (opcional):** itens estratégicos de imagem/portfólio com baixo giro e alta sensibilidade de capital.

## 5. Regras de Cobertura e Reposição

- **Cobertura inversa:** quanto maior o giro e previsibilidade, menor a cobertura alvo.
- **Classe A:** cobertura baixa, reposição frequente, lotes menores.
- **Classe B:** cobertura intermediária.
- **Classe C:** cobertura maior para absorver incerteza de demanda.
- **Classe D/E estratégica:** manter mínimo operacional (ex.: 1 unidade) e bloquear sugestão de lote elevado.

## 6. Tratamento de Variabilidade

- Itens com oscilação elevada não podem receber cobertura agressivamente baixa.
- Se variabilidade exceder limite configurado, o sistema deve adicionar colchão de segurança.
- Itens de baixa venda com alta oscilação podem migrar de B para política de C.

## 7. Estoque Morto (Folha Seca)

- Se um item não tiver saída por `X` dias (ex.: 90), marcar como `baixo_giro_critico`.
- Para itens marcados, reduzir recomendação de compra para mínimo.
- Para itens marcados, gerar alerta de capital imobilizado.
- Para itens marcados, exigir justificativa para recompras acima do mínimo.

## 8. Tabela de Referência de Política

| Classe | Cobertura Alvo | Giro Esperado | Estratégia |
| --- | --- | --- | --- |
| A | Baixa | Alto | Compras frequentes, capital enxuto |
| B | Média | Médio | Política equilibrada |
| C | Alta | Baixo | Estoque de segurança contra variabilidade |
| D/E | Mínima estratégica | Muito baixo | Disponibilidade de vitrine, sem lote grande |

## 9. Alertas Obrigatórios

- `risco_ruptura`: cobertura abaixo do mínimo da classe.
- `capital_imobilizado`: cobertura acima do máximo recomendado para classe A/B.
- `baixo_giro_critico`: item sem saída acima do limite.
- `revisao_classificacao`: mudança abrupta de padrão de venda.

## 10. Saídas Esperadas do Módulo

- classe do item (A/B/C/D/E);
- cobertura recomendada em dias;
- nível de confiança da recomendação;
- justificativa resumida da decisão;
- alertas acionados.
