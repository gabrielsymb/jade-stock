# Endpoints Sem Jargão

## O que é endpoint?

Pense em endpoint como um "botão remoto" do sistema.

Quando outro sistema aperta esse botão (via internet/rede), o WMS executa uma ação de negócio.

## Endpoints v1 do sistema

## `GET /v1/health`

Serve para confirmar se a API está no ar.

## `POST /v1/movimentacoes`

Ação de negócio: registrar entrada/saída/transferência.

## `POST /v1/ajustes`

Ação de negócio: registrar correção de estoque com motivo.

## `POST /v1/avarias`

Ação de negócio: registrar perda operacional (quebra, dano, etc.) com motivo obrigatório.

## `POST /v1/recebimentos`

Ação de negócio: registrar recebimento e divergências.

## `POST /v1/inventarios/ciclico`

Ação de negócio: registrar contagem cíclica e ajustar automaticamente quando houver diferença.

Resumo simples do comportamento:

- recebe o que foi contado por SKU/endereço;
- compara com o saldo sistêmico;
- se houver diferença, cria ajuste com motivo obrigatório;
- grava snapshot da contagem para auditoria;
- emite eventos por item ajustado e um evento final de sumário.

## `POST /v1/kanban/politicas`

Ação de negócio: definir ou atualizar a política de reposição Kanban de um SKU.

Resumo simples do comportamento:

- valida se o SKU é ativo e elegível;
- valida faixas (verde >= amarela >= vermelha);
- salva política vigente;
- registra histórico de mudança de faixa;
- dispara evento de reposição quando a faixa entra em amarelo/vermelho.

## `POST /v1/curva-abcd/processar`

Ação de negócio: classificar SKUs por impacto e gerar política operacional de cobertura.

Resumo simples do comportamento:

- classifica SKU em A/B/C/D por participação acumulada no impacto econômico;
- aplica cobertura base por classe;
- adiciona colchão quando variabilidade é alta;
- limita cobertura por shelf life (perecibilidade);
- reduz para mínimo quando baixo giro é crítico;
- grava política de reposição e eventos de processamento.

## `POST /v1/giro/processar`

Ação de negócio: calcular giro e cobertura por SKU e ajustar a política operacional.

Resumo simples do comportamento:

- calcula cobertura (`estoque_atual / venda_media_diaria_prevista`);
- calcula giro (`total_vendido_periodo / estoque_medio_periodo`);
- compara com metas por classe ABC;
- dispara alertas obrigatórios (giro baixo, capital imobilizado, ruptura recorrente);
- atualiza `politica_reposicao` e emite eventos por item e sumário.

## `POST /v1/sazonalidade/processar`

Ação de negócio: aplicar sinal sazonal externo (estatística/ML) de forma determinística na política operacional do WMS.

Resumo simples do comportamento:

- recebe fator sazonal e confiança de um motor externo;
- não faz inferência estatística dentro do WMS;
- ajusta cobertura quando o sinal é confiável;
- em baixa confiança/mudança estrutural, mantém política conservadora;
- respeita limite de shelf life e registra conflito quando houver;
- grava sinal em `sinal_externo` e atualiza `politica_reposicao`.

## `POST /v1/orcamento/simular`

Ação de negócio: validar uma compra sugerida contra orçamento total e por categoria.

Resumo simples do comportamento:

- compara consumo projetado com limites do período e da categoria;
- gera alertas de extrapolação e canibalização;
- exige aprovação para compra acima do orçamento total;
- registra exceção/aprovação de forma auditável;
- registra aporte externo e sua rastreabilidade;
- atualiza consumo em `orcamento_periodo` e `orcamento_categoria`.

## Por que isso importa para negócio?

Porque o PDV ou qualquer outro sistema pode usar o WMS sem mexer no banco.

Isso reduz risco de dados quebrados e mantém padrão único de regra.

## Repetição de chamada (idempotência)

No backend PostgreSQL, os endpoints de escrita têm proteção de repetição:

- mesma rota + mesmo `correlation_id` + mesmo conteúdo: o WMS devolve a mesma resposta e não duplica efeito;
- mesma rota + mesmo `correlation_id` + conteúdo diferente: o WMS bloqueia com `409` (conflito).

Na prática: se o PDV reenviar por falha de rede, o saldo não fica duplicado.

## Erro 409: o que significa e o que fazer

Significa:

- o sistema recebeu o mesmo `correlation_id` para a mesma rota, mas com conteúdo diferente.

Como resolver:

1. se foi repetição por falha de rede, reenviar exatamente o mesmo JSON;
2. se é uma nova decisão de negócio, usar um novo `correlation_id`.
