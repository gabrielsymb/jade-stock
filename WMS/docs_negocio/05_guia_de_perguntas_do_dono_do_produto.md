# Guia de Perguntas do Dono do Produto

Use este checklist para validar a qualidade do sistema sem depender de jargão técnico.

> Atualizado em 26/02/2026.

## Regras de negócio

- Este fluxo respeita a regra original que defini?
- Existe alguma regra crítica faltando?
- O sistema está forçando motivo quando necessário?

## Operação

- O operador consegue executar o fluxo sem ambiguidade?
- Em caso de erro, a mensagem é compreensível?
- Existe histórico para auditar depois?

## Integração (API)

- O endpoint representa uma ação real de negócio?
- Existe risco de duplicidade dessa operação?
- Qual evidência de sucesso/falha o endpoint devolve?

## Dados

- O saldo final fica coerente depois do fluxo?
- Se ocorrer falha no meio, o sistema desfaz tudo?
- O que é salvo em memória e o que é salvo no banco?

## Evolução

- Esse novo requisito entra como novo caso de uso ou muda um já existente?
- Essa mudança é compatível com `v1` ou exigiria `v2`?
- Estamos adicionando valor real ou apenas complexidade?

## Integração via SDK (para evitar retrabalho)

- O SDK já cobre o endpoint que eu preciso ou estamos obrigando uso manual da API?
- O time consegue executar um fluxo em menos de 10 linhas de código?
- Existe exemplo pronto no `sdk/README.md` para esse fluxo?
- Em erro de integração, a mensagem está clara para quem não é especialista?
