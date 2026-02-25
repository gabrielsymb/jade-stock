# ORDEM DE SERVIÇO — Refactoring `app.py` (WMS)
# Agente: SWE 1.5 / Windsurf
# Versão: 1.0 | Classificação: Produção

---

## ⚠️ LEIA ANTES DE QUALQUER AÇÃO

Este prompt é uma **ordem de serviço fechada**. Seu escopo é exclusivamente a eliminação de código duplicado no arquivo `app.py`. Qualquer decisão arquitetural fora deste escopo — ausência de microserviços, OAuth, frontend, monitoramento — é **intencional e documentada no roadmap (Fases B–E)**. Você não deve questionar, sugerir melhorias, nem alterar nada além do que está explicitamente descrito aqui.

Se encontrar algo que pareça "melhorável" fora do escopo: registre como `# TODO` e **prossiga sem alterar**.

---

## PROTOCOLO ANTI-ALUCINAÇÃO

Antes de escrever qualquer linha de código, confirme que você leu e entendeu os seguintes fatos do sistema. **Não invente informações sobre a arquitetura.**

| Fato do Sistema | Status |
|---|---|
| Migrations com Alembic | ✅ Existente — documentado na Sessão 9.1 |
| Release gate (`release_gate.sh`) | ✅ Existente — documentado na Sessão 9.2 |
| Módulo Contábil | 🔜 Fase D do roadmap — ausência é intencional |
| OAuth / IAM | 🔜 Fase E do roadmap — ausência é intencional |
| Observabilidade / Monitoramento | 🔜 Fase B do roadmap — ausência é intencional |
| Frontend | 🔜 Fora do escopo do MVP (Fase A) |
| Arquitetura: Monolito Modular | ✅ Decisão deliberada para equipe de 1–2 pessoas |

**Se você "ver" algo ausente na tabela acima como um problema: você está errado. Consulte o roadmap antes de comentar.**

---

## PROTOCOLO DE PARADA OBRIGATÓRIA

> Esta seção tem **prioridade máxima** sobre qualquer outro instinto do agente.

**SE qualquer teste falhar durante a refatoração:**

1. **PARE imediatamente.** Não tente corrigir automaticamente.
2. **NÃO faça nenhuma alteração adicional** no arquivo.
3. **Reporte EXATAMENTE** (copie e cole, sem resumir):
   - Nome completo do teste que falhou
   - Nome da rota que foi alterada imediatamente antes
   - Mensagem de erro completa (`stderr`)
   - O bloco de código que foi substituído (antes e depois)
4. **Aguarde instrução humana** antes de continuar.

> **Por quê:** Agentes de codificação têm tendência à "hiper-correção" — tentar resolver um erro criando outro. Este protocolo funciona como um *circuit breaker* que interrompe esse ciclo antes que o código seja poluído com soluções improvisadas não rastreáveis.

---

## PRÉ-REQUISITO: SNAPSHOT DE SEGURANÇA

**Antes de qualquer alteração**, confirme que os seguintes comandos foram executados no terminal:

```bash
git add app.py
git commit -m "chore: snapshot pré-refactor — baseline para rollback"
git tag pre-refactor-baseline
```

> Se o rollback for necessário em qualquer momento: `git checkout pre-refactor-baseline -- app.py`

---

## CONTEXTO TÉCNICO

**Sistema:** WMS (Warehouse Management System)
**Arquitetura:** Monolito Modular sobre PostgreSQL
**Problema:** O arquivo `app.py` (~1240 linhas) repete o seguinte bloco em **10 endpoints**:

```python
if API_BACKEND == "postgres":
    conn = get_connection_postgres()
    try:
        estoque_repo = PostgresEstoqueRepository(conn)
        mov_repo     = PostgresMovimentacaoRepository(conn)
        publisher    = PostgresEventStore(conn, tenant_id=TENANT_ID)
        use_case     = RegistrarMovimentacaoEstoque(mov_repo, estoque_repo, publisher)
        with postgres_transaction(conn):
            out = _execute_postgres_with_idempotency(
                connection=conn,
                operation_name="registrar_movimentacao",
                correlation_id=data.correlation_id,
                request_payload=body.model_dump(mode="json"),
                execute=lambda: asdict(use_case.execute(data)),
            )
        return out
    finally:
        conn.close()
```

