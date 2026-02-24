# Módulos e Responsabilidades (sem jargão)

Este arquivo agora também mostra **onde cada coisa está no projeto**.

## 1) Cadastro

Responsável por identificar corretamente o produto:

- SKU
- status ativo/inativo
- unidade
- variações

Sem cadastro correto, o resto do sistema perde qualidade.

Arquivos principais:

- Regra de negócio: `WMS/Regra_de_negocios/Estoque/sku/regra_sku/sku.md`
- Caso de uso de cadastro: `WMS/Regra_de_negocios/Estoque/sku/caso_de_uso/cadastro_sku.md`
- Entidade de domínio: `WMS/wms/domain/sku.py`
- Banco (tabela): `Database/schema_core.sql` -> `sku`

## 2) Endereçamento

Responsável por localizar fisicamente o item.

Pergunta que ele responde: "onde está esse SKU?"

Arquivos principais:

- Regra de negócio: `WMS/Regra_de_negocios/Estoque/address/address_regra/address.md`
- Caso de uso: `WMS/Regra_de_negocios/Estoque/enderecamento/caso_de_uso/enderecamento_basico.md`
- Entidade de domínio: `WMS/wms/domain/endereco.py`
- Banco (tabela): `Database/schema_core.sql` -> `endereco`

## 3) Movimentação

Responsável por registrar mudanças de saldo:

- entrada
- saída
- transferência
- avaria

Arquivos principais:

- Caso de uso executável: `WMS/wms/application/use_cases/registrar_movimentacao_estoque.py`
- Endpoint API: `WMS/wms/interfaces/api/app.py` -> `POST /v1/movimentacoes`
- Persistência: `WMS/wms/infrastructure/postgres/postgres_movimentacao_repository.py`
- Persistência de saldo: `WMS/wms/infrastructure/postgres/postgres_estoque_repository.py`
- Testes: `WMS/tests/test_registrar_movimentacao_estoque.py`
- Teste API: `WMS/tests/test_api_inmemory.py`
- Banco (tabelas): `Database/schema_core.sql` -> `movimentacao_estoque`, `saldo_estoque`

## 4) Ajuste

Responsável por correções operacionais (ex: quebra, erro de contagem).

Regra central: ajuste precisa de motivo.

Arquivos principais:

- Caso de uso executável: `WMS/wms/application/use_cases/registrar_ajuste_estoque.py`
- Documento de caso executável: `WMS/Regra_de_negocios/Estoque/integracao/caso_de_uso_executavel_registrar_ajuste_estoque.md`
- Endpoint API: `WMS/wms/interfaces/api/app.py` -> `POST /v1/ajustes`
- Testes: `WMS/tests/test_registrar_ajuste_estoque.py`
- Banco (tabela): `Database/schema_core.sql` -> `movimentacao_estoque` (tipo ajuste) e `saldo_estoque`

## 5) Recebimento

Responsável por entrada de mercadoria e conferência:

- quantidade esperada
- quantidade conferida
- divergência (falta, sobra, avaria)

Arquivos principais:

- Caso de uso executável: `WMS/wms/application/use_cases/registrar_recebimento.py`
- Documento de caso executável: `WMS/Regra_de_negocios/Estoque/integracao/caso_de_uso_executavel_registrar_recebimento.md`
- Endpoint API: `WMS/wms/interfaces/api/app.py` -> `POST /v1/recebimentos`
- Persistência: `WMS/wms/infrastructure/postgres/postgres_recebimento_repository.py`
- Testes: `WMS/tests/test_registrar_recebimento.py`
- Banco (tabelas): `Database/schema_core.sql` -> `recebimento`, `recebimento_item`

## 6) Eventos e histórico

Responsável por rastreabilidade.

Toda operação importante gera registro para auditoria e integração futura.

Arquivos principais:

- Contrato de eventos: `WMS/Regra_de_negocios/Estoque/integracao/contrato_eventos.md`
- Publicador em memória: `WMS/wms/infrastructure/events/in_memory_event_publisher.py`
- Event store Postgres: `WMS/wms/infrastructure/postgres/postgres_event_store.py`
- Banco (tabela): `Database/schema_core.sql` -> `event_store`

## 7) API

Responsável por permitir que outros sistemas (como PDV) usem essas funções sem acessar banco direto.

Arquivos principais:

- API principal: `WMS/wms/interfaces/api/app.py`
- Guia da API: `WMS/wms/interfaces/api/README.md`
- Runner da API: `WMS/scripts/run_api.sh`

## 8) Banco de dados

Responsável por persistir os fatos do negócio:

- saldos
- movimentações
- recebimentos
- eventos

Arquivos principais:

- Core (fase atual): `Database/schema_core.sql`
- Extended (futuro): `Database/schema_extended.sql`
- Guia do banco: `Database/README.md`
- Configuração de conexão: `WMS/wms/infrastructure/database/database_config.py`

Resumo importante:

- API em `inmemory` (padrão): não persiste no banco.
- API em `postgres`: grava no banco usando o schema core.
