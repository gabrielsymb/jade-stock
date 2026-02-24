"""Testes de integracao PostgreSQL para Kanban (extended)."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from uuid import uuid4

from wms.application.use_cases.registrar_politica_kanban import (
    RegistrarPoliticaKanban,
    RegistrarPoliticaKanbanInput,
)
from wms.infrastructure.database.database_config import get_connection_postgres
from wms.infrastructure.database.postgres_transaction_manager import postgres_transaction
from wms.infrastructure.postgres.postgres_estoque_repository import PostgresEstoqueRepository
from wms.infrastructure.postgres.postgres_event_store import PostgresEventStore
from wms.infrastructure.postgres.postgres_kanban_repository import PostgresKanbanRepository


@unittest.skipUnless(os.getenv("WMS_POSTGRES_DSN"), "WMS_POSTGRES_DSN nao definido")
class PostgresKanbanIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.connection = get_connection_postgres()
        except Exception as exc:
            raise unittest.SkipTest(f"Postgres indisponivel: {exc}") from exc
        cls.connection.autocommit = True
        cls.schema_name = f"wms_it_kanban_{uuid4().hex[:8]}"

        with cls.connection.cursor() as cursor:
            cursor.execute(f"CREATE SCHEMA {cls.schema_name}")
            cursor.execute(f"SET search_path TO {cls.schema_name}, public")

            schema_core = Path("../Database/schema_core.sql")
            if not schema_core.exists():
                schema_core = Path("Database/schema_core.sql")
            cursor.execute(schema_core.read_text(encoding="utf-8"))

            schema_extended = Path("../Database/schema_extended.sql")
            if not schema_extended.exists():
                schema_extended = Path("Database/schema_extended.sql")
            cursor.execute(schema_extended.read_text(encoding="utf-8"))

    @classmethod
    def tearDownClass(cls) -> None:
        with cls.connection.cursor() as cursor:
            cursor.execute(f"DROP SCHEMA IF EXISTS {cls.schema_name} CASCADE")
        cls.connection.close()

    def setUp(self) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(f"SET search_path TO {self.schema_name}, public")
            cursor.execute("DELETE FROM kanban_historico")
            cursor.execute("DELETE FROM kanban_politica")
            cursor.execute("DELETE FROM event_store")
            cursor.execute("DELETE FROM sku")
            cursor.execute("DELETE FROM item_master")

            cursor.execute(
                """
                INSERT INTO item_master (item_master_id, item_nome)
                VALUES ('itm_001', 'Item Kanban')
                """
            )
            cursor.execute(
                """
                INSERT INTO sku (sku_id, sku_codigo, sku_nome, item_master_id, status_ativo)
                VALUES ('sku_001', 'sku_001', 'SKU Kanban', 'itm_001', TRUE)
                """
            )

    def test_kanban_politica_e_historico(self) -> None:
        estoque_repo = PostgresEstoqueRepository(self.connection)
        kanban_repo = PostgresKanbanRepository(self.connection)
        publisher = PostgresEventStore(self.connection, tenant_id="loja_teste")
        use_case = RegistrarPoliticaKanban(
            estoque_repo=estoque_repo,
            kanban_repo=kanban_repo,
            publisher=publisher,
        )

        with postgres_transaction(self.connection):
            out1 = use_case.execute(
                RegistrarPoliticaKanbanInput(
                    sku_id="sku_001",
                    elegivel=True,
                    kanban_ativo=True,
                    faixa_atual="verde",
                    faixa_verde_min=20,
                    faixa_amarela_min=10,
                    faixa_vermelha_min=5,
                    operador="op_kanban",
                    correlation_id="corr_kanban_pg_001",
                    motivo="Inicial",
                )
            )
            out2 = use_case.execute(
                RegistrarPoliticaKanbanInput(
                    sku_id="sku_001",
                    elegivel=True,
                    kanban_ativo=True,
                    faixa_atual="vermelha",
                    faixa_verde_min=20,
                    faixa_amarela_min=10,
                    faixa_vermelha_min=5,
                    operador="op_kanban",
                    correlation_id="corr_kanban_pg_002",
                    motivo="Ruptura",
                )
            )

        self.assertTrue(out1.kanban_politica_id.startswith("kbp_"))
        self.assertTrue(out2.faixa_alterada)

        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM kanban_politica")
            politicas = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM kanban_historico")
            historicos = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT COUNT(*) FROM event_store WHERE event_name IN ('kanban_politica_atualizada', 'kanban_faixa_atualizada', 'kanban_reposicao_disparada')"
            )
            events = int(cursor.fetchone()[0])

        self.assertEqual(1, politicas)
        self.assertEqual(2, historicos)
        self.assertEqual(5, events)


if __name__ == "__main__":
    unittest.main()
