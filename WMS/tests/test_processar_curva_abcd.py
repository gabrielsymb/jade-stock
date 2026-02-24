"""Testes do vertical slice ProcessarCurvaABCD."""

import unittest

from wms.application.use_cases.processar_curva_abcd import (
    ItemCurvaABCDInput,
    ProcessarCurvaABCD,
    ProcessarCurvaABCDInput,
)
from wms.domain.exceptions import QuantidadeInvalida, SKUInativoOuInexistente
from wms.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from wms.infrastructure.repositories.in_memory_estoque_repository import InMemoryEstoqueRepository
from wms.infrastructure.repositories.in_memory_politica_reposicao_repository import (
    InMemoryPoliticaReposicaoRepository,
)


class ProcessarCurvaABCDTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.estoque_repo = InMemoryEstoqueRepository(skus_ativos={"sku_a", "sku_b", "sku_c"})
        self.politica_repo = InMemoryPoliticaReposicaoRepository()
        self.publisher = InMemoryEventPublisher(tenant_id="loja_teste")
        self.use_case = ProcessarCurvaABCD(
            estoque_repo=self.estoque_repo,
            politica_repo=self.politica_repo,
            publisher=self.publisher,
        )

    def test_processar_com_classe_e_alertas(self) -> None:
        out = self.use_case.execute(
            ProcessarCurvaABCDInput(
                operador="op_01",
                correlation_id="corr_abcd_001",
                itens=[
                    ItemCurvaABCDInput(
                        sku_id="sku_a",
                        impacto_economico=1000,
                        variabilidade=0.10,
                        shelf_life_dias=60,
                        dias_sem_venda=10,
                        giro_periodo=12,
                        lead_time_dias=2,
                    ),
                    ItemCurvaABCDInput(
                        sku_id="sku_b",
                        impacto_economico=200,
                        variabilidade=0.50,
                        shelf_life_dias=9,
                        dias_sem_venda=20,
                        giro_periodo=4,
                        lead_time_dias=5,
                    ),
                    ItemCurvaABCDInput(
                        sku_id="sku_c",
                        impacto_economico=50,
                        variabilidade=0.20,
                        shelf_life_dias=365,
                        dias_sem_venda=120,
                        giro_periodo=0.2,
                        lead_time_dias=7,
                    ),
                ],
            )
        )

        self.assertEqual(3, out.itens_processados)
        self.assertEqual("curva_abcd_processada", out.evento_emitido)
        self.assertEqual(4, out.alertas_acionados)

        pol_a = self.politica_repo.politicas["sku_a"]
        pol_b = self.politica_repo.politicas["sku_b"]
        pol_c = self.politica_repo.politicas["sku_c"]

        self.assertEqual("A", pol_a["classe_abc"])
        self.assertEqual(7.0, pol_a["cobertura_dias"])
        self.assertEqual("C", pol_b["classe_abc"])
        self.assertEqual(7.0, pol_b["cobertura_dias"])
        self.assertEqual("D", pol_c["classe_abc"])
        self.assertEqual(1.0, pol_c["cobertura_dias"])
        self.assertEqual(4, len(self.publisher.events))

    def test_sku_inativo_erro(self) -> None:
        with self.assertRaises(SKUInativoOuInexistente):
            self.use_case.execute(
                ProcessarCurvaABCDInput(
                    operador="op_01",
                    correlation_id="corr_err_sku",
                    itens=[
                        ItemCurvaABCDInput(
                            sku_id="sku_x",
                            impacto_economico=100,
                            variabilidade=0.2,
                            shelf_life_dias=90,
                            dias_sem_venda=10,
                            giro_periodo=2,
                            lead_time_dias=4,
                        )
                    ],
                )
            )

    def test_entrada_vazia_erro(self) -> None:
        with self.assertRaises(QuantidadeInvalida):
            self.use_case.execute(
                ProcessarCurvaABCDInput(
                    operador="op_01",
                    correlation_id="corr_err_empty",
                    itens=[],
                )
            )


if __name__ == "__main__":
    unittest.main()
