# Mapa do Sistema WMS (visão de negócio)

## O que este sistema é

Este WMS é um sistema para manter o estoque confiável no dia a dia da operação.

Ele foi desenhado para responder perguntas de negócio como:

- O que entrou?
- O que saiu?
- Onde está cada SKU?
- O saldo está correto?
- Houve divergência no recebimento?

## O que este sistema não é (ainda)

- Não é um ERP completo.
- Não é um BI/analytics avançado.
- Não é um motor de previsão estatística.

Ele é o núcleo operacional do estoque, com regras claras e rastreabilidade.

## Como ler esta documentação

1. Comece pela visão macro (`00`, `01`, `02`).
2. Entenda os endpoints em linguagem de negócio (`03`).
3. Só depois entre nos detalhes técnicos (`04`, `05`).

## Resultado esperado para o dono do produto

Ao terminar a leitura, você deve conseguir:

- validar se a implementação respeita suas regras de negócio;
- questionar decisões técnicas com segurança;
- priorizar próximos casos de uso sem depender de jargão.
