"""Entidade de dominio de recebimento.

Nota arquitetural:
- O projeto esta, no momento, em modelo procedural (regras nos use cases).
- Esta entidade ainda nao e usada diretamente na execucao dos fluxos atuais.
- Mantida de forma explicita para migracao gradual para modelo OO
  (movendo invariantes do use case para a entidade quando fizer sentido).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Recebimento:
    recebimento_id: str
    nota_fiscal_numero: str
    fornecedor_id: str
    status_conferencia: str
    possui_avaria: bool = False
