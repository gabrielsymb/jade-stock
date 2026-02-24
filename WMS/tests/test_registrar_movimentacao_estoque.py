"""Testes do vertical slice RegistrarMovimentacaoEstoque."""

import unittest

from wms.application.use_cases.registrar_movimentacao_estoque import (
    RegistrarMovimentacaoEstoque,
    RegistrarMovimentacaoEstoqueInput,
)
from wms.domain.exceptions import (
    EnderecoInvalido,
    EstoqueInsuficiente,
    QuantidadeInvalida,
    SKUInativoOuInexistente,
    TipoMovimentacaoInvalido,
)
from wms.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from wms.infrastructure.repositories.in_memory_estoque_repository import InMemoryEstoqueRepository
from wms.infrastructure.repositories.in_memory_movimentacao_repository import (
    InMemoryMovimentacaoRepository,
)


class RegistrarMovimentacaoEstoqueTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.estoque_repo = InMemoryEstoqueRepository(
            skus_ativos={"sku_001"},
            enderecos_validos={"DEP-A-01", "LOJA-FR-01", "LOJA-AV-01"},
        )
        self.mov_repo = InMemoryMovimentacaoRepository()
        self.publisher = InMemoryEventPublisher(tenant_id="loja_teste")

        self.estoque_repo.saldos[("sku_001", "DEP-A-01")] = 20.0

        self.use_case = RegistrarMovimentacaoEstoque(
            movimentacao_repo=self.mov_repo,
            estoque_repo=self.estoque_repo,
            publisher=self.publisher,
        )

    def test_transferencia_sucesso_atualiza_saldo_e_emite_evento(self) -> None:
        output = self.use_case.execute(
            RegistrarMovimentacaoEstoqueInput(
                sku_id="sku_001",
                tipo_movimentacao="transferencia",
                quantidade=5,
                endereco_origem="DEP-A-01",
                endereco_destino="LOJA-FR-01",
                operador="op_01",
                correlation_id="corr_ok_001",
            )
        )

        self.assertTrue(output.saldo_atualizado)
        self.assertEqual("movimentacao_estoque_registrada", output.evento_emitido)
        self.assertEqual(15.0, self.estoque_repo.saldos[("sku_001", "DEP-A-01")])
        self.assertEqual(5.0, self.estoque_repo.saldos[("sku_001", "LOJA-FR-01")])
        self.assertEqual(1, len(self.mov_repo.movimentacoes))
        self.assertEqual(1, len(self.publisher.events))

    def test_quantidade_invalida_lanca_erro(self) -> None:
        with self.assertRaises(QuantidadeInvalida):
            self.use_case.execute(
                RegistrarMovimentacaoEstoqueInput(
                    sku_id="sku_001",
                    tipo_movimentacao="entrada",
                    quantidade=0,
                    endereco_origem=None,
                    endereco_destino="LOJA-FR-01",
                    operador="op_01",
                    correlation_id="corr_err_qtd",
                )
            )

    def test_tipo_invalido_lanca_erro(self) -> None:
        with self.assertRaises(TipoMovimentacaoInvalido):
            self.use_case.execute(
                RegistrarMovimentacaoEstoqueInput(
                    sku_id="sku_001",
                    tipo_movimentacao="troca",
                    quantidade=1,
                    endereco_origem="DEP-A-01",
                    endereco_destino="LOJA-FR-01",
                    operador="op_01",
                    correlation_id="corr_err_tipo",
                )
            )

    def test_sku_inativo_lanca_erro(self) -> None:
        with self.assertRaises(SKUInativoOuInexistente):
            self.use_case.execute(
                RegistrarMovimentacaoEstoqueInput(
                    sku_id="sku_999",
                    tipo_movimentacao="entrada",
                    quantidade=1,
                    endereco_origem=None,
                    endereco_destino="LOJA-FR-01",
                    operador="op_01",
                    correlation_id="corr_err_sku",
                )
            )

    def test_endereco_invalido_lanca_erro(self) -> None:
        with self.assertRaises(EnderecoInvalido):
            self.use_case.execute(
                RegistrarMovimentacaoEstoqueInput(
                    sku_id="sku_001",
                    tipo_movimentacao="transferencia",
                    quantidade=1,
                    endereco_origem="DEP-X-99",
                    endereco_destino="LOJA-FR-01",
                    operador="op_01",
                    correlation_id="corr_err_end",
                )
            )

    def test_saldo_insuficiente_lanca_erro(self) -> None:
        with self.assertRaises(EstoqueInsuficiente):
            self.use_case.execute(
                RegistrarMovimentacaoEstoqueInput(
                    sku_id="sku_001",
                    tipo_movimentacao="saida",
                    quantidade=999,
                    endereco_origem="DEP-A-01",
                    endereco_destino=None,
                    operador="op_01",
                    correlation_id="corr_err_saldo",
                )
            )


if __name__ == "__main__":
    unittest.main()
