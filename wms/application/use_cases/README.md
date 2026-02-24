# Application Layer - Use Cases

Esta pasta contem contratos de aplicacao orientados por casos de uso.

Regra de implementacao:

1. Entrada e saida tipadas por caso de uso.
2. Validacoes de negocio via dominio.
3. Persistencia via repositorios (portas/interfaces).
4. Emissao de eventos conforme contrato.

Nenhum caso de uso deve depender diretamente de framework web ou ORM.

Casos de uso implementados:

- `registrar_movimentacao_estoque.py`
- `registrar_ajuste_estoque.py`
- `registrar_recebimento.py`
- `registrar_inventario_ciclico.py`
