"""Adapters PostgreSQL para migracao progressiva de persistencia."""

from .postgres_estoque_repository import PostgresEstoqueRepository
from .postgres_event_store import PostgresEventStore
from .postgres_idempotency_repository import (
    IdempotencyPayloadConflict,
    PostgresIdempotencyRepository,
)
from .postgres_inventario_repository import PostgresInventarioRepository
from .postgres_kanban_repository import PostgresKanbanRepository
from .postgres_movimentacao_repository import PostgresMovimentacaoRepository
from .postgres_orcamento_repository import PostgresOrcamentoRepository
from .postgres_politica_reposicao_repository import PostgresPoliticaReposicaoRepository
from .postgres_recebimento_repository import PostgresRecebimentoRepository
from .postgres_sinal_externo_repository import PostgresSinalExternoRepository

__all__ = [
    "PostgresEstoqueRepository",
    "PostgresMovimentacaoRepository",
    "PostgresOrcamentoRepository",
    "PostgresPoliticaReposicaoRepository",
    "PostgresRecebimentoRepository",
    "PostgresSinalExternoRepository",
    "PostgresKanbanRepository",
    "PostgresEventStore",
    "PostgresInventarioRepository",
    "PostgresIdempotencyRepository",
    "IdempotencyPayloadConflict",
]
