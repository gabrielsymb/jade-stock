"""Entidade de dominio Saldo de Estoque por SKU e endereco.

Nota arquitetural:
- O projeto esta, no momento, em modelo procedural (regras nos use cases).
- Esta entidade ainda nao e usada diretamente na execucao dos fluxos atuais.
- Mantida de forma explicita para migracao gradual para modelo OO
  (movendo invariantes do use case para a entidade quando fizer sentido).
"""

from dataclasses import dataclass


@dataclass
class SaldoEstoque:
    sku_id: str
    endereco_codigo: str
    saldo_disponivel: float = 0.0
    saldo_avariado: float = 0.0
    saldo_bloqueado: float = 0.0
