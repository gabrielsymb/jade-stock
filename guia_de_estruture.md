# Guia de Estrutura do Repositorio - Jade-stock

**Data:** 2026-02-26  
**Status:** ativo

## Objetivo

Definir onde cada tipo de artefato deve ficar e evitar poluicao de repositorio com pastas de modulos ainda nao implementados.

## Estrutura atual (alto nivel)

```text
Jade-stock/
|- README.md
|- CONTRIBUTING.md
|- DOCS_BOAS_PRACTICES.md
|- JADE-STOCK-BIBLIA-DO-SISTEMA.md
|- jade-stock-adendos.docx.md
|- guia_de_estruture.md
|- Database/
|- WMS/
|- sdk/
|- archive/
|- Estudos/
|- LaboratorioDepositoBebidas/
```

## Regra principal de modulos futuros

Modulos planejados (`Contabil`, `PDV`, `IA/Analytics`) **nao** devem ter pasta no root enquanto nao houver no minimo:

1. codigo inicial versionavel;
2. testes basicos;
3. README do modulo com comando executavel.

Sem esses tres itens, o modulo deve existir apenas na documentacao.

## Onde colocar cada coisa

- Codigo de dominio/aplicacao/infra do modulo ativo: `WMS/wms/`
- Testes automatizados do modulo ativo: `WMS/tests/`
- Scripts operacionais: `WMS/scripts/`
- Schemas e migracoes SQL compartilhadas: `Database/`
- SDK para integracoes: `sdk/`
- Historico/legado descontinuado: `archive/`

## Politica de limpeza antes de commit

- remover pastas vazias;
- remover placeholders sem uso;
- separar staging por contexto (`git add -p`);
- garantir que docs descrevem o estado real do filesystem.

## Fluxo de evolucao para novo modulo

Quando iniciar um novo modulo, crie a estrutura em um unico PR com:

- `modulo/README.md` com setup e execucao;
- `modulo/src` ou equivalente;
- `modulo/tests` com smoke test;
- ajuste do `README.md` raiz e da Biblia.
