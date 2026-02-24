"""Vertical slice: ProcessarGovernancaOrcamentaria."""

from dataclasses import dataclass
from datetime import date
from typing import Protocol

from wms.domain.exceptions import QuantidadeInvalida, RegraOrcamentariaInvalida


@dataclass(frozen=True)
class AporteExternoInput:
    valor: float
    origem: str
    destino: str | None
    validade_ate: date | None
    aprovado_por: str | None
    observacao: str | None = None


@dataclass(frozen=True)
class AprovacaoExcecaoInput:
    aprovado_por: str
    motivo: str
    valor_aprovado: float | None = None


@dataclass(frozen=True)
class ProcessarGovernancaOrcamentariaInput:
    operador: str
    correlation_id: str
    periodo_referencia: date
    categoria_id: str
    valor_compra_sugerida: float
    orcamento_total_periodo: float
    orcamento_categoria_periodo: float
    consumo_atual_total: float
    consumo_atual_categoria: float
    aporte_externo: AporteExternoInput | None = None
    aprovacao_excecao: AprovacaoExcecaoInput | None = None


@dataclass(frozen=True)
class ProcessarGovernancaOrcamentariaOutput:
    aprovado: bool
    alertas: list[str]
    consumo_total_projetado: float
    consumo_categoria_projetado: float
    evento_emitido: str


class OrcamentoRepository(Protocol):
    def salvar_ou_atualizar_periodo(self, payload: dict) -> str: ...
    def salvar_ou_atualizar_categoria(self, payload: dict) -> str: ...
    def salvar_aporte_externo(self, payload: dict) -> str: ...
    def salvar_compra_excecao(self, payload: dict) -> str: ...


class EventPublisher(Protocol):
    def publish(self, event_name: str, payload: dict) -> None: ...


