"""Testes de integracao SQL (core) para adapters PostgreSQL.

Por padrao ficam ignorados se `WMS_POSTGRES_DSN` nao estiver definido.
"""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from uuid import uuid4

from wms.infrastructure.database.database_config import get_connection_postgres
from wms.infrastructure.postgres.postgres_estoque_repository import PostgresEstoqueRepository
from wms.infrastructure.postgres.postgres_movimentacao_repository import (
    PostgresMovimentacaoRepository,
)
from wms.infrastructure.postgres.postgres_recebimento_repository import (
    PostgresRecebimentoRepository,
)


@unittest.skipUnless(os.getenv("WMS_POSTGRES_DSN"), "WMS_POSTGRES_DSN nao definido")
class PostgresCoreIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.connection = get_connection_postgres()
        except Exception as exc:
            raise unittest.SkipTest(f"Postgres indisponivel: {exc}") from exc
        cls.connection.autocommit = True
        cls.schema_name = f"wms_it_{uuid4().hex[:8]}"

        with cls.connection.cursor() as cursor:
            cursor.execute(f"CREATE SCHEMA {cls.schema_name}")
            cursor.execute(f"SET search_path TO {cls.schema_name}, public")

            schema_sql = Path("../Database/schema_core.sql")
            if not schema_sql.exists():
                schema_sql = Path("Database/schema_core.sql")
            sql_text = schema_sql.read_text(encoding="utf-8")
            cursor.execute(sql_text)

    @classmethod
    def tearDownClass(cls) -> None:
        with cls.connection.cursor() as cursor:
            cursor.execute(f"DROP SCHEMA IF EXISTS {cls.schema_name} CASCADE")
        cls.connection.close()

    def setUp(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {self.schema_name}, public")
            cursor.execute("DELETE FROM movimentacao_estoque")
            cursor.execute("DELETE FROM saldo_estoque")
            cursor.execute("DELETE FROM recebimento_item")
            cursor.execute("DELETE FROM recebimento")
            cursor.execute("DELETE FROM event_store")
            cursor.execute("DELETE FROM sku")
            cursor.execute("DELETE FROM item_master")
            cursor.execute("DELETE FROM endereco")

            cursor.execute(
                """
                INSERT INTO item_master (item_master_id, item_nome, categoria_id, classe_abc)
                VALUES ('itm_001', 'Item Teste', 'cat_1', 'A')
                """
            )
            cursor.execute(
                """
                INSERT INTO sku (sku_id, sku_codigo, sku_nome, item_master_id, status_ativo)
                VALUES ('sku_001', 'SKU-COD-001', 'SKU Teste', 'itm_001', TRUE)
                """
            )
            cursor.execute(
                """
                INSERT INTO endereco (endereco_codigo, zona_codigo, tipo_endereco, ativo)
                VALUES ('DEP-A-01', 'DEP', 'reserva', TRUE),
                       ('LOJA-FR-01', 'LOJA', 'venda', TRUE)
                """
            )

        self.estoque_repo = PostgresEstoqueRepository(self.connection)
        self.mov_repo = PostgresMovimentacaoRepository(self.connection)
        self.recebimento_repo = PostgresRecebimentoRepository(self.connection)

    def test_validacoes_basicas_estoque(self) -> None:
        self.assertTrue(self.estoque_repo.validar_sku_ativo("sku_001"))
        self.assertFalse(self.estoque_repo.validar_sku_ativo("sku_999"))
        self.assertTrue(self.estoque_repo.validar_endereco("DEP-A-01"))
        self.assertFalse(self.estoque_repo.validar_endereco("DEP-X-99"))

    def test_movimentacao_transferencia_persiste_e_atualiza_saldo(self) -> None:
        self.estoque_repo.aplicar_movimentacao(
            {
                "sku_id": "sku_001",
                "tipo_movimentacao": "entrada",
                "quantidade": 20,
                "endereco_origem": None,
                "endereco_destino": "DEP-A-01",
                "correlation_id": "corr_seed",
            }
        )

        self.assertTrue(self.estoque_repo.validar_saldo("sku_001", "DEP-A-01", 5))

        self.estoque_repo.aplicar_movimentacao(
            {
                "sku_id": "sku_001",
                "tipo_movimentacao": "transferencia",
                "quantidade": 5,
                "endereco_origem": "DEP-A-01",
                "endereco_destino": "LOJA-FR-01",
                "correlation_id": "corr_transf_001",
            }
        )

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT saldo_disponivel
                FROM saldo_estoque
                WHERE sku_id = 'sku_001' AND endereco_codigo = 'DEP-A-01'
                """
            )
            origem = float(cursor.fetchone()[0])

            cursor.execute(
                """
                SELECT saldo_disponivel
                FROM saldo_estoque
                WHERE sku_id = 'sku_001' AND endereco_codigo = 'LOJA-FR-01'
                """
            )
            destino = float(cursor.fetchone()[0])

        self.assertEqual(15.0, origem)
        self.assertEqual(5.0, destino)

    def test_salvar_movimentacao(self) -> None:
        mov_id = self.mov_repo.salvar_movimentacao(
            {
                "sku_id": "SKU-COD-001",
                "tipo_movimentacao": "ajuste",
                "quantidade": 2,
                "endereco_origem": "DEP-A-01",
                "endereco_destino": None,
                "motivo": "Teste",
                "operador": "op_01",
                "tenant_id": "loja_teste",
                "correlation_id": "corr_mov_001",
            }
        )

        self.assertTrue(mov_id.startswith("mov_"))

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*), MIN(sku_id)
                FROM movimentacao_estoque
                WHERE movimentacao_id = %s
                """,
                (mov_id,),
            )
            count, sku_id = cursor.fetchone()
            count = int(count)

        self.assertEqual(1, count)
        self.assertEqual("sku_001", sku_id)

    def test_salvar_recebimento_e_verificar_duplicidade(self) -> None:
        recebimento_id = self.recebimento_repo.salvar_recebimento(
            {
                "nota_fiscal": "NF-INT-001",
                "fornecedor_id": "forn_int",
                "status": "conferido_com_divergencia",
                "operador": "op_01",
                "tenant_id": "loja_teste",
                "correlation_id": "corr_rec_sql_001",
                "itens": [
                    {
                        "sku_codigo": "SKU-COD-001",
                        "endereco_destino": "DEP-A-01",
                        "quantidade_esperada": 10,
                        "quantidade_conferida": 9,
                        "divergencia": True,
                        "classificacao_divergencia": "falta",
                    }
                ],
            }
        )

        self.assertTrue(recebimento_id.startswith("rec_"))
        self.assertTrue(
            self.recebimento_repo.nota_ja_processada("NF-INT-001", "corr_rec_sql_001")
        )

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM recebimento
                WHERE recebimento_id = %s
                """,
                (recebimento_id,),
            )
            rec_count = int(cursor.fetchone()[0])

            cursor.execute(
                """
                SELECT COUNT(*), MIN(sku_id)
                FROM recebimento_item
                WHERE recebimento_id = %s
                """,
                (recebimento_id,),
            )
            item_count, sku_id = cursor.fetchone()
            item_count = int(item_count)

        self.assertEqual(1, rec_count)
        self.assertEqual(1, item_count)
        self.assertEqual("sku_001", sku_id)


if __name__ == "__main__":
    unittest.main()
