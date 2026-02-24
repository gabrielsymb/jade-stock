# Politica de Versionamento e Depreciacao da API

## Escopo

Esta politica se aplica aos endpoints `v1` expostos em `WMS`.

## Regras de versionamento

- Versao de rota obrigatoria no path: `/v1/...`.
- Mudanca compativel (backward-compatible):
  - adicionar campo opcional no request/response;
  - adicionar novo endpoint em `v1`.
- Mudanca incompativel (breaking):
  - remover/renomear campo existente;
  - alterar semantica de campo existente;
  - alterar status code esperado de sucesso/erro.

Mudanca incompativel exige nova versao de rota (`/v2/...`).

## Janela de suporte

- Versao atual: `v1`.
- Regra de suporte: manter `vN` e `vN-1` quando `v2` existir.
- Depreciacao minima: 90 dias antes de desativar versao antiga.

## Sinalizacao de depreciacao

Ao depreciar um endpoint/versao, a API deve responder com headers:

- `Deprecation: true`
- `Sunset: <RFC-1123 date>`
- `Link: <url-documentacao>; rel=\"deprecation\"`

## Contrato de erro padrao

Todos os erros de aplicacao devem seguir:

```json
{
  "code": "domain_error",
  "message": "descricao curta",
  "details": {},
  "correlation_id": "corr_123"
}
```

Codigos padrao atuais:

- `validation_error` (422)
- `domain_error` (400)
- `nota_fiscal_duplicada` (409)
- `idempotency_payload_conflict` (409)
- `internal_error` (500)

## SDK e estabilidade externa

- O SDK e o contrato oficial para consumidores externos.
- Endpoint pode evoluir internamente sem quebrar cliente, desde que o SDK mantenha compatibilidade de interface na versao major atual.
- Mudancas breaking no SDK exigem incremento de major version (SemVer).