**As únicas coisas que variam** entre os 10 endpoints:

| Variável | Exemplo |
|---|---|
| `operation_name` | `"registrar_movimentacao"` |
| `use_case_class` | `RegistrarMovimentacaoEstoque` |
| `correlation_id` | `body.correlation_id` |
| `request_payload` | `body.model_dump(mode="json")` |
| Repositórios específicos | `{"mov_repo": PostgresMovimentacaoRepository}` |

Tudo o mais é **idêntico** em todos os endpoints.

---

## SOLUÇÃO: FUNÇÃO MESTRA UNIVERSAL

### Padrões de referência (não invente outros)

Esta solução aplica **exclusivamente** dois padrões da literatura:

- **Factory Method** — GoF, Gamma et al., *Design Patterns: Elements of Reusable Object-Oriented Software*, Addison-Wesley, 1994. Responsável por criar instâncias dos repositórios específicos sem expor a lógica de construção às rotas.
- **Dependency Injection** — Fowler, M., *Inversion of Control Containers and the Dependency Injection pattern*, martinfowler.com, 2004. Os repositórios são construídos externamente e injetados no `use_case`, eliminando acoplamento direto dentro das rotas.

> **Instrução explícita:** NÃO introduza frameworks de DI externos (`dependency-injector`, `injector`, `punq`, etc.). A injeção será **manual e explícita**, adequada ao porte da equipe (1–2 pessoas), conforme decisão arquitetural documentada.

---

## IMPLEMENTAÇÃO — PASSO A PASSO

### PASSO 1 — Adicionar imports

Localize o bloco de imports existente. Adicione **apenas o que estiver faltando**. Não remova imports existentes.

```python
from typing import Callable, Dict, Type
```

---

### PASSO 2 — Criar a Função Mestra Universal

Insira esta função **após os helpers existentes** (`_raise_http`, `_execute_postgres_with_idempotency`, etc.) e **antes da definição das rotas**. Copie exatamente:

```python
def execute_use_case(
    operation_name: str,
    use_case_class: Type,
    correlation_id: str,
    request_payload: dict,
    repository_factories: Dict[str, Callable],
    execute_fn: Callable,
) -> dict:
    """
    Função mestra universal para execução de use cases com PostgreSQL.

    Padrões aplicados:
    - Factory Method (GoF, Gamma et al., 1994): instanciação dos repositórios via factories.
    - Dependency Injection (Fowler, 2004): repositórios injetados externamente no use case.

    Args:
        operation_name:       Nome da operação para idempotência e logging.
        use_case_class:       Classe do use case a ser instanciado.
        correlation_id:       ID de correlação da requisição (garante idempotência).
        request_payload:      Payload serializado da requisição (dict).
        repository_factories: Dict mapeando nome_do_argumento -> classe_do_repositório.
                              Ex.: {'mov_repo': PostgresMovimentacaoRepository}
        execute_fn:           Função que recebe o use_case instanciado e retorna
                              um callable sem argumentos para o executor de idempotência.
                              Padrão: lambda uc: lambda: asdict(uc.execute(data))

    Returns:
        dict com o resultado serializado da operação.

    Raises:
        Propaga qualquer exceção levantada pelo use case ou pela infraestrutura.
        O tratamento HTTP (_raise_http) permanece nas rotas, não aqui.
    """
    conn = get_connection_postgres()
    try:
        # Repositórios universais — presentes em TODOS os use cases
        estoque_repo = PostgresEstoqueRepository(conn)
        publisher    = PostgresEventStore(conn, tenant_id=TENANT_ID)

        # Repositórios específicos via Factory Method
        specific_repos = {
            name: factory(conn)
            for name, factory in repository_factories.items()
        }

        # Dependency Injection — use case recebe os repositórios de fora
        use_case = use_case_class(
            **specific_repos,
            estoque_repo=estoque_repo,
            publisher=publisher,
        )

        # Execução com transação atômica e idempotência — comportamento preservado
        with postgres_transaction(conn):
            return _execute_postgres_with_idempotency(
                connection=conn,
                operation_name=operation_name,
                correlation_id=correlation_id,
                request_payload=request_payload,
                execute=execute_fn(use_case),
            )
    finally:
        conn.close()
```

