# Regra de Uso: Avarias, Degustação e Movimentação

## 1. Objetivo

Padronizar o tratamento de avarias no recebimento de notas e na movimentação interna, garantindo rastreabilidade, impacto correto em estoque e visibilidade financeira.

## 2. Escopo

- entrada de nota fiscal de compra;
- registro de avaria de degustação;
- registro de avaria por movimentação (quebra, vazamento, dano logístico);
- baixa de estoque e lançamento de motivo.

## 3. Conceitos

- **Avaria:** perda parcial ou total de item por dano físico, validade comprometida ou inutilização comercial.
- **Avaria de degustação:** baixa intencional para prova/ação comercial, sem venda direta.
- **Avaria de movimentação:** dano ocorrido em recebimento, armazenagem, separação, transporte ou transferência.

## 4. Regra Obrigatória na Entrada de Notas

Ao lançar uma nota fiscal, o sistema deve obrigatoriamente perguntar:

- `Esta nota possui avarias?` (`sim` ou `não`)

Se a resposta for `sim`, o sistema deve exigir:

- item afetado;
- quantidade avariada;
- tipo de avaria (`degustacao`, `movimentacao`, `outros`);
- responsável pelo lançamento;
- observação obrigatória;
- evidência opcional (foto/documento), conforme política da empresa.

## 5. Regras de Estoque

- Quantidade avariada não pode entrar como estoque disponível para venda.
- O sistema deve separar saldos por status: `disponivel`, `avariado` e `bloqueado` (quando necessário para análise).
- Baixa por avaria deve gerar movimentação própria, com trilha de auditoria.

## 6. Regras de Movimentação

- Toda avaria deve ter origem de processo identificada: `recebimento`, `armazenagem`, `transferencia`, `separacao_expedicao` ou `acao_comercial_degustacao`.
- Movimentações com avaria devem atualizar indicadores de perdas por setor e por usuário.

## 7. Regras Específicas de Degustação

- Avaria de degustação deve usar motivo dedicado e centro de custo de marketing/comercial (quando aplicável).
- Quantidade destinada à degustação deve ser aprovada conforme alçada configurada.
- O sistema deve impedir que item marcado como degustação retorne automaticamente ao saldo vendável.

## 8. Regras Financeiras e Fiscais

- O sistema deve apurar custo de perda por item, categoria e período.
- Notas com avaria devem ficar sinalizadas para conciliação fiscal/contábil.
- Quando houver devolução ao fornecedor, registrar vínculo entre avaria e documento de devolução.

## 9. Alertas Obrigatórios

- `nota_com_avaria_sem_detalhe`
- `quantidade_avariada_maior_que_recebida`
- `avaria_sem_motivo_valido`
- `avaria_movimentacao_recorrente`
- `degustacao_acima_limite`

## 10. Saídas Esperadas do Módulo

- saldo atualizado por status (`disponivel`, `avariado`, `bloqueado`);
- relatório de perdas por tipo de avaria;
- rastreabilidade completa por nota, item e usuário;
- indicadores de recorrência para ações corretivas.

## 11. Diretriz Final

O sistema deve tratar avaria como evento operacional crítico, não como ajuste genérico de estoque. Toda ocorrência precisa ser classificada, auditável e refletida corretamente na disponibilidade e no resultado financeiro.
