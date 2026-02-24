"""Entidade de dominio de movimentacao de estoque.

Nota arquitetural:
- O projeto esta, no momento, em modelo procedural (regras nos use cases).
- Esta entidade ainda nao e usada diretamente na execucao dos fluxos atuais.
- Mantida de forma explicita para migracao gradual para modelo OO
  (movendo invariantes do use case para a entidade quando fizer sentido).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MovimentacaoEstoque:
    movimentacao_id: str
    sku_id: str
    tipo_movimentacao: str
    quantidade: float
    endereco_origem: str | None
    endereco_destino: str | None
    motivo: str | None = None
