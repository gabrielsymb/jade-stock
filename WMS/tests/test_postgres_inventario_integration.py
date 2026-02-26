"""Testes de integracao PostgreSQL para inventario ciclico (extended)."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from uuid import uuid4

from wms.application.use_cases.registrar_inventario_ciclico import (
    ItemContagemCiclicaInput,
    RegistrarInventarioCiclico,
    RegistrarInventarioCiclicoInput,
)
from wms.infrastructure.database.database_config import get_connection_postgres
from wms.infrastructure.database.postgres_transaction_manager import postgres_transaction
from wms.infrastructure.postgres.postgres_estoque_repository import PostgresEstoqueRepository
from wms.infrastructure.postgres.postgres_event_store import PostgresEventStore
from wms.infrastructure.postgres.postgres_inventario_repository import (
    PostgresInventarioRepository,
)
from wms.infrastructure.postgres.postgres_movimentacao_repository import (
    PostgresMovimentacaoRepository,
)


@unittest.skipUnless(os.getenv("WMS_POSTGRES_DSN"), "WMS_POSTGRES_DSN nao definido")
class PostgresInventarioIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.connection = get_connection_postgres()
        except Exception as exc:
            raise unittest.SkipTest(f"Postgres indisponivel: {exc}") from exc
        cls.connection.autocommit = True
        cls.schema_name = f"wms_it_inv_{uuid4().hex[:8]}"

        with cls.connection.cursor() as cursor:
            cursor.execute(f"CREATE SCHEMA {cls.schema_name}")
            cursor.execute(f"SET search_path TO {cls.schema_name}, public")

            schema_core = Path(__file__).resolve().parents[2] / "Database/schema_core.sql"
            cursor.execute(schema_core.read_text(encoding="utf-8"))

            schema_extended = Path(__file__).resolve().parents[2] / "Database/schema_extended.sql"
            cursor.execute(schema_extended.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        with cls.connection.cursor() as cursor:
            cursor.execute(f"DROP SCHEMA IF EXISTS {cls.schema_name} CASCADE")
        cls.connection.close()

    def setUp(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {self.schema_name}, public")
            cursor.execute("DELETE FROM inventario_contagem")
            cursor.execute("DELETE FROM movimentacao_estoque")
            cursor.execute("DELETE FROM saldo_estoque")
            cursor.execute("DELETE FROM event_store")
            cursor.execute("DELETE FROM sku")
            cursor.execute("DELETE FROM item_master")
            cursor.execute("DELETE FROM endereco")

            cursor.execute(
                """
                INSERT INTO item_master (item_master_id, item_nome)
                VALUES ('itm_001', 'Item Inventario')
                """
            )
            cursor.execute(
                """
                INSERT INTO sku (sku_id, sku_codigo, sku_nome, item_master_id, status_ativo)
                VALUES ('sku_001', 'sku_001', 'SKU Inventario', 'itm_001', TRUE)
                """
            )
            cursor.execute(
                """
                INSERT INTO endereco (endereco_codigo, zona_codigo, tipo_endereco, ativo)
                VALUES ('DEP-A-01', 'DEP', 'reserva', TRUE)
                """
            )
            cursor.execute(
                """
                INSERT INTO saldo_estoque (
                    saldo_estoque_id,
                    sku_id,
                    endereco_codigo,
                    saldo_disponivel,
                    saldo_avariado,
                    saldo_bloqueado,
                    saldo_total,
                    correlation_id
                )
                VALUES ('sld_seed_inv_001', 'sku_001', 'DEP-A-01', 10, 0, 0, 10, 'corr_seed_inv')
                """
            )

    def test_inventario_com_divergencia_salva_contagem_e_ajuste(self) -> None:
        estoque_repo = PostgresEstoqueRepository(self.connection)
        mov_repo = PostgresMovimentacaoRepository(self.connection)
        inventario_repo = PostgresInventarioRepository(self.connection)
        publisher = PostgresEventStore(self.connection, tenant_id="loja_teste")

        use_case = RegistrarInventarioCiclico(
            movimentacao_repo=mov_repo,
            estoque_repo=estoque_repo,
            inventario_repo=inventario_repo,
            publisher=publisher,
        )

        data = RegistrarInventarioCiclicoInput(
            operador="op_inv",
            correlation_id="corr_inv_001",
            motivo="Contagem ciclica",
            itens=[
                ItemContagemCiclicaInput(
                    sku_id="sku_001",
                    endereco_codigo="DEP-A-01",
                    quantidade_contada=8,
                )
            ],
        )

        with postgres_transaction(self.connection):
            out = use_case.execute(data)

        self.assertEqual(1, out.itens_processados)
        self.assertEqual(1, out.ajustes_gerados)

        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM inventario_contagem")
            contagens = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM movimentacao_estoque")
            movs = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM event_store")
            events = int(cursor.fetchone()[0])
            cursor.execute(
                """
                SELECT saldo_disponivel
                FROM saldo_estoque
                WHERE sku_id = 'sku_001' AND endereco_codigo = 'DEP-A-01'
                """
            )
            saldo = float(cursor.fetchone()[0])

        self.assertEqual(1, contagens)
        self.assertEqual(1, movs)
        self.assertEqual(2, events)
        self.assertEqual(8.0, saldo)

    def test_inventario_sem_divergencia_salva_contagem_sem_movimentacao(self) -> None:
        estoque_repo = PostgresEstoqueRepository(self.connection)
        mov_repo = PostgresMovimentacaoRepository(self.connection)
        inventario_repo = PostgresInventarioRepository(self.connection)
        publisher = PostgresEventStore(self.connection, tenant_id="loja_teste")

        use_case = RegistrarInventarioCiclico(
            movimentacao_repo=mov_repo,
            estoque_repo=estoque_repo,
            inventario_repo=inventario_repo,
            publisher=publisher,
        )

        data = RegistrarInventarioCiclicoInput(
            operador="op_inv",
            correlation_id="corr_inv_002",
            motivo="Contagem sem divergencia",
            itens=[
                ItemContagemCiclicaInput(
                    sku_id="sku_001",
                    endereco_codigo="DEP-A-01",
                    quantidade_contada=10,
                )
            ],
        )

        with postgres_transaction(self.connection):
            out = use_case.execute(data)

        self.assertEqual(1, out.itens_processados)
        self.assertEqual(0, out.ajustes_gerados)

        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM inventario_contagem")
            contagens = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM movimentacao_estoque")
            movs = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM event_store")
            events = int(cursor.fetchone()[0])

        self.assertEqual(1, contagens)
        self.assertEqual(0, movs)
        self.assertEqual(1, events)


if __name__ == "__main__":
    unittest.main()
