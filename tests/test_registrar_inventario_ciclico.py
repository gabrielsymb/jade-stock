"""Testes do vertical slice RegistrarInventarioCiclico."""

import unittest

from wms.application.use_cases.registrar_inventario_ciclico import (
    ItemContagemCiclicaInput,
    RegistrarInventarioCiclico,
    RegistrarInventarioCiclicoInput,
)
from wms.domain.exceptions import (
    MotivoObrigatorio,
)
from wms.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from wms.infrastructure.repositories.in_memory_estoque_repository import InMemoryEstoqueRepository
from wms.infrastructure.repositories.in_memory_inventario_repository import (
    InMemoryInventarioRepository,
)
from wms.infrastructure.repositories.in_memory_movimentacao_repository import (
    InMemoryMovimentacaoRepository,
)


class RegistrarInventarioCiclicoTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.estoque_repo = InMemoryEstoqueRepository(
            skus_ativos={"sku_001", "sku_002"},
            enderecos_validos={"DEP-A-01", "DEP-A-02"},
        )
        self.mov_repo = InMemoryMovimentacaoRepository()
        self.inventario_repo = InMemoryInventarioRepository()
        self.publisher = InMemoryEventPublisher(tenant_id="loja_teste")

        self.estoque_repo.saldos[("sku_001", "DEP-A-01")] = 10.0
        self.estoque_repo.saldos[("sku_002", "DEP-A-02")] = 4.0

        self.use_case = RegistrarInventarioCiclico(
            movimentacao_repo=self.mov_repo,
            estoque_repo=self.estoque_repo,
            inventario_repo=self.inventario_repo,
            publisher=self.publisher,
        )

    def test_contagem_com_divergencia_gera_ajustes_e_eventos(self) -> None:
        output = self.use_case.execute(
            RegistrarInventarioCiclicoInput(
                operador="op_ciclo_01",
                correlation_id="corr_ciclo_001",
                motivo="Contagem ciclica semanal",
                itens=[
                    ItemContagemCiclicaInput(
                        sku_id="sku_001",
                        endereco_codigo="DEP-A-01",
                        quantidade_contada=7,
                    ),
                    ItemContagemCiclicaInput(
                        sku_id="sku_002",
                        endereco_codigo="DEP-A-02",
                        quantidade_contada=6,
                    ),
                ],
            )
        )

        self.assertEqual(2, output.itens_processados)
        self.assertEqual(2, output.ajustes_gerados)
        self.assertEqual("inventario_ciclico_processado", output.evento_emitido)
        self.assertEqual(7.0, self.estoque_repo.saldos[("sku_001", "DEP-A-01")])
        self.assertEqual(6.0, self.estoque_repo.saldos[("sku_002", "DEP-A-02")])
        self.assertEqual(2, len(self.inventario_repo.contagens))
        self.assertEqual(2, len(self.mov_repo.movimentacoes))
        self.assertEqual(3, len(self.publisher.events))

    def test_contagem_sem_divergencia_gera_somente_evento_sumario(self) -> None:
        output = self.use_case.execute(
            RegistrarInventarioCiclicoInput(
                operador="op_ciclo_01",
                correlation_id="corr_ciclo_002",
                motivo="Contagem sem ajuste",
                itens=[
                    ItemContagemCiclicaInput(
                        sku_id="sku_001",
                        endereco_codigo="DEP-A-01",
                        quantidade_contada=10,
                    )
                ],
            )
        )

        self.assertEqual(1, output.itens_processados)
        self.assertEqual(0, output.ajustes_gerados)
        self.assertEqual(10.0, self.estoque_repo.saldos[("sku_001", "DEP-A-01")])
        self.assertEqual(1, len(self.inventario_repo.contagens))
        self.assertEqual(0, len(self.mov_repo.movimentacoes))
        self.assertEqual(1, len(self.publisher.events))

    def test_motivo_obrigatorio_lanca_erro(self) -> None:
        with self.assertRaises(MotivoObrigatorio):
            self.use_case.execute(
                RegistrarInventarioCiclicoInput(
                    operador="op_ciclo_01",
                    correlation_id="corr_ciclo_err_001",
                    motivo="",
                    itens=[
                        ItemContagemCiclicaInput(
                            sku_id="sku_001",
                            endereco_codigo="DEP-A-01",
                            quantidade_contada=9,
                        )
                    ],
                )
            )

if __name__ == "__main__":
    unittest.main()
