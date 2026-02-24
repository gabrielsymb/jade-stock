# Caso de Uso: Endereçamento Básico

## 1. Objetivo

Organizar localização física de itens com baixa complexidade operacional, permitindo rastreabilidade mínima e separação mais eficiente.

## 2. Modelo Inicial (MVP)

Endereçamento mínimo útil:

- `zona` (ex.: `LOJA`, `DEP`)
- `prateleira` (ex.: `P01`, `P02`)
- `posicao` (ex.: `01`, `02`)

Formato recomendado:

- `zona-prateleira-posicao`
- Exemplo: `DEP-P03-02`

Evolução opcional (quando a operação crescer):

- `rua`, `modulo`, `nivel`, `vao`
- Exemplo expandido: `DEP-R01-M02-N01-V03`

## 3. Fluxo Principal

1. Item é recebido e conferido.
2. Sistema sugere endereço padrão conforme regra do item.
3. Operador confirma movimentação para o endereço.
4. Sistema atualiza saldo por localização.

## 4. Regras de Negócio

- Todo item em estoque deve ter localização ativa.
- Movimentação entre endereços deve gerar evento auditável.
- Inventário cíclico deve considerar item + localização.
- Avaria não pode permanecer em endereço vendável.
- Endereço deve ser específico o suficiente para qualquer operador localizar o item sem interpretação subjetiva.

## 5. Alertas Obrigatórios

- `item_sem_endereco`
- `movimentacao_sem_confirmacao`
- `saldo_negativo_no_endereco`

## 6. Saídas Esperadas

- saldo por item e endereço;
- histórico de transferências internas;
- base para picking e inventário cíclico.
