# Regra de Negócio: Kanban de Reposição

## 1. Objetivo

Implementar reposição visual e puxada para itens de consumo recorrente, reduzindo ruptura e superestoque com sinalização simples e operacional.

## 2. Conceito

Kanban é um mecanismo visual de controle de fluxo baseado em "cartões".  
No contexto do sistema, cada cartão representa uma necessidade de reposição de um SKU elegível.

## 3. Princípio de Funcionamento

O gatilho de reposição ocorre pelo consumo, não por produção empurrada.

Fluxo resumido:

1. item é vendido/consumido;
2. sistema atualiza posição do cartão no quadro;
3. operador prioriza reposição conforme urgência visual;
4. após reposição, cartão retorna ao estado de controle.

## 4. Lógica Visual (Cores)

- `verde`: estoque em faixa segura;
- `amarelo`: consumo em faixa de atenção;
- `vermelho`: atingiu estoque de segurança, reposição urgente.

## 5. Critérios de Elegibilidade

Kanban deve ser ativado apenas para SKUs com padrão adequado:

- baixa variabilidade de consumo;
- alta frequência de saída;
- recorrência consistente de demanda;
- lead time relativamente estável.

## 6. Itens Não Elegíveis

Não aplicar Kanban para:

- itens sob encomenda/customizados;
- itens de baixa recorrência;
- SKUs com demanda altamente errática sem histórico suficiente.

## 7. Regras Obrigatórias do Sistema

1. SKU só entra no Kanban se atender critérios mínimos de elegibilidade.
2. Faixas (verde/amarelo/vermelho) devem ser parametrizadas por SKU.
3. Reposição sugerida deve respeitar shelf life, orçamento e capacidade.
4. Se quadro estiver "verde cheio", sistema deve despriorizar nova reposição.
5. Toda transição de cor deve ser auditável.

## 8. Integração com Módulos Existentes

- **SKU:** identifica o item monitorado.
- **Giro e Curva:** base para selecionar SKUs aderentes ao Kanban.
- **Sazonalidade:** ajusta faixas por período.
- **Shelf Life:** limita quantidade sugerida.
- **Governança Orçamentária:** valida viabilidade financeira da reposição.
- **Avarias e Cíclico:** corrigem saldo para manter o quadro confiável.

## 9. Alertas Obrigatórios

- `kanban_sku_nao_elegivel`
- `kanban_faixa_vermelha_ativa`
- `kanban_parametrizacao_invalida`
- `kanban_reposicao_bloqueada_por_validade`
- `kanban_reposicao_bloqueada_por_orcamento`

## 10. Saídas Esperadas

- quadro visual de reposição por SKU;
- fila priorizada de compra/produção;
- histórico de transição de cartões;
- indicadores de ruptura evitada e excesso evitado.

## 11. Resultado Esperado

Aumentar autonomia operacional e velocidade de reposição em itens recorrentes, mantendo disciplina visual e evitando aplicação indevida do método em produtos não aderentes.
