# Database (Planejamento)

Pasta reservada para decisao de arquitetura de dados.

Estado atual:

- schema faseado em:
  - `Database/schema_core.sql` (uso imediato);
  - `Database/schema_extended.sql` (fases futuras);
- sem migrations;
- sem scripts de carga;
- sem trigger/procedure por decisao arquitetural.

Regra de evolucao:

1. definir casos de uso executaveis;
2. validar entidades e invariantes de dominio;
3. so entao materializar schema do banco.

Cobertura atual do schema (varredura completa em `WMS`):

- CORE (aplicar agora): `item_master`, `sku`, `endereco`, `saldo_estoque`,
  `movimentacao_estoque`, `recebimento`, `recebimento_item`, `event_store`,
  `idempotency_command`.
- EXTENDED (aplicar depois): `sku_endereco`, `lote_validade`, `avaria_registro`,
  `inventario_contagem`, `politica_reposicao`, `kanban_politica`,
  `kanban_historico`, `orcamento_periodo`, `orcamento_categoria`,
  `aporte_externo`, `compra_excecao`, `sinal_externo`.

Decisoes de modelagem adotadas:

- IDs em `TEXT` para receber UUID/string gerado pela aplicacao;
- constraints basicas (PK, FK, unique, not null);
- sem logica de negocio no SQL;
- dominio/use cases continuam como fonte primaria de regra.

Ordem recomendada de aplicacao:

1. `schema_core.sql`
2. implementar adapters Postgres dos casos de uso atuais
3. validar testes de integracao
4. somente depois aplicar `schema_extended.sql` por modulo

Observacao:

A decisao final de segmentacao (db unico, schema por dominio, ou database-per-service)
sera tomada apos consolidacao dos casos de uso e limites de contexto.
