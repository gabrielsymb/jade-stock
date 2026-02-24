"""Testes do vertical slice ProcessarGovernancaOrcamentaria."""

from datetime import date
import unittest

from wms.application.use_cases.processar_governanca_orcamentaria import (
    AporteExternoInput,
    AprovacaoExcecaoInput,
    ProcessarGovernancaOrcamentaria,
    ProcessarGovernancaOrcamentariaInput,
)
from wms.domain.exceptions import RegraOrcamentariaInvalida
from wms.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from wms.infrastructure.repositories.in_memory_orcamento_repository import (
    InMemoryOrcamentoRepository,
)


class ProcessarGovernancaOrcamentariaTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = InMemoryOrcamentoRepository()
        self.publisher = InMemoryEventPublisher(tenant_id="loja_teste")
        self.use_case = ProcessarGovernancaOrcamentaria(self.repo, self.publisher)

    def test_compra_dentro_orcamento(self) -> None:
        out = self.use_case.execute(
            ProcessarGovernancaOrcamentariaInput(
                operador="op_01",
                correlation_id="corr_orc_001",
                periodo_referencia=date(2026, 2, 1),
                categoria_id="cat_a",
                valor_compra_sugerida=100,
                orcamento_total_periodo=1000,
                orcamento_categoria_periodo=300,
                consumo_atual_total=400,
                consumo_atual_categoria=100,
            )
        )
        self.assertTrue(out.aprovado)
        self.assertEqual([], out.alertas)
        self.assertEqual(500, out.consumo_total_projetado)
        self.assertEqual(200, out.consumo_categoria_projetado)
        self.assertEqual(1, len(self.publisher.events))

    def test_compra_acima_total_sem_aprovacao(self) -> None:
        out = self.use_case.execute(
            ProcessarGovernancaOrcamentariaInput(
                operador="op_01",
                correlation_id="corr_orc_002",
                periodo_referencia=date(2026, 2, 1),
                categoria_id="cat_a",
                valor_compra_sugerida=700,
                orcamento_total_periodo=1000,
                orcamento_categoria_periodo=600,
                consumo_atual_total=500,
                consumo_atual_categoria=100,
            )
        )
        self.assertFalse(out.aprovado)
        self.assertIn("compra_acima_orcamento_total", out.alertas)
        self.assertIn("excecao_sem_aprovacao", out.alertas)
        self.assertEqual(1, len(self.repo.excecoes))

    def test_compra_acima_total_com_aprovacao(self) -> None:
        out = self.use_case.execute(
            ProcessarGovernancaOrcamentariaInput(
                operador="op_01",
                correlation_id="corr_orc_003",
                periodo_referencia=date(2026, 2, 1),
                categoria_id="cat_a",
                valor_compra_sugerida=700,
                orcamento_total_periodo=1000,
                orcamento_categoria_periodo=600,
                consumo_atual_total=500,
                consumo_atual_categoria=100,
                aprovacao_excecao=AprovacaoExcecaoInput(
                    aprovado_por="gestor_01",
                    motivo="Produto critico",
                    valor_aprovado=700,
                ),
            )
        )
        self.assertTrue(out.aprovado)
        self.assertIn("compra_acima_orcamento_total", out.alertas)
        self.assertEqual("aprovada", self.repo.excecoes[0]["status"])

    def test_compra_acima_total_com_aprovacao_parcial_aplica_valor_aprovado(self) -> None:
        out = self.use_case.execute(
            ProcessarGovernancaOrcamentariaInput(
                operador="op_01",
                correlation_id="corr_orc_003b",
                periodo_referencia=date(2026, 2, 1),
                categoria_id="cat_a",
                valor_compra_sugerida=700,
                orcamento_total_periodo=1000,
                orcamento_categoria_periodo=600,
                consumo_atual_total=500,
                consumo_atual_categoria=100,
                aprovacao_excecao=AprovacaoExcecaoInput(
                    aprovado_por="gestor_01",
                    motivo="Aprovar parcialmente",
                    valor_aprovado=400,
                ),
            )
        )
        self.assertTrue(out.aprovado)
        self.assertEqual(900, out.consumo_total_projetado)
        self.assertEqual(500, out.consumo_categoria_projetado)
        periodo = self.repo.periodos[date(2026, 2, 1)]
        categoria = self.repo.categorias[(date(2026, 2, 1), "cat_a")]
        self.assertEqual(900, periodo["consumo_orcamento"])
        self.assertEqual(500, categoria["consumo_categoria"])

    def test_aporte_sem_rastreabilidade(self) -> None:
        out = self.use_case.execute(
            ProcessarGovernancaOrcamentariaInput(
                operador="op_01",
                correlation_id="corr_orc_004",
                periodo_referencia=date(2026, 2, 1),
                categoria_id="cat_a",
                valor_compra_sugerida=100,
                orcamento_total_periodo=1000,
                orcamento_categoria_periodo=300,
                consumo_atual_total=950,
                consumo_atual_categoria=250,
                aporte_externo=AporteExternoInput(
                    valor=300,
                    origem="socios",
                    destino="cat_a",
                    validade_ate=None,
                    aprovado_por=None,
                    observacao="sem aprovador",
                ),
            )
        )
        self.assertIn("aporte_externo_sem_rastreabilidade", out.alertas)
        self.assertFalse(out.aprovado)

    def test_categoria_obrigatoria(self) -> None:
        with self.assertRaises(RegraOrcamentariaInvalida):
            self.use_case.execute(
                ProcessarGovernancaOrcamentariaInput(
                    operador="op_01",
                    correlation_id="corr_orc_err_001",
                    periodo_referencia=date(2026, 2, 1),
                    categoria_id="",
                    valor_compra_sugerida=100,
                    orcamento_total_periodo=1000,
                    orcamento_categoria_periodo=300,
                    consumo_atual_total=400,
                    consumo_atual_categoria=100,
                )
            )

    def test_valor_aprovado_maior_que_sugerido_erro(self) -> None:
        with self.assertRaises(RegraOrcamentariaInvalida):
            self.use_case.execute(
                ProcessarGovernancaOrcamentariaInput(
                    operador="op_01",
                    correlation_id="corr_orc_err_002",
                    periodo_referencia=date(2026, 2, 1),
                    categoria_id="cat_a",
                    valor_compra_sugerida=100,
                    orcamento_total_periodo=1000,
                    orcamento_categoria_periodo=300,
                    consumo_atual_total=400,
                    consumo_atual_categoria=100,
                    aprovacao_excecao=AprovacaoExcecaoInput(
                        aprovado_por="gestor_01",
                        motivo="Teste de limite",
                        valor_aprovado=150,
                    ),
                )
            )


if __name__ == "__main__":
    unittest.main()
