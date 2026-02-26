"""Testes de consistencia transacional e concorrencia (PostgreSQL)."""

from __future__ import annotations

import os
import threading
import unittest
from pathlib import Path
from uuid import uuid4

from wms.application.use_cases.registrar_movimentacao_estoque import (
    RegistrarMovimentacaoEstoque,
    RegistrarMovimentacaoEstoqueInput,
)
from wms.infrastructure.database.database_config import get_connection_postgres
from wms.infrastructure.database.postgres_transaction_manager import (
    postgres_transaction,
)
from wms.infrastructure.postgres.postgres_estoque_repository import PostgresEstoqueRepository
from wms.infrastructure.postgres.postgres_event_store import PostgresEventStore
from wms.infrastructure.postgres.postgres_movimentacao_repository import (
    PostgresMovimentacaoRepository,
)


class _FailAfterPublish:
    """Publisher de teste: grava evento e falha para forcar rollback."""

    def __init__(self, event_store: PostgresEventStore) -> None:
        self._event_store = event_store

    def publish(self, event_name: str, payload: dict) -> None:
        self._event_store.publish(event_name, payload)
        raise RuntimeError("falha_forcada_pos_evento")


@unittest.skipUnless(os.getenv("WMS_POSTGRES_DSN"), "WMS_POSTGRES_DSN nao definido")
class PostgresTransactionalBehaviorTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.connection = get_connection_postgres()
        except Exception as exc:
            raise unittest.SkipTest(f"Postgres indisponivel: {exc}") from exc
        cls.connection.autocommit = True
        cls.schema_name = f"wms_it_tx_{uuid4().hex[:8]}"

        with cls.connection.cursor() as cursor:
            cursor.execute(f"CREATE SCHEMA {cls.schema_name}")
            cursor.execute(f"SET search_path TO {cls.schema_name}, public")

            schema_sql = Path(__file__).resolve().parents[2] / "Database/schema_core.sql"
            cursor.execute(schema_sql.read_text(encoding="utf-8"))

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
            cursor.execute("DELETE FROM event_store")
            cursor.execute("DELETE FROM recebimento_item")
            cursor.execute("DELETE FROM recebimento")
            cursor.execute("DELETE FROM sku")
            cursor.execute("DELETE FROM item_master")
            cursor.execute("DELETE FROM endereco")

            cursor.execute(
                """
                INSERT INTO item_master (item_master_id, item_nome)
                VALUES ('itm_001', 'Item Teste')
                """
            )
            cursor.execute(
                """
                INSERT INTO sku (sku_id, sku_codigo, sku_nome, item_master_id, status_ativo)
                VALUES ('sku_001', 'sku_001', 'SKU Teste', 'itm_001', TRUE)
                """
            )
            cursor.execute(
                """
                INSERT INTO endereco (endereco_codigo, zona_codigo, tipo_endereco, ativo)
                VALUES ('DEP-A-01', 'DEP', 'reserva', TRUE),
                       ('LOJA-FR-01', 'LOJA', 'venda', TRUE)
                """
            )

    def test_transacao_atomica_commit_saldo_movimentacao_evento(self) -> None:
        estoque_repo = PostgresEstoqueRepository(self.connection)
        mov_repo = PostgresMovimentacaoRepository(self.connection)
        event_store = PostgresEventStore(self.connection, tenant_id="loja_teste")

        use_case = RegistrarMovimentacaoEstoque(
            movimentacao_repo=mov_repo,
            estoque_repo=estoque_repo,
            publisher=event_store,
        )
        data = RegistrarMovimentacaoEstoqueInput(
            sku_id="sku_001",
            tipo_movimentacao="entrada",
            quantidade=10,
            endereco_origem=None,
            endereco_destino="DEP-A-01",
            operador="op_tx",
            correlation_id="corr_tx_commit_001",
            motivo="seed",
        )

        with postgres_transaction(self.connection):
            use_case.execute(data)

        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM movimentacao_estoque")
            mov_count = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM event_store")
            evt_count = int(cursor.fetchone()[0])
            cursor.execute(
                """
                SELECT saldo_disponivel
                FROM saldo_estoque
                WHERE sku_id = 'sku_001' AND endereco_codigo = 'DEP-A-01'
                """
            )
            saldo = float(cursor.fetchone()[0])

        self.assertEqual(1, mov_count)
        self.assertEqual(1, evt_count)
        self.assertEqual(10.0, saldo)

    def test_transacao_atomica_rollback_quando_evento_falha(self) -> None:
        estoque_repo = PostgresEstoqueRepository(self.connection)
        mov_repo = PostgresMovimentacaoRepository(self.connection)
        event_store = PostgresEventStore(self.connection, tenant_id="loja_teste")
        publisher = _FailAfterPublish(event_store)

        use_case = RegistrarMovimentacaoEstoque(
            movimentacao_repo=mov_repo,
            estoque_repo=estoque_repo,
            publisher=publisher,
        )
        data = RegistrarMovimentacaoEstoqueInput(
            sku_id="sku_001",
            tipo_movimentacao="entrada",
            quantidade=10,
            endereco_origem=None,
            endereco_destino="DEP-A-01",
            operador="op_tx",
            correlation_id="corr_tx_rb_001",
            motivo="seed",
        )

        with self.assertRaises(RuntimeError):
            with postgres_transaction(self.connection):
                use_case.execute(data)

        with self.connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM movimentacao_estoque")
            mov_count = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM event_store")
            evt_count = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM saldo_estoque")
            saldo_count = int(cursor.fetchone()[0])

        self.assertEqual(0, mov_count)
        self.assertEqual(0, evt_count)
        self.assertEqual(0, saldo_count)

    def test_concorrencia_transferencia_sem_corrupcao_de_saldo(self) -> None:
        with self.connection.cursor() as cursor:
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
                VALUES ('sld_seed_001', 'sku_001', 'DEP-A-01', 10, 0, 0, 10, 'corr_seed')
                """
            )

        results: list[str] = []

        def worker(corr_id: str) -> None:
            conn = get_connection_postgres()
            try:
                conn.autocommit = True
                with conn.cursor() as cursor:
                    cursor.execute(f"SET search_path TO {self.schema_name}, public")

                estoque_repo = PostgresEstoqueRepository(conn)
                mov_repo = PostgresMovimentacaoRepository(conn)
                event_store = PostgresEventStore(conn, tenant_id="loja_teste")

                use_case = RegistrarMovimentacaoEstoque(
                    movimentacao_repo=mov_repo,
                    estoque_repo=estoque_repo,
                    publisher=event_store,
                )
                data = RegistrarMovimentacaoEstoqueInput(
                    sku_id="sku_001",
                    tipo_movimentacao="transferencia",
                    quantidade=7,
                    endereco_origem="DEP-A-01",
                    endereco_destino="LOJA-FR-01",
                    operador="op_cc",
                    correlation_id=corr_id,
                    motivo="teste_concorrencia",
                )

                with postgres_transaction(conn):
                    use_case.execute(data)
                results.append("ok")
            except Exception:
                results.append("erro")
            finally:
                conn.close()

        t1 = threading.Thread(target=worker, args=("corr_cc_001",))
        t2 = threading.Thread(target=worker, args=("corr_cc_002",))
        t1.start()
        t2.start()
        t1.join()
        t2.join()

        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COALESCE(saldo_disponivel, 0)
                FROM saldo_estoque
                WHERE sku_id = 'sku_001' AND endereco_codigo = 'DEP-A-01'
                """
            )
            origem = float(cursor.fetchone()[0])
            cursor.execute(
                """
                SELECT COALESCE(saldo_disponivel, 0)
                FROM saldo_estoque
                WHERE sku_id = 'sku_001' AND endereco_codigo = 'LOJA-FR-01'
                """
            )
            row = cursor.fetchone()
            destino = float(row[0]) if row else 0.0

        self.assertEqual(2, len(results))
        self.assertEqual(1, results.count("ok"))
        self.assertEqual(1, results.count("erro"))
        self.assertGreaterEqual(origem, 0.0)
        self.assertEqual(10.0, origem + destino)


if __name__ == "__main__":
    unittest.main()
