# Caso de Uso: Inventário Cíclico com Curva ABC

## 1. Objetivo

Executar contagens rotativas de estoque sem interromper a operação, priorizando itens com maior risco de divergência e maior impacto financeiro.

## 2. Atores

- Sistema de Estoque
- Operador de Inventário
- Gestor de Estoque

## 3. Pré-condições

- Itens classificados por Curva ABC.
- Histórico mínimo de movimentação disponível.
- Regras de frequência configuradas por classe.

## 4. Gatilho

Início do ciclo diário de inventário.

## 5. Fluxo Principal

1. O sistema seleciona a lista de itens a contar no dia.
2. A seleção prioriza itens conforme classe ABC e critérios de risco.
3. O operador realiza contagem física dos itens selecionados.
4. O sistema compara saldo físico x saldo sistêmico.
5. Se houver divergência, o sistema registra ocorrência e solicita tratativa.
6. O sistema recalcula indicadores de acuracidade por item, classe e depósito.

### Nota Operacional: "Foto da Contagem" (Snapshot)

Em cada contagem, o sistema deve registrar uma foto do estado atual (snapshot), incluindo imagem e metadados da conferência. A lógica é parecida com um commit: fica salvo um retrato auditável daquele momento.

Esse histórico permite:

- comparar a contagem atual com a última contagem do mesmo item/local;
- apoiar análise de acuracidade por operador e por ciclo;
- melhorar rastreabilidade em casos de divergência recorrente.

## 6. Regras de Negócio

- **Classe A:** maior frequência de contagem (semanal ou até 2x por mês).
- **Classe B:** frequência intermediária (ex.: mensal).
- **Classe C:** menor frequência (ex.: trimestral).
- Itens de alto valor agregado ou alto risco de furto podem ter frequência elevada independentemente da classe.
- O inventário cíclico não deve exigir paralisação total da operação.

## 7. Fluxos Alternativos

- **Divergência crítica:** quando o desvio supera limite configurado, bloquear nova reposição até validação do gestor.
- **Item não localizado:** registrar ocorrência, abrir investigação e reprogramar contagem de confirmação.
- **Mudança de perfil do item:** se aumento de movimentação for persistente, sinalizar revisão de classe ABC.

## 8. Pós-condições

- Saldos atualizados após validação.
- Divergências registradas com trilha de auditoria.
- Plano de contagem futuro ajustado com base em risco e acuracidade.

## 9. Indicadores de Sucesso

- Acuracidade de estoque por classe.
- Percentual de divergências por ciclo.
- Tempo médio de tratativa de divergências.
- Redução de perdas por erro de saldo.

## 10. Resultado Esperado

Manter alta confiabilidade do estoque com contagens contínuas e direcionadas, reduzindo impacto operacional e financeiro de inventários gerais.
