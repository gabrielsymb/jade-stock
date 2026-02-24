"""Testes de integracao PostgreSQL para sazonalidade operacional (extended)."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from uuid import uuid4

from wms.application.use_cases.processar_sazonalidade_operacional import (
    ItemSazonalidadeInput,
    ProcessarSazonalidadeOperacional,
    ProcessarSazonalidadeOperacionalInput,
)
from wms.infrastructure.database.database_config import get_connection_postgres
from wms.infrastructure.database.postgres_transaction_manager import postgres_transaction
from wms.infrastructure.postgres.postgres_estoque_repository import PostgresEstoqueRepository
from wms.infrastructure.postgres.postgres_event_store import PostgresEventStore
from wms.infrastructure.postgres.postgres_politica_reposicao_repository import (
    PostgresPoliticaReposicaoRepository,
)
from wms.infrastructure.postgres.postgres_sinal_externo_repository import (
    PostgresSinalExternoRepository,
)


@unittest.skipUnless(os.getenv("WMS_POSTGRES_DSN"), "WMS_POSTGRES_DSN nao definido")
class PostgresSazonalidadeIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.connection = get_connection_postgres()
        except Exception as exc:
            raise unittest.SkipTest(f"Postgres indisponivel: {exc}") from exc
        cls.connection.autocommit = True
        cls.schema_name = f"wms_it_sazo_{uuid4().hex[:8]}"

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
            cursor.execute("DELETE FROM sinal_externo")
            cursor.execute("DELETE FROM politica_reposicao")
            cursor.execute("DELETE FROM event_store")
            cursor.execute("DELETE FROM sku")
            cursor.execute("DELETE FROM item_master")

            cursor.execute(
                """
                INSERT INTO item_master (item_master_id, item_nome)
                VALUES ('itm_001', 'Item Sazonalidade')
                """
            )
            cursor.execute(
                """
                INSERT INTO sku (sku_id, sku_codigo, sku_nome, item_master_id, status_ativo)
                VALUES ('sku_001', 'sku_001', 'SKU Sazonalidade', 'itm_001', TRUE)
                """
            )
            cursor.execute(
                """
                INSERT INTO politica_reposicao (
                    politica_reposicao_id,
                    sku_id,
                    classe_abc,
                    cobertura_dias,
                    giro_periodo,
                    lead_time_dias,
                    fator_sazonal,
                    sazonalidade_status,
                    janela_analise_meses,
                    shelf_life_dias,
                    risco_vencimento,
                    updated_by,
                    correlation_id
                )
                VALUES (
                    'prp_seed_001',
                    'sku_001',
                    'A',
                    10,
                    8,
                    2,
                    1.0,
                    'inativo',
                    24,
                    20,
                    'baixo',
                    'seed',
                    'corr_seed_sazo_001'
                )
                """
            )

    def test_processar_sazonalidade_persiste_sinal_e_politica(self) -> None:
        estoque_repo = PostgresEstoqueRepository(self.connection)
        politica_repo = PostgresPoliticaReposicaoRepository(self.connection)
        sinal_repo = PostgresSinalExternoRepository(self.connection)
        publisher = PostgresEventStore(self.connection, tenant_id="loja_teste")
        use_case = ProcessarSazonalidadeOperacional(
            estoque_repo=estoque_repo,
            politica_repo=politica_repo,
            sinal_repo=sinal_repo,
            publisher=publisher,
        )

        with postgres_transaction(self.connection):
            out = use_case.execute(
                ProcessarSazonalidadeOperacionalInput(
                    operador="op_sazo",
                    correlation_id="corr_sazo_pg_001",
                    itens=[
                        ItemSazonalidadeInput(
                            sku_id="sku_001",
                            fator_sazonal=1.2,
                            confianca_modelo=0.9,
                            janela_analise_meses=24,
                            mudanca_estrutural=False,
                            origem_motor="stats_engine",
                            versao_modelo="v1",
                        )
                    ],
                )
            )

        self.assertEqual(1, out.itens_processados)
        self.assertEqual("sazonalidade_processada", out.evento_emitido)

        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM sinal_externo")
            sinais = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT cobertura_dias, sazonalidade_status FROM politica_reposicao WHERE sku_id = 'sku_001'"
            )
            row = cursor.fetchone()
            cobertura = float(row[0])
            status = row[1]
            cursor.execute(
                "SELECT COUNT(*) FROM event_store WHERE event_name IN ('sazonalidade_item_processada', 'sazonalidade_processada')"
            )
            events = int(cursor.fetchone()[0])

        self.assertEqual(1, sinais)
        self.assertEqual(12.0, cobertura)
        self.assertEqual("ativo", status)
        self.assertEqual(2, events)


if __name__ == "__main__":
    unittest.main()