> ⚠️ **NÃO altere** `_execute_postgres_with_idempotency`, `postgres_transaction`, nem qualquer helper existente. Chame-os exatamente como estão hoje.

---

### PASSO 3 — Refatorar as 10 Rotas

**Regra para cada rota:**
- Substitua **somente** o bloco `if API_BACKEND == "postgres": ... finally: conn.close()`
- O bloco `else` (in-memory) deve ser **preservado byte a byte, sem nenhuma alteração**
- **Após cada rota**, execute a validação obrigatória (Seção de Validação abaixo) antes de avançar

---

#### ROTA 3.1 — `registrar_movimentacao` (linhas ~762–777)

```python
# REMOVER este bloco:
if API_BACKEND == "postgres":
    conn = get_connection_postgres()
    try:
        estoque_repo = PostgresEstoqueRepository(conn)
        mov_repo = PostgresMovimentacaoRepository(conn)
        publisher = PostgresEventStore(conn, tenant_id=TENANT_ID)
        use_case = RegistrarMovimentacaoEstoque(mov_repo, estoque_repo, publisher)
        with postgres_transaction(conn):
            out = _execute_postgres_with_idempotency(...)
        return out
    finally:
        conn.close()

# INSERIR este bloco:
if API_BACKEND == "postgres":
    return execute_use_case(
        operation_name="registrar_movimentacao",
        use_case_class=RegistrarMovimentacaoEstoque,
        correlation_id=body.correlation_id,
        request_payload=body.model_dump(mode="json"),
        repository_factories={"mov_repo": PostgresMovimentacaoRepository},
        execute_fn=lambda uc: lambda: asdict(uc.execute(data)),
    )
```

---

#### ROTA 3.2 — `registrar_ajuste` (linhas ~804–819)

```python
if API_BACKEND == "postgres":
    return execute_use_case(
        operation_name="registrar_ajuste",
        use_case_class=RegistrarAjusteEstoque,
        correlation_id=body.correlation_id,
        request_payload=body.model_dump(mode="json"),
        repository_factories={"mov_repo": PostgresMovimentacaoRepository},
        execute_fn=lambda uc: lambda: asdict(uc.execute(data)),
    )
```

---

#### ROTA 3.3 — `registrar_avaria` (linhas ~846–861)

```python
if API_BACKEND == "postgres":
    return execute_use_case(
        operation_name="registrar_avaria",
        use_case_class=RegistrarAvariaEstoque,
        correlation_id=body.correlation_id,
        request_payload=body.model_dump(mode="json"),
        repository_factories={"mov_repo": PostgresMovimentacaoRepository},
        execute_fn=lambda uc: lambda: asdict(uc.execute(data)),
    )
```

---

#### ROTA 3.4 — `registrar_recebimento` (linhas ~895–910)

```python
if API_BACKEND == "postgres":
    return execute_use_case(
        operation_name="registrar_recebimento",
        use_case_class=RegistrarRecebimento,
        correlation_id=body.correlation_id,
        request_payload=body.model_dump(mode="json"),
        repository_factories={"recebimento_repo": PostgresRecebimentoRepository},
        execute_fn=lambda uc: lambda: asdict(uc.execute(data)),
    )
```

---

#### ROTA 3.5 — `registrar_inventario_ciclico` (linhas ~944–965)

> ℹ️ Este é o único endpoint com **dois repositórios específicos**. A função mestra suporta isso nativamente via dict — não é necessário nenhum tratamento especial.

```python
if API_BACKEND == "postgres":
    return execute_use_case(
        operation_name="registrar_inventario_ciclico",
        use_case_class=RegistrarInventarioCiclico,
        correlation_id=body.correlation_id,
        request_payload=body.model_dump(mode="json"),
        repository_factories={
            "mov_repo":        PostgresMovimentacaoRepository,
            "inventario_repo": PostgresInventarioRepository,
        },
        execute_fn=lambda uc: lambda: asdict(uc.execute(data)),
    )
```

