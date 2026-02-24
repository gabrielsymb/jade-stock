"""Testes de integracao PostgreSQL para Curva ABCD (extended)."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from uuid import uuid4

from wms.application.use_cases.processar_curva_abcd import (
    ItemCurvaABCDInput,
    ProcessarCurvaABCD,
    ProcessarCurvaABCDInput,
)
from wms.infrastructure.database.database_config import get_connection_postgres
from wms.infrastructure.database.postgres_transaction_manager import postgres_transaction
from wms.infrastructure.postgres.postgres_estoque_repository import PostgresEstoqueRepository
from wms.infrastructure.postgres.postgres_event_store import PostgresEventStore
from wms.infrastructure.postgres.postgres_politica_reposicao_repository import (
    PostgresPoliticaReposicaoRepository,
)


@unittest.skipUnless(os.getenv("WMS_POSTGRES_DSN"), "WMS_POSTGRES_DSN nao definido")
class PostgresCurvaABCDIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.connection = get_connection_postgres()
        except Exception as exc:
            raise unittest.SkipTest(f"Postgres indisponivel: {exc}") from exc
        cls.connection.autocommit = True
        cls.schema_name = f"wms_it_abcd_{uuid4().hex[:8]}"

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
            cursor.execute("DELETE FROM politica_reposicao")
            cursor.execute("DELETE FROM event_store")
            cursor.execute("DELETE FROM sku")
            cursor.execute("DELETE FROM item_master")

            cursor.execute(
                """
                INSERT INTO item_master (item_master_id, item_nome)
                VALUES ('itm_001', 'Item ABCD 1'),
                       ('itm_002', 'Item ABCD 2')
                """
            )
            cursor.execute(
                """
                INSERT INTO sku (sku_id, sku_codigo, sku_nome, item_master_id, status_ativo)
                VALUES ('sku_001', 'sku_001', 'SKU ABCD 1', 'itm_001', TRUE),
                       ('sku_002', 'sku_002', 'SKU ABCD 2', 'itm_002', TRUE)
                """
            )

    def test_processar_curva_abcd_persiste_politica(self) -> None:
        estoque_repo = PostgresEstoqueRepository(self.connection)
        politica_repo = PostgresPoliticaReposicaoRepository(self.connection)
        publisher = PostgresEventStore(self.connection, tenant_id="loja_teste")

        use_case = ProcessarCurvaABCD(estoque_repo, politica_repo, publisher)

        with postgres_transaction(self.connection):
            out = use_case.execute(
                ProcessarCurvaABCDInput(
                    operador="op_abcd",
                    correlation_id="corr_abcd_pg_001",
                    itens=[
                        ItemCurvaABCDInput(
                            sku_id="sku_001",
                            impacto_economico=1000,
                            variabilidade=0.10,
                            shelf_life_dias=60,
                            dias_sem_venda=10,
                            giro_periodo=12,
                            lead_time_dias=2,
                        ),
                        ItemCurvaABCDInput(
                            sku_id="sku_002",
                            impacto_economico=200,
                            variabilidade=0.50,
                            shelf_life_dias=9,
                            dias_sem_venda=20,
                            giro_periodo=4,
                            lead_time_dias=5,
                        ),
                    ],
                )
            )

        self.assertEqual(2, out.itens_processados)
        self.assertEqual("curva_abcd_processada", out.evento_emitido)

        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM politica_reposicao")
            politicas = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT COUNT(*) FROM event_store WHERE event_name IN ('curva_abcd_item_processado', 'curva_abcd_processada')"
            )
            events = int(cursor.fetchone()[0])

        self.assertEqual(2, politicas)
        self.assertEqual(3, events)


if __name__ == "__main__":
    unittest.main()
