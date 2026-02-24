"""Testes do vertical slice RegistrarAvariaEstoque."""

import unittest

from wms.application.use_cases.registrar_avaria_estoque import (
    RegistrarAvariaEstoque,
    RegistrarAvariaEstoqueInput,
)
from wms.domain.exceptions import (
    EnderecoInvalido,
    EstoqueInsuficiente,
    MotivoObrigatorio,
    QuantidadeInvalida,
    SKUInativoOuInexistente,
)
from wms.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from wms.infrastructure.repositories.in_memory_estoque_repository import InMemoryEstoqueRepository
from wms.infrastructure.repositories.in_memory_movimentacao_repository import (
    InMemoryMovimentacaoRepository,
)


class RegistrarAvariaEstoqueTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.estoque_repo = InMemoryEstoqueRepository(
            skus_ativos={"sku_001"},
            enderecos_validos={"DEP-A-01"},
        )
        self.mov_repo = InMemoryMovimentacaoRepository()
        self.publisher = InMemoryEventPublisher(tenant_id="loja_teste")
        self.estoque_repo.saldos[("sku_001", "DEP-A-01")] = 10.0

        self.use_case = RegistrarAvariaEstoque(
            movimentacao_repo=self.mov_repo,
            estoque_repo=self.estoque_repo,
            publisher=self.publisher,
        )

    def test_avaria_sucesso(self) -> None:
        output = self.use_case.execute(
            RegistrarAvariaEstoqueInput(
                sku_id="sku_001",
                endereco_codigo="DEP-A-01",
                quantidade_avaria=2,
                operador="op_01",
                correlation_id="corr_avaria_ok",
                motivo="Quebra no picking",
            )
        )

        self.assertTrue(output.saldo_atualizado)
        self.assertEqual("avaria_estoque_registrada", output.evento_emitido)
        self.assertEqual(8.0, self.estoque_repo.saldos[("sku_001", "DEP-A-01")])
        self.assertEqual(1, len(self.mov_repo.movimentacoes))
        self.assertEqual(1, len(self.publisher.events))
        self.assertEqual("avaria", self.mov_repo.movimentacoes[0]["tipo_movimentacao"])

    def test_motivo_obrigatorio_erro(self) -> None:
        with self.assertRaises(MotivoObrigatorio):
            self.use_case.execute(
                RegistrarAvariaEstoqueInput(
                    sku_id="sku_001",
                    endereco_codigo="DEP-A-01",
                    quantidade_avaria=1,
                    operador="op_01",
                    correlation_id="corr_err_motivo",
                    motivo="",
                )
            )

    def test_quantidade_invalida_erro(self) -> None:
        with self.assertRaises(QuantidadeInvalida):
            self.use_case.execute(
                RegistrarAvariaEstoqueInput(
                    sku_id="sku_001",
                    endereco_codigo="DEP-A-01",
                    quantidade_avaria=0,
                    operador="op_01",
                    correlation_id="corr_err_qtd",
                    motivo="Teste",
                )
            )

    def test_sku_inativo_erro(self) -> None:
        with self.assertRaises(SKUInativoOuInexistente):
            self.use_case.execute(
                RegistrarAvariaEstoqueInput(
                    sku_id="sku_999",
                    endereco_codigo="DEP-A-01",
                    quantidade_avaria=1,
                    operador="op_01",
                    correlation_id="corr_err_sku",
                    motivo="Teste",
                )
            )

    def test_endereco_invalido_erro(self) -> None:
        with self.assertRaises(EnderecoInvalido):
            self.use_case.execute(
                RegistrarAvariaEstoqueInput(
                    sku_id="sku_001",
                    endereco_codigo="DEP-X-99",
                    quantidade_avaria=1,
                    operador="op_01",
                    correlation_id="corr_err_end",
                    motivo="Teste",
                )
            )

    def test_saldo_insuficiente_erro(self) -> None:
        with self.assertRaises(EstoqueInsuficiente):
            self.use_case.execute(
                RegistrarAvariaEstoqueInput(
                    sku_id="sku_001",
                    endereco_codigo="DEP-A-01",
                    quantidade_avaria=999,
                    operador="op_01",
                    correlation_id="corr_err_saldo",
                    motivo="Teste",
                )
            )


if __name__ == "__main__":
    unittest.main()
