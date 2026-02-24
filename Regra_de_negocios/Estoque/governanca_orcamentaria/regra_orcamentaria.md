# Regra de Negócio: Governança Orçamentária de Compra

## 1. Objetivo

Controlar decisões de compra sem perder simplicidade operacional, equilibrando:

- caixa unificado da empresa;
- limites de compra por categoria/classe;
- flexibilidade para exceções (aporte externo).

## 2. Princípio de Projeto

Simples por padrão, flexível por exceção, rastreável sempre.

## 3. Escopo (MVP)

- limite de compra total por período;
- limite de compra por categoria (soft cap);
- alerta de canibalização de orçamento entre categorias;
- exceção aprovada para compra acima do limite;
- registro de aporte externo com origem e destino.

## 4. Conceitos

- **Caixa unificado:** visão financeira consolidada da empresa.
- **Orçamento de compra:** limite gerencial para controlar consumo de capital.
- **Soft cap:** limite recomendável que gera alerta, mas não bloqueia automaticamente.
- **Hard cap (opcional):** limite bloqueante, usado apenas em cenários críticos.
- **Aporte externo:** entrada extraordinária de recurso para suportar compra.

## 5. Regras de Decisão

1. Toda sugestão de compra deve ser comparada ao orçamento disponível no período.
2. Se a compra ultrapassar o limite de categoria, gerar alerta de impacto.
3. Se ultrapassar limite total, exigir aprovação com justificativa.
4. Exceções aprovadas devem ficar auditáveis (quem aprovou, quando, motivo).
5. Aporte externo deve ser registrado separadamente do caixa operacional padrão.

## 6. Regras para Aporte Externo

Quando houver injeção de recurso externo, registrar:

- valor;
- origem;
- período de validade (se aplicável);
- destino (`livre` ou categoria específica);
- responsável pela aprovação.

Sem esse registro, o sistema não deve tratar o aporte como orçamento disponível.

## 7. Alertas Obrigatórios

- `compra_acima_orcamento_categoria`
- `compra_acima_orcamento_total`
- `canibalizacao_entre_categorias`
- `excecao_sem_aprovacao`
- `aporte_externo_sem_rastreabilidade`

## 8. Como Conecta com as Outras Regras de Estoque

- **Curva ABC (`curva_abcd.md`)**: define prioridade operacional; governança define quanto pode ser investido.
- **Shelf Life (`shelf_life.md`)**: impede compra acima da validade, mesmo que haja orçamento.
- **Giro (`giro_estoque.md`)**: ajusta frequência e tamanho de compra; orçamento limita execução.
- **Sazonalidade (`sazonalidade.md`)**: pode elevar necessidade de compra em períodos de alta; governança controla impacto em caixa.
- **Cíclico (`ciclico.md`)**: melhora acuracidade para comprar melhor; governança evita distorção por excesso.
- **Avarias (`avarias.md`)**: perdas reduzem disponibilidade e podem exigir recompra; governança evita reposição descontrolada.

## 9. Saídas Esperadas do Módulo

- orçamento disponível por período;
- consumo por categoria e total;
- impacto da compra sugerida no orçamento;
- trilha de exceções/aprovações;
- histórico de aportes externos.

## 10. Resultado Esperado

Evitar falta de capital em categorias críticas sem engessar a operação, mantendo decisões de compra tecnicamente corretas e financeiramente sustentáveis.