class ProcessarGovernancaOrcamentaria:
    EVENT_NAME = "governanca_orcamentaria_processada"

    def __init__(self, orcamento_repo: OrcamentoRepository, publisher: EventPublisher) -> None:
        self._orcamento_repo = orcamento_repo
        self._publisher = publisher

    def execute(
        self, data: ProcessarGovernancaOrcamentariaInput
    ) -> ProcessarGovernancaOrcamentariaOutput:
        self._validar_entrada(data)

        # Garante o periodo antes de gravar aportes/excecoes dependentes.
        self._orcamento_repo.salvar_ou_atualizar_periodo(
            {
                "periodo_referencia": data.periodo_referencia,
                "orcamento_total_periodo": data.orcamento_total_periodo,
                "consumo_orcamento": data.consumo_atual_total,
                "created_by": data.operador,
                "correlation_id": data.correlation_id,
            }
        )

        alertas: list[str] = []
        aporte_disponivel = 0.0
        aporte_id: str | None = None

        if data.aporte_externo is not None:
            if not data.aporte_externo.aprovado_por:
                alertas.append("aporte_externo_sem_rastreabilidade")
            else:
                aporte_disponivel = data.aporte_externo.valor
            aporte_id = self._orcamento_repo.salvar_aporte_externo(
                {
                    "periodo_referencia": data.periodo_referencia,
                    "valor": data.aporte_externo.valor,
                    "origem": data.aporte_externo.origem,
                    "destino": data.aporte_externo.destino,
                    "validade_ate": data.aporte_externo.validade_ate,
                    "aprovado_por": data.aporte_externo.aprovado_por,
                    "observacao": data.aporte_externo.observacao,
                    "correlation_id": data.correlation_id,
                }
            )

        limite_total = data.orcamento_total_periodo + aporte_disponivel
        limite_categoria = data.orcamento_categoria_periodo + (
            aporte_disponivel
            if data.aporte_externo and data.aporte_externo.destino == data.categoria_id
            else 0.0
        )

        consumo_total_alerta = data.consumo_atual_total + data.valor_compra_sugerida
        consumo_categoria_alerta = data.consumo_atual_categoria + data.valor_compra_sugerida

        if consumo_categoria_alerta > limite_categoria:
            alertas.append("compra_acima_orcamento_categoria")
        if consumo_total_alerta > limite_total:
            alertas.append("compra_acima_orcamento_total")
        if (
            consumo_categoria_alerta > limite_categoria
            and consumo_total_alerta <= limite_total
        ):
            alertas.append("canibalizacao_entre_categorias")

        aprovado = True
        status_excecao = "nao_aplicavel"
        excecao_id: str | None = None
        if "compra_acima_orcamento_total" in alertas:
            if data.aprovacao_excecao is None:
                aprovado = False
                status_excecao = "pendente_aprovacao"
                alertas.append("excecao_sem_aprovacao")
            else:
                aprovado = True
                status_excecao = "aprovada"
            excecao_id = self._orcamento_repo.salvar_compra_excecao(
                {
                    "periodo_referencia": data.periodo_referencia,
                    "categoria_id": data.categoria_id,
                    "valor_solicitado": data.valor_compra_sugerida,
                    "valor_aprovado": (
                        data.aprovacao_excecao.valor_aprovado
                        if data.aprovacao_excecao is not None
                        else None
                    ),
                    "motivo": (
                        data.aprovacao_excecao.motivo
                        if data.aprovacao_excecao is not None
                        else "Acima do orcamento total"
                    ),
                    "aprovado_por": (
                        data.aprovacao_excecao.aprovado_por
                        if data.aprovacao_excecao is not None
                        else None
                    ),
                    "status": status_excecao,
                    "correlation_id": data.correlation_id,
                }
            )

        valor_compra_aplicado = data.valor_compra_sugerida
        if (
            status_excecao == "aprovada"
            and data.aprovacao_excecao is not None
            and data.aprovacao_excecao.valor_aprovado is not None
        ):
            valor_compra_aplicado = data.aprovacao_excecao.valor_aprovado

        consumo_total_projetado = data.consumo_atual_total + valor_compra_aplicado
        consumo_categoria_projetado = data.consumo_atual_categoria + valor_compra_aplicado

        self._orcamento_repo.salvar_ou_atualizar_periodo(
            {
                "periodo_referencia": data.periodo_referencia,
                "orcamento_total_periodo": data.orcamento_total_periodo,
                "consumo_orcamento": consumo_total_projetado if aprovado else data.consumo_atual_total,
                "created_by": data.operador,
                "correlation_id": data.correlation_id,
            }
        )
        self._orcamento_repo.salvar_ou_atualizar_categoria(
            {
                "periodo_referencia": data.periodo_referencia,
                "categoria_id": data.categoria_id,
                "orcamento_categoria_periodo": data.orcamento_categoria_periodo,
                "consumo_categoria": consumo_categoria_projetado if aprovado else data.consumo_atual_categoria,
                "correlation_id": data.correlation_id,
            }
        )

        self._publisher.publish(
            self.EVENT_NAME,
            {
                "periodo_referencia": str(data.periodo_referencia),
                "categoria_id": data.categoria_id,
                "valor_compra_sugerida": data.valor_compra_sugerida,
                "valor_compra_aplicado": valor_compra_aplicado,
                "aprovado": aprovado,
                "alertas": alertas,
                "aporte_externo_id": aporte_id,
                "compra_excecao_id": excecao_id,
                "consumo_total_projetado": consumo_total_projetado,
                "consumo_categoria_projetado": consumo_categoria_projetado,
                "actor_id": data.operador,
                "correlation_id": data.correlation_id,
            },
        )

        return ProcessarGovernancaOrcamentariaOutput(
            aprovado=aprovado,
            alertas=alertas,
            consumo_total_projetado=consumo_total_projetado,
            consumo_categoria_projetado=consumo_categoria_projetado,
            evento_emitido=self.EVENT_NAME,
        )

    def _validar_entrada(self, data: ProcessarGovernancaOrcamentariaInput) -> None:
        if data.valor_compra_sugerida <= 0:
            raise QuantidadeInvalida("valor_compra_sugerida deve ser maior que zero")
        if data.orcamento_total_periodo < 0 or data.orcamento_categoria_periodo < 0:
            raise QuantidadeInvalida("orcamentos nao podem ser negativos")
        if data.consumo_atual_total < 0 or data.consumo_atual_categoria < 0:
            raise QuantidadeInvalida("consumos atuais nao podem ser negativos")
        if data.consumo_atual_total > data.orcamento_total_periodo * 10:
            raise RegraOrcamentariaInvalida("consumo total informado parece invalido")
        if not data.categoria_id.strip():
            raise RegraOrcamentariaInvalida("categoria_id e obrigatorio")
        if data.aprovacao_excecao is not None:
            if not data.aprovacao_excecao.aprovado_por.strip():
                raise RegraOrcamentariaInvalida("aprovado_por e obrigatorio na excecao")
            if not data.aprovacao_excecao.motivo.strip():
                raise RegraOrcamentariaInvalida("motivo e obrigatorio na excecao")
            if data.aprovacao_excecao.valor_aprovado is not None:
                if data.aprovacao_excecao.valor_aprovado <= 0:
                    raise RegraOrcamentariaInvalida(
                        "valor_aprovado deve ser maior que zero"
                    )
                if data.aprovacao_excecao.valor_aprovado > data.valor_compra_sugerida:
                    raise RegraOrcamentariaInvalida(
                        "valor_aprovado nao pode ser maior que valor_compra_sugerida"
                    )