---

#### ROTA 3.6 — `registrar_politica_kanban` (linhas ~993–1008)

```python
if API_BACKEND == "postgres":
    return execute_use_case(
        operation_name="registrar_politica_kanban",
        use_case_class=RegistrarPoliticaKanban,
        correlation_id=body.correlation_id,
        request_payload=body.model_dump(mode="json"),
        repository_factories={"kanban_repo": PostgresKanbanRepository},
        execute_fn=lambda uc: lambda: asdict(uc.execute(data)),
    )
```

---

#### ROTA 3.7 — `processar_curva_abcd` (linhas ~1040–1055)

```python
if API_BACKEND == "postgres":
    return execute_use_case(
        operation_name="processar_curva_abcd",
        use_case_class=ProcessarCurvaABCD,
        correlation_id=body.correlation_id,
        request_payload=body.model_dump(mode="json"),
        repository_factories={"politica_repo": PostgresPoliticaReposicaoRepository},
        execute_fn=lambda uc: lambda: asdict(uc.execute(data)),
    )
```

---

#### ROTA 3.8 — `processar_giro_estoque` (linhas ~1087–1102)

```python
if API_BACKEND == "postgres":
    return execute_use_case(
        operation_name="processar_giro_estoque",
        use_case_class=ProcessarGiroEstoque,
        correlation_id=body.correlation_id,
        request_payload=body.model_dump(mode="json"),
        repository_factories={"politica_repo": PostgresPoliticaReposicaoRepository},
        execute_fn=lambda uc: lambda: asdict(uc.execute(data)),
    )
```

---

#### ROTA 3.9 — `processar_sazonalidade_operacional` (linhas ~1134–1149)

```python
if API_BACKEND == "postgres":
    return execute_use_case(
        operation_name="processar_sazonalidade_operacional",
        use_case_class=ProcessarSazonalidadeOperacional,
        correlation_id=body.correlation_id,
        request_payload=body.model_dump(mode="json"),
        repository_factories={"sinal_repo": PostgresSinalExternoRepository},
        execute_fn=lambda uc: lambda: asdict(uc.execute(data)),
    )
```

---

#### ROTA 3.10 — `processar_governanca_orcamentaria` (linhas ~1214–1229)

```python
if API_BACKEND == "postgres":
    return execute_use_case(
        operation_name="processar_governanca_orcamentaria",
        use_case_class=ProcessarGovernancaOrcamentaria,
        correlation_id=body.correlation_id,
        request_payload=body.model_dump(mode="json"),
        repository_factories={"orcamento_repo": PostgresOrcamentoRepository},
        execute_fn=lambda uc: lambda: asdict(uc.execute(data)),
    )
```

---

## VALIDAÇÃO OBRIGATÓRIA APÓS CADA ROTA

Execute este comando após **cada rota individualmente**. Não avance para a próxima sem confirmação de sucesso:

```bash
cd WMS && python3 -m unittest discover -s tests -p 'test_*.py' -v 2>&1 | tee refactor_test_log.txt | grep -E "(FAIL|ERROR|OK)"
```

> O `tee` salva o log completo em `refactor_test_log.txt`. O `grep` mostra apenas o sinal relevante. Se um teste falhar, **acione o Protocolo de Parada** (seção no topo deste documento).

---

## VALIDAÇÃO FINAL — SMOKE TEST DE CONTRATO

Após todas as 10 rotas, crie e execute este script para verificar se a fábrica de repositórios está injetando os tipos corretos em cada use case. Este teste **não requer banco de dados**:

