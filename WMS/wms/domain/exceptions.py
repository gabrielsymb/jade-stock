"""Excecoes de dominio para casos de uso WMS."""


class DomainError(Exception):
    """Erro base de dominio."""


class SKUInativoOuInexistente(DomainError):
    pass


class EnderecoInvalido(DomainError):
    pass


class EstoqueInsuficiente(DomainError):
    pass


class QuantidadeInvalida(DomainError):
    pass


class TipoMovimentacaoInvalido(DomainError):
    pass


class MotivoObrigatorio(DomainError):
    pass


class NotaFiscalDuplicada(DomainError):
    pass


class DivergenciaNaoClassificada(DomainError):
    pass


class RegraKanbanInvalida(DomainError):
    pass


class RegraGiroInvalida(DomainError):
    pass


class RegraSazonalidadeInvalida(DomainError):
    pass


class RegraOrcamentariaInvalida(DomainError):
    pass
