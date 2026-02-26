# Decisões Técnicas Traduzidas para Negócio

## FastAPI (framework da API)

Tradução de negócio: é a ferramenta que cria uma "porta organizada" para integrar o WMS com outros sistemas.

Por que foi escolhido:

- rápido de implementar;
- gera documentação automática (`/docs`);
- reduz erro de integração.

## Uvicorn (servidor da API)

Tradução de negócio: é o processo que "mantém a porta aberta" da API.

Sem ele, a API não recebe chamadas.

## Camadas do sistema

Analogia:

- Regras de negócio = política da empresa.
- Casos de uso = procedimento operacional.
- Banco/API = meios de execução.

Benefício: evita misturar regra com tecnologia.

## Validação

Antes de gravar qualquer coisa, o sistema valida regras.

Exemplo: não faz saída sem saldo.

Benefício: previne erro operacional e financeiro.

## Idempotência (conceito importante)

Analogia: evitar cobrança duplicada no cartão quando você clica duas vezes.

No WMS, significa evitar processar a mesma operação duas vezes sem querer.

No estado atual (núcleo WMS em PostgreSQL):

- endpoints de escrita do core usam `correlation_id` para evitar duplicidade acidental;
- retry com mesmo payload retorna o mesmo resultado;
- mesmo `correlation_id` com payload diferente retorna `409` (conflito).

## Transação e rollback

Analogia: ou fecha a compra completa, ou cancela tudo.

No WMS:

- saldo
- movimentação
- evento

são tratados juntos; se algo falha, volta ao estado anterior.

Benefício: consistência.

## Concorrência

Analogia: duas pessoas tentando pegar o último item ao mesmo tempo.

O sistema foi testado para evitar corrupção de saldo nesse cenário.
