"""Testes do vertical slice ProcessarSazonalidadeOperacional."""

import unittest

from wms.application.use_cases.processar_sazonalidade_operacional import (
    ItemSazonalidadeInput,
    ProcessarSazonalidadeOperacional,
    ProcessarSazonalidadeOperacionalInput,
)
from wms.domain.exceptions import RegraSazonalidadeInvalida, SKUInativoOuInexistente
from wms.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from wms.infrastructure.repositories.in_memory_estoque_repository import InMemoryEstoqueRepository
from wms.infrastructure.repositories.in_memory_politica_reposicao_repository import (
    InMemoryPoliticaReposicaoRepository,
)
from wms.infrastructure.repositories.in_memory_sinal_externo_repository import (
    InMemorySinalExternoRepository,
)


class ProcessarSazonalidadeOperacionalTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.estoque_repo = InMemoryEstoqueRepository(skus_ativos={"sku_001", "sku_002"})
        self.politica_repo = InMemoryPoliticaReposicaoRepository()
        self.sinal_repo = InMemorySinalExternoRepository()
        self.publisher = InMemoryEventPublisher(tenant_id="loja_teste")

        self.politica_repo.salvar_ou_atualizar_politica(
            {
                "sku_id": "sku_001",
                "classe_abc": "A",
                "cobertura_dias": 10,
                "giro_periodo": 8,
                "lead_time_dias": 2,
                "fator_sazonal": 1.0,
                "sazonalidade_status": "inativo",
                "janela_analise_meses": 24,
                "shelf_life_dias": 20,
                "risco_vencimento": "baixo",
                "updated_by": "seed",
                "correlation_id": "seed_001",
            }
        )
        self.politica_repo.salvar_ou_atualizar_politica(
            {
                "sku_id": "sku_002",
                "classe_abc": "C",
                "cobertura_dias": 8,
                "giro_periodo": 2,
                "lead_time_dias": 4,
                "fator_sazonal": 1.0,
                "sazonalidade_status": "inativo",
                "janela_analise_meses": 24,
                "shelf_life_dias": 30,
                "risco_vencimento": "baixo",
                "updated_by": "seed",
                "correlation_id": "seed_002",
            }
        )

        self.use_case = ProcessarSazonalidadeOperacional(
            estoque_repo=self.estoque_repo,
            politica_repo=self.politica_repo,
            sinal_repo=self.sinal_repo,
            publisher=self.publisher,
        )

    def test_processar_sazonalidade_com_alertas(self) -> None:
        out = self.use_case.execute(
            ProcessarSazonalidadeOperacionalInput(
                operador="op_01",
                correlation_id="corr_sazo_001",
                itens=[
                    ItemSazonalidadeInput(
                        sku_id="sku_001",
                        fator_sazonal=2.0,
                        confianca_modelo=0.9,
                        janela_analise_meses=24,
                        mudanca_estrutural=False,
                        origem_motor="stats_engine",
                    ),
                    ItemSazonalidadeInput(
                        sku_id="sku_002",
                        fator_sazonal=1.3,
                        confianca_modelo=0.5,
                        janela_analise_meses=12,
                        mudanca_estrutural=True,
                        origem_motor="stats_engine",
                    ),
                ],
            )
        )

        self.assertEqual(2, out.itens_processados)
        self.assertEqual("sazonalidade_processada", out.evento_emitido)
        self.assertEqual(4, out.alertas_acionados)

        pol_1 = self.politica_repo.obter_politica("sku_001")
        pol_2 = self.politica_repo.obter_politica("sku_002")
        self.assertEqual(18.0, pol_1["cobertura_dias"])
        self.assertEqual("ativo", pol_1["sazonalidade_status"])
        self.assertEqual(8.0, pol_2["cobertura_dias"])
        self.assertEqual("baixa_confianca", pol_2["sazonalidade_status"])
        self.assertEqual(2, len(self.sinal_repo.sinais))
        self.assertEqual(3, len(self.publisher.events))

    def test_sku_inativo_erro(self) -> None:
        with self.assertRaises(SKUInativoOuInexistente):
            self.use_case.execute(
                ProcessarSazonalidadeOperacionalInput(
                    operador="op_01",
                    correlation_id="corr_sazo_err_sku",
                    itens=[
                        ItemSazonalidadeInput(
                            sku_id="sku_x",
                            fator_sazonal=1.1,
                            confianca_modelo=0.9,
                            janela_analise_meses=24,
                            mudanca_estrutural=False,
                            origem_motor="stats_engine",
                        )
                    ],
                )
            )

    def test_fator_invalido_erro(self) -> None:
        with self.assertRaises(RegraSazonalidadeInvalida):
            self.use_case.execute(
                ProcessarSazonalidadeOperacionalInput(
                    operador="op_01",
                    correlation_id="corr_sazo_err_fator",
                    itens=[
                        ItemSazonalidadeInput(
                            sku_id="sku_001",
                            fator_sazonal=0,
                            confianca_modelo=0.9,
                            janela_analise_meses=24,
                            mudanca_estrutural=False,
                            origem_motor="stats_engine",
                        )
                    ],
                )
            )


if __name__ == "__main__":
    unittest.main()
