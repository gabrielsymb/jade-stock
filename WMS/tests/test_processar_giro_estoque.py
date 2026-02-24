"""Testes do vertical slice ProcessarGiroEstoque."""

import unittest

from wms.application.use_cases.processar_giro_estoque import (
    ItemGiroEstoqueInput,
    ProcessarGiroEstoque,
    ProcessarGiroEstoqueInput,
)
from wms.domain.exceptions import QuantidadeInvalida, RegraGiroInvalida, SKUInativoOuInexistente
from wms.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from wms.infrastructure.repositories.in_memory_estoque_repository import InMemoryEstoqueRepository
from wms.infrastructure.repositories.in_memory_politica_reposicao_repository import (
    InMemoryPoliticaReposicaoRepository,
)


class ProcessarGiroEstoqueTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.estoque_repo = InMemoryEstoqueRepository(skus_ativos={"sku_a", "sku_b", "sku_c"})
        self.politica_repo = InMemoryPoliticaReposicaoRepository()
        self.publisher = InMemoryEventPublisher(tenant_id="loja_teste")
        self.use_case = ProcessarGiroEstoque(
            estoque_repo=self.estoque_repo,
            politica_repo=self.politica_repo,
            publisher=self.publisher,
        )

    def test_processar_com_alertas_por_classe(self) -> None:
        out = self.use_case.execute(
            ProcessarGiroEstoqueInput(
                operador="op_01",
                correlation_id="corr_giro_001",
                itens=[
                    ItemGiroEstoqueInput(
                        sku_id="sku_a",
                        classe_abc="A",
                        estoque_atual=100,
                        venda_media_diaria_prevista=5,
                        total_vendido_periodo=40,
                        estoque_medio_periodo=10,
                        ruptura_recorrente=False,
                        lead_time_dias=2,
                        shelf_life_dias=60,
                    ),
                    ItemGiroEstoqueInput(
                        sku_id="sku_b",
                        classe_abc="B",
                        estoque_atual=60,
                        venda_media_diaria_prevista=2,
                        total_vendido_periodo=40,
                        estoque_medio_periodo=10,
                        ruptura_recorrente=False,
                        lead_time_dias=3,
                        shelf_life_dias=120,
                    ),
                    ItemGiroEstoqueInput(
                        sku_id="sku_c",
                        classe_abc="C",
                        estoque_atual=30,
                        venda_media_diaria_prevista=2,
                        total_vendido_periodo=20,
                        estoque_medio_periodo=10,
                        ruptura_recorrente=True,
                        lead_time_dias=4,
                        shelf_life_dias=365,
                    ),
                ],
            )
        )

        self.assertEqual(3, out.itens_processados)
        self.assertEqual("giro_estoque_processado", out.evento_emitido)
        self.assertEqual(6, out.alertas_acionados)
        self.assertEqual(4, len(self.publisher.events))

        pol_a = self.politica_repo.politicas["sku_a"]
        pol_c = self.politica_repo.politicas["sku_c"]
        self.assertEqual(20.0, pol_a["cobertura_dias"])
        self.assertEqual(18.0, pol_c["cobertura_dias"])

    def test_sku_inativo_erro(self) -> None:
        with self.assertRaises(SKUInativoOuInexistente):
            self.use_case.execute(
                ProcessarGiroEstoqueInput(
                    operador="op_01",
                    correlation_id="corr_giro_err_sku",
                    itens=[
                        ItemGiroEstoqueInput(
                            sku_id="sku_x",
                            classe_abc="A",
                            estoque_atual=10,
                            venda_media_diaria_prevista=1,
                            total_vendido_periodo=10,
                            estoque_medio_periodo=5,
                            ruptura_recorrente=False,
                            lead_time_dias=2,
                            shelf_life_dias=30,
                        )
                    ],
                )
            )

    def test_classe_invalida_erro(self) -> None:
        with self.assertRaises(RegraGiroInvalida):
            self.use_case.execute(
                ProcessarGiroEstoqueInput(
                    operador="op_01",
                    correlation_id="corr_giro_err_class",
                    itens=[
                        ItemGiroEstoqueInput(
                            sku_id="sku_a",
                            classe_abc="Z",
                            estoque_atual=10,
                            venda_media_diaria_prevista=1,
                            total_vendido_periodo=10,
                            estoque_medio_periodo=5,
                            ruptura_recorrente=False,
                            lead_time_dias=2,
                            shelf_life_dias=30,
                        )
                    ],
                )
            )

    def test_entrada_vazia_erro(self) -> None:
        with self.assertRaises(QuantidadeInvalida):
            self.use_case.execute(
                ProcessarGiroEstoqueInput(
                    operador="op_01",
                    correlation_id="corr_giro_err_empty",
                    itens=[],
                )
            )


if __name__ == "__main__":
    unittest.main()
