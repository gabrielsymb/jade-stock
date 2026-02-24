# Repositories

Implementacoes concretas das portas definidas em `application/use_cases`.

Status atual:

- adapters `in_memory_*` sao somente para desenvolvimento local e testes;
- nao devem ser usados como referencia de persistencia de producao.

Exemplo de proximos adaptadores:

- `recebimento_repository_sql.py`
- `estoque_repository_sql.py`
- `movimentacao_repository_sql.py`
