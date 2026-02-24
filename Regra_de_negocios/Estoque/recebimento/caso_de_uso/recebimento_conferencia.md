# Caso de Uso: Recebimento e Conferência

## 1. Objetivo

Garantir entrada correta de mercadorias no estoque, com conferência física e documental antes de disponibilizar saldo para venda.

## 2. Atores

- Operador de Recebimento
- Sistema de Estoque
- Gestor (em caso de divergência crítica)

## 3. Pré-condições

- Nota/documento de entrada disponível.
- Pedido de compra cadastrado (quando aplicável).
- Item cadastrado no sistema.

## 4. Fluxo Principal

1. Operador inicia recebimento da nota.
2. Sistema apresenta itens esperados para conferência.
3. Operador informa quantidade recebida por item.
4. Sistema compara esperado x recebido.
5. Se não houver divergência crítica, saldo é atualizado.
6. Sistema registra trilha de auditoria do recebimento.

## 5. Regras de Negócio

- Item só entra em saldo vendável após conferência concluída.
- Divergências devem ser classificadas (`falta`, `sobra`, `avaria`).
- Se houver avaria, aplicar regra específica de avarias.
- Recebimento deve registrar responsável e horário.

## 6. Alertas Obrigatórios

- `recebimento_com_divergencia_quantidade`
- `recebimento_com_avaria`
- `recebimento_sem_conferencia_completa`

## 7. Saídas Esperadas

- saldo atualizado por status;
- divergências registradas;
- vínculo entre recebimento e documento fiscal;
- histórico auditável.
