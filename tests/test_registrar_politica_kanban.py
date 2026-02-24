"""Testes do vertical slice RegistrarPoliticaKanban."""

import unittest

from wms.application.use_cases.registrar_politica_kanban import (
    RegistrarPoliticaKanban,
    RegistrarPoliticaKanbanInput,
)
from wms.domain.exceptions import RegraKanbanInvalida, SKUInativoOuInexistente
from wms.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from wms.infrastructure.repositories.in_memory_estoque_repository import InMemoryEstoqueRepository
from wms.infrastructure.repositories.in_memory_kanban_repository import (
    InMemoryKanbanRepository,
)


class RegistrarPoliticaKanbanTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.estoque_repo = InMemoryEstoqueRepository(skus_ativos={"sku_001"})
        self.kanban_repo = InMemoryKanbanRepository()
        self.publisher = InMemoryEventPublisher(tenant_id="loja_teste")
        self.use_case = RegistrarPoliticaKanban(
            estoque_repo=self.estoque_repo,
            kanban_repo=self.kanban_repo,
            publisher=self.publisher,
        )

    def test_criar_politica_verde_sucesso(self) -> None:
        output = self.use_case.execute(
            RegistrarPoliticaKanbanInput(
                sku_id="sku_001",
                elegivel=True,
                kanban_ativo=True,
                faixa_atual="verde",
                faixa_verde_min=20,
                faixa_amarela_min=10,
                faixa_vermelha_min=5,
                operador="op_01",
                correlation_id="corr_kanban_ok_001",
                motivo="Politica inicial",
            )
        )

        self.assertTrue(output.kanban_politica_id.startswith("kbp_"))
        self.assertTrue(output.faixa_alterada)
        self.assertEqual("kanban_politica_atualizada", output.evento_emitido)
        self.assertEqual(2, len(self.publisher.events))
        self.assertEqual("kanban_politica_atualizada", self.publisher.events[0]["event_name"])
        self.assertEqual("kanban_faixa_atualizada", self.publisher.events[1]["event_name"])

    def test_alterar_para_vermelha_dispara_reposicao(self) -> None:
        self.use_case.execute(
            RegistrarPoliticaKanbanInput(
                sku_id="sku_001",
                elegivel=True,
                kanban_ativo=True,
                faixa_atual="verde",
                faixa_verde_min=20,
                faixa_amarela_min=10,
                faixa_vermelha_min=5,
                operador="op_01",
                correlation_id="corr_kanban_seed_001",
                motivo="Seed",
            )
        )
        self.publisher.events.clear()

        output = self.use_case.execute(
            RegistrarPoliticaKanbanInput(
                sku_id="sku_001",
                elegivel=True,
                kanban_ativo=True,
                faixa_atual="vermelha",
                faixa_verde_min=20,
                faixa_amarela_min=10,
                faixa_vermelha_min=5,
                operador="op_01",
                correlation_id="corr_kanban_upd_001",
                motivo="Consumo acima do previsto",
            )
        )

        self.assertTrue(output.faixa_alterada)
        self.assertEqual(3, len(self.publisher.events))
        self.assertEqual("kanban_reposicao_disparada", self.publisher.events[-1]["event_name"])
        self.assertEqual(2, len(self.kanban_repo.historicos))

    def test_sku_inativo_erro(self) -> None:
        with self.assertRaises(SKUInativoOuInexistente):
            self.use_case.execute(
                RegistrarPoliticaKanbanInput(
                    sku_id="sku_999",
                    elegivel=True,
                    kanban_ativo=True,
                    faixa_atual="verde",
                    faixa_verde_min=20,
                    faixa_amarela_min=10,
                    faixa_vermelha_min=5,
                    operador="op_01",
                    correlation_id="corr_kanban_err_sku",
                    motivo="Teste",
                )
            )

    def test_faixas_invalidas_erro(self) -> None:
        with self.assertRaises(RegraKanbanInvalida):
            self.use_case.execute(
                RegistrarPoliticaKanbanInput(
                    sku_id="sku_001",
                    elegivel=True,
                    kanban_ativo=True,
                    faixa_atual="verde",
                    faixa_verde_min=10,
                    faixa_amarela_min=20,
                    faixa_vermelha_min=5,
                    operador="op_01",
                    correlation_id="corr_kanban_err_fx",
                    motivo="Teste",
                )
            )

    def test_kanban_ativo_sem_elegibilidade_erro(self) -> None:
        with self.assertRaises(RegraKanbanInvalida):
            self.use_case.execute(
                RegistrarPoliticaKanbanInput(
                    sku_id="sku_001",
                    elegivel=False,
                    kanban_ativo=True,
                    faixa_atual="amarela",
                    faixa_verde_min=20,
                    faixa_amarela_min=10,
                    faixa_vermelha_min=5,
                    operador="op_01",
                    correlation_id="corr_kanban_err_eleg",
                    motivo="Teste",
                )
            )

    def test_motivo_obrigatorio_erro(self) -> None:
        with self.assertRaises(RegraKanbanInvalida):
            self.use_case.execute(
                RegistrarPoliticaKanbanInput(
                    sku_id="sku_001",
                    elegivel=True,
                    kanban_ativo=False,
                    faixa_atual="verde",
                    faixa_verde_min=20,
                    faixa_amarela_min=10,
                    faixa_vermelha_min=5,
                    operador="op_01",
                    correlation_id="corr_kanban_err_motivo",
                    motivo="",
                )
            )


if __name__ == "__main__":
    unittest.main()
