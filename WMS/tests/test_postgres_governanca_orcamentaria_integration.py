"""Testes de integracao PostgreSQL para governanca orcamentaria (extended)."""

from __future__ import annotations

import os
import unittest
from datetime import date
from pathlib import Path
from uuid import uuid4

from wms.application.use_cases.processar_governanca_orcamentaria import (
    AprovacaoExcecaoInput,
    ProcessarGovernancaOrcamentaria,
    ProcessarGovernancaOrcamentariaInput,
)
from wms.domain.exceptions import RegraOrcamentariaInvalida
from wms.infrastructure.database.database_config import get_connection_postgres
from wms.infrastructure.database.postgres_transaction_manager import postgres_transaction
from wms.infrastructure.postgres.postgres_event_store import PostgresEventStore
from wms.infrastructure.postgres.postgres_orcamento_repository import (
    PostgresOrcamentoRepository,
)


@unittest.skipUnless(os.getenv("WMS_POSTGRES_DSN"), "WMS_POSTGRES_DSN nao definido")
class PostgresGovernancaOrcamentariaIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.connection = get_connection_postgres()
        except Exception as exc:
            raise unittest.SkipTest(f"Postgres indisponivel: {exc}") from exc
        cls.connection.autocommit = True
        cls.schema_name = f"wms_it_orc_{uuid4().hex[:8]}"

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
            cursor.execute("DELETE FROM compra_excecao")
            cursor.execute("DELETE FROM aporte_externo")
            cursor.execute("DELETE FROM orcamento_categoria")
            cursor.execute("DELETE FROM orcamento_periodo")
            cursor.execute("DELETE FROM event_store")

    def test_processar_governanca_com_excecao_aprovada(self) -> None:
        repo = PostgresOrcamentoRepository(self.connection)
        publisher = PostgresEventStore(self.connection, tenant_id="loja_teste")
        use_case = ProcessarGovernancaOrcamentaria(repo, publisher)

        with postgres_transaction(self.connection):
            out = use_case.execute(
                ProcessarGovernancaOrcamentariaInput(
                    operador="op_orc",
                    correlation_id="corr_orc_pg_001",
                    periodo_referencia=date(2026, 2, 1),
                    categoria_id="cat_a",
                    valor_compra_sugerida=700,
                    orcamento_total_periodo=1000,
                    orcamento_categoria_periodo=600,
                    consumo_atual_total=500,
                    consumo_atual_categoria=100,
                    aprovacao_excecao=AprovacaoExcecaoInput(
                        aprovado_por="gestor_01",
                        motivo="Item critico",
                        valor_aprovado=700,
                    ),
                )
            )

        self.assertTrue(out.aprovado)
        self.assertIn("compra_acima_orcamento_total", out.alertas)

        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM orcamento_periodo")
            periodos = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM orcamento_categoria")
            categorias = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM compra_excecao")
            excecoes = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT COUNT(*) FROM event_store WHERE event_name = 'governanca_orcamentaria_processada'"
            )
            events = int(cursor.fetchone()[0])

        self.assertEqual(1, periodos)
        self.assertEqual(1, categorias)
        self.assertEqual(1, excecoes)
        self.assertEqual(1, events)

    def test_processar_governanca_com_aprovacao_parcial_respeita_valor_aprovado(self) -> None:
        repo = PostgresOrcamentoRepository(self.connection)
        publisher = PostgresEventStore(self.connection, tenant_id="loja_teste")
        use_case = ProcessarGovernancaOrcamentaria(repo, publisher)

        with postgres_transaction(self.connection):
            out = use_case.execute(
                ProcessarGovernancaOrcamentariaInput(
                    operador="op_orc",
                    correlation_id="corr_orc_pg_002",
                    periodo_referencia=date(2026, 2, 1),
                    categoria_id="cat_a",
                    valor_compra_sugerida=700,
                    orcamento_total_periodo=1000,
                    orcamento_categoria_periodo=600,
                    consumo_atual_total=500,
                    consumo_atual_categoria=100,
                    aprovacao_excecao=AprovacaoExcecaoInput(
                        aprovado_por="gestor_01",
                        motivo="Aprovar parcialmente",
                        valor_aprovado=400,
                    ),
                )
            )

        self.assertTrue(out.aprovado)
        self.assertEqual(900, out.consumo_total_projetado)
        self.assertEqual(500, out.consumo_categoria_projetado)

        with self.connection.cursor() as cursor:
            cursor.execute(
                "SELECT consumo_orcamento FROM orcamento_periodo WHERE periodo_referencia = %s",
                (date(2026, 2, 1),),
            )
            consumo_total = float(cursor.fetchone()[0])
            cursor.execute(
                """
                SELECT consumo_categoria
                FROM orcamento_categoria
                WHERE categoria_id = %s
                """,
                ("cat_a",),
            )
            consumo_categoria = float(cursor.fetchone()[0])

        self.assertEqual(900.0, consumo_total)
        self.assertEqual(500.0, consumo_categoria)

    def test_valor_aprovado_maior_que_sugerido_lanca_erro(self) -> None:
        repo = PostgresOrcamentoRepository(self.connection)
        publisher = PostgresEventStore(self.connection, tenant_id="loja_teste")
        use_case = ProcessarGovernancaOrcamentaria(repo, publisher)

        with self.assertRaisesRegex(
            RegraOrcamentariaInvalida, "valor_aprovado nao pode ser maior"
        ):
            with postgres_transaction(self.connection):
                use_case.execute(
                    ProcessarGovernancaOrcamentariaInput(
                        operador="op_orc",
                        correlation_id="corr_orc_pg_003",
                        periodo_referencia=date(2026, 2, 1),
                        categoria_id="cat_a",
                        valor_compra_sugerida=100,
                        orcamento_total_periodo=1000,
                        orcamento_categoria_periodo=600,
                        consumo_atual_total=500,
                        consumo_atual_categoria=100,
                        aprovacao_excecao=AprovacaoExcecaoInput(
                            aprovado_por="gestor_01",
                            motivo="Limite excedido",
                            valor_aprovado=120,
                        ),
                    )
                )


if __name__ == "__main__":
    unittest.main()
