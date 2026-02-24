"""Testes do vertical slice RegistrarRecebimento."""

import unittest

from wms.application.use_cases.registrar_recebimento import (
    ItemRecebimentoInput,
    RegistrarRecebimento,
    RegistrarRecebimentoInput,
)
from wms.domain.exceptions import (
    DivergenciaNaoClassificada,
    EnderecoInvalido,
    NotaFiscalDuplicada,
    QuantidadeInvalida,
    SKUInativoOuInexistente,
)
from wms.infrastructure.events.in_memory_event_publisher import InMemoryEventPublisher
from wms.infrastructure.repositories.in_memory_estoque_repository import InMemoryEstoqueRepository
from wms.infrastructure.repositories.in_memory_recebimento_repository import (
    InMemoryRecebimentoRepository,
)


class RegistrarRecebimentoTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.estoque_repo = InMemoryEstoqueRepository(
            skus_ativos={"sku_001", "sku_002"},
            enderecos_validos={"DEP-A-01", "DEP-A-02"},
        )
        self.recebimento_repo = InMemoryRecebimentoRepository()
        self.publisher = InMemoryEventPublisher(tenant_id="loja_teste")

        self.use_case = RegistrarRecebimento(
            recebimento_repo=self.recebimento_repo,
            estoque_repo=self.estoque_repo,
            publisher=self.publisher,
        )

    def test_recebimento_sem_divergencia_sucesso(self) -> None:
        output = self.use_case.execute(
            RegistrarRecebimentoInput(
                nota_fiscal="NF-100",
                fornecedor_id="forn_01",
                operador="op_01",
                correlation_id="corr_rec_ok",
                itens=[
                    ItemRecebimentoInput(
                        sku_codigo="sku_001",
                        quantidade_esperada=10,
                        quantidade_conferida=10,
                        endereco_destino="DEP-A-01",
                    )
                ],
            )
        )

        self.assertEqual("conferido", output.status)
        self.assertEqual(1, output.itens_processados)
        self.assertEqual(0, output.itens_com_divergencia)
        self.assertEqual(["recebimento_conferido"], output.eventos_emitidos)
        self.assertEqual(10.0, self.estoque_repo.saldos[("sku_001", "DEP-A-01")])
        self.assertEqual(1, len(self.publisher.events))

    def test_recebimento_com_divergencia_emite_dois_eventos(self) -> None:
        output = self.use_case.execute(
            RegistrarRecebimentoInput(
                nota_fiscal="NF-101",
                fornecedor_id="forn_01",
                operador="op_01",
                correlation_id="corr_rec_div",
                itens=[
                    ItemRecebimentoInput(
                        sku_codigo="sku_002",
                        quantidade_esperada=8,
                        quantidade_conferida=7,
                        endereco_destino="DEP-A-02",
                        classificacao_divergencia="falta",
                    )
                ],
            )
        )

        self.assertEqual("conferido_com_divergencia", output.status)
        self.assertEqual(1, output.itens_com_divergencia)
        self.assertEqual(
            ["recebimento_conferido", "recebimento_divergente"],
            output.eventos_emitidos,
        )
        self.assertEqual(2, len(self.publisher.events))

    def test_nota_duplicada_lanca_erro(self) -> None:
        payload = RegistrarRecebimentoInput(
            nota_fiscal="NF-102",
            fornecedor_id="forn_01",
            operador="op_01",
            correlation_id="corr_dup",
            itens=[
                ItemRecebimentoInput(
                    sku_codigo="sku_001",
                    quantidade_esperada=1,
                    quantidade_conferida=1,
                    endereco_destino="DEP-A-01",
                )
            ],
        )
        self.use_case.execute(payload)

        with self.assertRaises(NotaFiscalDuplicada):
            self.use_case.execute(payload)

    def test_mesma_nota_com_correlation_id_diferente_permite_novo_processamento(self) -> None:
        payload_a = RegistrarRecebimentoInput(
            nota_fiscal="NF-108",
            fornecedor_id="forn_01",
            operador="op_01",
            correlation_id="corr_nf108_a",
            itens=[
                ItemRecebimentoInput(
                    sku_codigo="sku_001",
                    quantidade_esperada=2,
                    quantidade_conferida=2,
                    endereco_destino="DEP-A-01",
                )
            ],
        )
        payload_b = RegistrarRecebimentoInput(
            nota_fiscal="NF-108",
            fornecedor_id="forn_01",
            operador="op_01",
            correlation_id="corr_nf108_b",
            itens=[
                ItemRecebimentoInput(
                    sku_codigo="sku_001",
                    quantidade_esperada=3,
                    quantidade_conferida=3,
                    endereco_destino="DEP-A-01",
                )
            ],
        )

        result_a = self.use_case.execute(payload_a)
        result_b = self.use_case.execute(payload_b)

        self.assertEqual("conferido", result_a.status)
        self.assertEqual("conferido", result_b.status)
        self.assertEqual(2, len(self.recebimento_repo.recebimentos))
        self.assertEqual(5.0, self.estoque_repo.saldos[("sku_001", "DEP-A-01")])

    def test_sku_invalido_lanca_erro(self) -> None:
        with self.assertRaises(SKUInativoOuInexistente):
            self.use_case.execute(
                RegistrarRecebimentoInput(
                    nota_fiscal="NF-103",
                    fornecedor_id="forn_01",
                    operador="op_01",
                    correlation_id="corr_sku_err",
                    itens=[
                        ItemRecebimentoInput(
                            sku_codigo="sku_999",
                            quantidade_esperada=1,
                            quantidade_conferida=1,
                            endereco_destino="DEP-A-01",
                        )
                    ],
                )
            )

    def test_endereco_invalido_lanca_erro(self) -> None:
        with self.assertRaises(EnderecoInvalido):
            self.use_case.execute(
                RegistrarRecebimentoInput(
                    nota_fiscal="NF-104",
                    fornecedor_id="forn_01",
                    operador="op_01",
                    correlation_id="corr_end_err",
                    itens=[
                        ItemRecebimentoInput(
                            sku_codigo="sku_001",
                            quantidade_esperada=1,
                            quantidade_conferida=1,
                            endereco_destino="DEP-X-99",
                        )
                    ],
                )
            )

    def test_divergencia_sem_classificacao_lanca_erro(self) -> None:
        with self.assertRaises(DivergenciaNaoClassificada):
            self.use_case.execute(
                RegistrarRecebimentoInput(
                    nota_fiscal="NF-105",
                    fornecedor_id="forn_01",
                    operador="op_01",
                    correlation_id="corr_div_sem_class",
                    itens=[
                        ItemRecebimentoInput(
                            sku_codigo="sku_001",
                            quantidade_esperada=10,
                            quantidade_conferida=9,
                            endereco_destino="DEP-A-01",
                            classificacao_divergencia=None,
                        )
                    ],
                )
            )

    def test_classificacao_divergencia_invalida_lanca_erro(self) -> None:
        with self.assertRaises(DivergenciaNaoClassificada):
            self.use_case.execute(
                RegistrarRecebimentoInput(
                    nota_fiscal="NF-106",
                    fornecedor_id="forn_01",
                    operador="op_01",
                    correlation_id="corr_div_class_invalida",
                    itens=[
                        ItemRecebimentoInput(
                            sku_codigo="sku_001",
                            quantidade_esperada=10,
                            quantidade_conferida=8,
                            endereco_destino="DEP-A-01",
                            classificacao_divergencia="troca",
                        )
                    ],
                )
            )

    def test_quantidade_negativa_lanca_erro(self) -> None:
        with self.assertRaises(QuantidadeInvalida):
            self.use_case.execute(
                RegistrarRecebimentoInput(
                    nota_fiscal="NF-107",
                    fornecedor_id="forn_01",
                    operador="op_01",
                    correlation_id="corr_qtd_neg",
                    itens=[
                        ItemRecebimentoInput(
                            sku_codigo="sku_001",
                            quantidade_esperada=-1,
                            quantidade_conferida=1,
                            endereco_destino="DEP-A-01",
                        )
                    ],
                )
            )


if __name__ == "__main__":
    unittest.main()
