# WMS - Estrutura Base de Implementacao

Estrutura inicial orientada a dominio e casos de uso:

- `domain/`: entidades e regras de negocio puras;
- `application/`: orquestracao por caso de uso;
- `infrastructure/`: persistencia e adaptadores externos;
- `interfaces/`: portas de entrada (API).

Fluxo recomendado:

1. definir contrato do caso de uso;
2. implementar vertical slice;
3. persistir e emitir eventos;
4. expor por API.

Vertical slice atual:

- `RegistrarMovimentacaoEstoque` implementado em `application/use_cases/registrar_movimentacao_estoque.py`
- `RegistrarAjusteEstoque` implementado em `application/use_cases/registrar_ajuste_estoque.py`
- `RegistrarRecebimento` implementado em `application/use_cases/registrar_recebimento.py`
- `RegistrarInventarioCiclico` implementado em `application/use_cases/registrar_inventario_ciclico.py`
- `RegistrarAvariaEstoque` implementado em `application/use_cases/registrar_avaria_estoque.py`
- `RegistrarPoliticaKanban` implementado em `application/use_cases/registrar_politica_kanban.py`
- `ProcessarCurvaABCD` implementado em `application/use_cases/processar_curva_abcd.py`
- `ProcessarGiroEstoque` implementado em `application/use_cases/processar_giro_estoque.py`
- `ProcessarSazonalidadeOperacional` implementado em `application/use_cases/processar_sazonalidade_operacional.py`
- `ProcessarGovernancaOrcamentaria` implementado em `application/use_cases/processar_governanca_orcamentaria.py`
- repositorios e publisher in-memory em `infrastructure/`
- adapters Postgres core:
  - `infrastructure/postgres/postgres_estoque_repository.py`
  - `infrastructure/postgres/postgres_movimentacao_repository.py`
  - `infrastructure/postgres/postgres_recebimento_repository.py`

Execucao local recomendada (API + testes):

```bash
cd WMS
./scripts/run_api.sh
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Testes automatizados:

```bash
cd WMS
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Testes de integração SQL (opcional):

```bash
export WMS_POSTGRES_DSN='postgresql://usuario:senha@host:5432/database'
cd WMS
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

Cobertura SQL atual:

- adapters core (`estoque`, `movimentacao`, `recebimento`);
- consistencia transacional (commit/rollback atomico);
- concorrencia de transferencia sem corrupcao de saldo.

Cobertura atual de testes de caso de uso:

- `RegistrarMovimentacaoEstoque`
- `RegistrarAjusteEstoque`
- `RegistrarRecebimento`
- `RegistrarInventarioCiclico`
- `RegistrarAvariaEstoque`
- `RegistrarPoliticaKanban`
- `ProcessarCurvaABCD`
- `ProcessarGiroEstoque`
- `ProcessarSazonalidadeOperacional`
- `ProcessarGovernancaOrcamentaria`

Guardrails de limpeza:

- arquivos `in_memory_*` em `infrastructure/` sao temporarios (dev/test);
- implementacao de producao deve substituir adapters in-memory por adapters SQL/API.
