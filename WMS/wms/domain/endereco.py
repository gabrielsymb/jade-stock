"""Entidade de dominio Endereco.

Nota arquitetural:
- O projeto esta, no momento, em modelo procedural (regras nos use cases).
- Esta entidade ainda nao e usada diretamente na execucao dos fluxos atuais.
- Mantida de forma explicita para migracao gradual para modelo OO
  (movendo invariantes do use case para a entidade quando fizer sentido).
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Endereco:
    endereco_codigo: str
    tipo_endereco: str
    ativo: bool = True