```python
# smoke_test_factory.py — executar uma vez após o refactor completo
"""
Valida que execute_use_case injeta os repositórios corretos em cada use case.
Detecta erros de contrato que testes unitários não capturam.
Rodar: python3 smoke_test_factory.py
"""
import inspect

# Ajuste os imports conforme a estrutura real do projeto
from domain.use_cases import (
    RegistrarMovimentacaoEstoque, RegistrarAjusteEstoque, RegistrarAvariaEstoque,
    RegistrarRecebimento, RegistrarInventarioCiclico, RegistrarPoliticaKanban,
    ProcessarCurvaABCD, ProcessarGiroEstoque,
    ProcessarSazonalidadeOperacional, ProcessarGovernancaOrcamentaria,
)

def verificar_contrato(use_case_class, repository_factories):
    """Compara parâmetros esperados pelo __init__ com o que a fábrica entrega."""
    params_esperados = set(inspect.signature(use_case_class.__init__).parameters.keys())
    params_esperados.discard("self")
    params_entregues = set(repository_factories.keys()) | {"estoque_repo", "publisher"}

    faltando = params_esperados - params_entregues
    sobrando = params_entregues - params_esperados

    if faltando or sobrando:
        print(f"❌  {use_case_class.__name__}")
        if faltando: print(f"    Faltando : {faltando}")
        if sobrando: print(f"    Sobrando : {sobrando}")
        return False
    else:
        print(f"✅  {use_case_class.__name__} — contrato OK")
        return True

casos = [
    (RegistrarMovimentacaoEstoque,     {"mov_repo": None}),
    (RegistrarAjusteEstoque,           {"mov_repo": None}),
    (RegistrarAvariaEstoque,           {"mov_repo": None}),
    (RegistrarRecebimento,             {"recebimento_repo": None}),
    (RegistrarInventarioCiclico,       {"mov_repo": None, "inventario_repo": None}),
    (RegistrarPoliticaKanban,          {"kanban_repo": None}),
    (ProcessarCurvaABCD,               {"politica_repo": None}),
    (ProcessarGiroEstoque,             {"politica_repo": None}),
    (ProcessarSazonalidadeOperacional, {"sinal_repo": None}),
    (ProcessarGovernancaOrcamentaria,  {"orcamento_repo": None}),
]

print("=== Smoke Test — Contrato de Fábrica ===\n")
resultados = [verificar_contrato(uc, f) for uc, f in casos]
print(f"\n{'✅ Todos os contratos OK' if all(resultados) else '❌ FALHAS ENCONTRADAS — revisar antes do commit'}")
```

---

## REGRAS ABSOLUTAS — RESUMO FINAL

| # | O que NÃO fazer |
|---|---|
| 1 | Alterar qualquer bloco `else` (in-memory) |
| 2 | Alterar assinaturas de rotas (`@app.route`, decoradores, parâmetros) |
| 3 | Alterar blocos `try/except` e chamadas a `_raise_http` nas rotas |
| 4 | Introduzir dependências externas não listadas neste documento |
| 5 | Questionar ausência de microserviços, OAuth, frontend ou monitoramento |
| 6 | Tentar "melhorar" padrões fora do escopo — use `# TODO` e prossiga |
| 7 | Tentar corrigir automaticamente um teste que falhou — acione o Protocolo de Parada |
| 8 | Alterar `_execute_postgres_with_idempotency` ou `postgres_transaction` |

---

## CHECKLIST FINAL DO AGENTE

Ao concluir todas as 10 rotas, confirme cada item:

- [ ] Nenhum bloco `if API_BACKEND == "postgres": conn = get_connection_postgres()` existe fora de `execute_use_case`
- [ ] Todos os blocos `else` (in-memory) estão intactos
- [ ] Suite de testes passa 100% (`grep -c "OK" refactor_test_log.txt`)
- [ ] Script `smoke_test_factory.py` exibe ✅ para todos os 10 use cases
- [ ] Arquivo `app.py` tem redução visível de linhas (~80% de código repetido eliminado)
- [ ] Função `execute_use_case` está no lugar correto (após helpers, antes das rotas)
- [ ] Função `execute_use_case` possui docstring completa conforme especificado
- [ ] Nenhuma dependência externa foi adicionada ao projeto

---

*Fim da Ordem de Serviço. Qualquer dúvida sobre escopo: consulte o roadmap faseado (Fases A–E) antes de agir.*