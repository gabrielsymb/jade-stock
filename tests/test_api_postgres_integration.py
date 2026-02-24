"""Teste de integracao da API com backend PostgreSQL."""

from __future__ import annotations

import os
import unittest
from pathlib import Path
from uuid import uuid4
from unittest.mock import patch

try:
    from fastapi.testclient import TestClient

    _FASTAPI_AVAILABLE = True
except Exception:
    TestClient = None  # type: ignore[assignment]
    _FASTAPI_AVAILABLE = False

from wms.infrastructure.database.database_config import get_connection_postgres

if _FASTAPI_AVAILABLE:
    from wms.interfaces.api import app as api_module
else:
    api_module = None


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi nao instalado")
@unittest.skipUnless(os.getenv("WMS_POSTGRES_DSN"), "WMS_POSTGRES_DSN nao definido")
class ApiPostgresIntegrationTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        try:
            cls.admin_conn = get_connection_postgres()
        except Exception as exc:
            raise unittest.SkipTest(f"Postgres indisponivel: {exc}") from exc
        cls.admin_conn.autocommit = True
        cls.schema_name = f"wms_it_api_{uuid4().hex[:8]}"

        with cls.admin_conn.cursor() as cursor:
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
        with cls.admin_conn.cursor() as cursor:
            cursor.execute(f"DROP SCHEMA IF EXISTS {cls.schema_name} CASCADE")
        cls.admin_conn.close()

    def setUp(self) -> None:
        with self.admin_conn.cursor() as cursor:
            cursor.execute(f"SET search_path TO {self.schema_name}, public")
            cursor.execute("DELETE FROM compra_excecao")
            cursor.execute("DELETE FROM aporte_externo")
            cursor.execute("DELETE FROM orcamento_categoria")
            cursor.execute("DELETE FROM orcamento_periodo")
            cursor.execute("DELETE FROM kanban_historico")
            cursor.execute("DELETE FROM kanban_politica")
            cursor.execute("DELETE FROM sinal_externo")
            cursor.execute("DELETE FROM politica_reposicao")
            cursor.execute("DELETE FROM movimentacao_estoque")
            cursor.execute("DELETE FROM saldo_estoque")
            cursor.execute("DELETE FROM inventario_contagem")
            cursor.execute("DELETE FROM recebimento_item")
            cursor.execute("DELETE FROM recebimento")
            cursor.execute("DELETE FROM event_store")
            cursor.execute("DELETE FROM idempotency_command")
            cursor.execute("DELETE FROM sku")
            cursor.execute("DELETE FROM item_master")
            cursor.execute("DELETE FROM endereco")

            cursor.execute(
                """
                INSERT INTO item_master (item_master_id, item_nome)
                VALUES ('itm_001', 'Item API')
                """
            )
            cursor.execute(
                """
                INSERT INTO sku (sku_id, sku_codigo, sku_nome, item_master_id, status_ativo)
                VALUES ('sku_001', 'sku_001', 'SKU API', 'itm_001', TRUE)
                """
            )
            cursor.execute(
                """
                INSERT INTO endereco (endereco_codigo, zona_codigo, tipo_endereco, ativo)
                VALUES ('DEP-A-01', 'DEP', 'reserva', TRUE)
                """
            )

    def _connection_for_api(self):
        conn = get_connection_postgres()
        conn.autocommit = True
        with conn.cursor() as cursor:
            cursor.execute(f"SET search_path TO {self.schema_name}, public")
        return conn

    def test_post_movimentacoes_backend_postgres(self) -> None:
        api_module.API_BACKEND = "postgres"
        client = TestClient(api_module.app)

        with patch("wms.interfaces.api.app.get_connection_postgres", new=self._connection_for_api):
            response = client.post(
                "/v1/movimentacoes",
                json={
                    "sku_id": "sku_001",
                    "tipo_movimentacao": "entrada",
                    "quantidade": 10,
                    "endereco_origem": None,
                    "endereco_destino": "DEP-A-01",
                    "operador": "op_api_pg",
                    "correlation_id": "corr_api_pg_mov_001",
                    "motivo": "Carga inicial",
                },
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertTrue(payload["movimentacao_id"].startswith("mov_"))
        self.assertEqual("movimentacao_estoque_registrada", payload["evento_emitido"])

        with self.admin_conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT saldo_disponivel
                FROM saldo_estoque
                WHERE sku_id = 'sku_001' AND endereco_codigo = 'DEP-A-01'
                """
            )
            saldo = float(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM event_store")
            events = int(cursor.fetchone()[0])

        self.assertEqual(10.0, saldo)
        self.assertEqual(1, events)

    def test_post_movimentacoes_idempotencia_mesmo_payload(self) -> None:
        api_module.API_BACKEND = "postgres"
        client = TestClient(api_module.app)
        request_payload = {
            "sku_id": "sku_001",
            "tipo_movimentacao": "entrada",
            "quantidade": 10,
            "endereco_origem": None,
            "endereco_destino": "DEP-A-01",
            "operador": "op_api_pg",
            "correlation_id": "corr_api_pg_mov_idem_001",
            "motivo": "Carga inicial",
        }

        with patch("wms.interfaces.api.app.get_connection_postgres", new=self._connection_for_api):
            response_1 = client.post("/v1/movimentacoes", json=request_payload)
            response_2 = client.post("/v1/movimentacoes", json=request_payload)

        self.assertEqual(200, response_1.status_code)
        self.assertEqual(200, response_2.status_code)
        self.assertEqual(response_1.json(), response_2.json())

        with self.admin_conn.cursor() as cursor:
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
            cursor.execute("SELECT COUNT(*) FROM idempotency_command")
            idem = int(cursor.fetchone()[0])

        self.assertEqual(1, movs)
        self.assertEqual(1, events)
        self.assertEqual(10.0, saldo)
        self.assertEqual(1, idem)

    def test_post_movimentacoes_idempotencia_conflito_payload(self) -> None:
        api_module.API_BACKEND = "postgres"
        client = TestClient(api_module.app)
        payload_base = {
            "sku_id": "sku_001",
            "tipo_movimentacao": "entrada",
            "quantidade": 10,
            "endereco_origem": None,
            "endereco_destino": "DEP-A-01",
            "operador": "op_api_pg",
            "correlation_id": "corr_api_pg_mov_idem_002",
            "motivo": "Carga inicial",
        }
        payload_conflito = {**payload_base, "quantidade": 12}

        with patch("wms.interfaces.api.app.get_connection_postgres", new=self._connection_for_api):
            response_1 = client.post("/v1/movimentacoes", json=payload_base)
            response_2 = client.post("/v1/movimentacoes", json=payload_conflito)

        self.assertEqual(200, response_1.status_code)
        self.assertEqual(409, response_2.status_code)

        with self.admin_conn.cursor() as cursor:
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

        self.assertEqual(1, movs)
        self.assertEqual(1, events)
        self.assertEqual(10.0, saldo)

    def test_post_inventario_ciclico_backend_postgres(self) -> None:
        api_module.API_BACKEND = "postgres"
        client = TestClient(api_module.app)

        with patch("wms.interfaces.api.app.get_connection_postgres", new=self._connection_for_api):
            seed = client.post(
                "/v1/movimentacoes",
                json={
                    "sku_id": "sku_001",
                    "tipo_movimentacao": "entrada",
                    "quantidade": 10,
                    "endereco_origem": None,
                    "endereco_destino": "DEP-A-01",
                    "operador": "op_api_pg",
                    "correlation_id": "corr_api_pg_inv_seed_001",
                    "motivo": "Seed inventario",
                },
            )
            self.assertEqual(200, seed.status_code)

            response = client.post(
                "/v1/inventarios/ciclico",
                json={
                    "operador": "op_api_pg",
                    "correlation_id": "corr_api_pg_inv_001",
                    "motivo": "Contagem ciclica",
                    "itens": [
                        {
                            "sku_id": "sku_001",
                            "endereco_codigo": "DEP-A-01",
                            "quantidade_contada": 8,
                        }
                    ],
                },
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual(1, payload["itens_processados"])
        self.assertEqual(1, payload["ajustes_gerados"])
        self.assertEqual("inventario_ciclico_processado", payload["evento_emitido"])

        with self.admin_conn.cursor() as cursor:
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
        self.assertEqual(2, movs)
        self.assertEqual(3, events)
        self.assertEqual(8.0, saldo)

    def test_post_inventario_ciclico_idempotencia_mesmo_payload(self) -> None:
        api_module.API_BACKEND = "postgres"
        client = TestClient(api_module.app)
        request_payload = {
            "operador": "op_api_pg",
            "correlation_id": "corr_api_pg_inv_idem_001",
            "motivo": "Contagem ciclica",
            "itens": [
                {
                    "sku_id": "sku_001",
                    "endereco_codigo": "DEP-A-01",
                    "quantidade_contada": 8,
                }
            ],
        }

        with patch("wms.interfaces.api.app.get_connection_postgres", new=self._connection_for_api):
            seed = client.post(
                "/v1/movimentacoes",
                json={
                    "sku_id": "sku_001",
                    "tipo_movimentacao": "entrada",
                    "quantidade": 10,
                    "endereco_origem": None,
                    "endereco_destino": "DEP-A-01",
                    "operador": "op_api_pg",
                    "correlation_id": "corr_api_pg_inv_idem_seed_001",
                    "motivo": "Seed inventario",
                },
            )
            self.assertEqual(200, seed.status_code)

            response_1 = client.post("/v1/inventarios/ciclico", json=request_payload)
            response_2 = client.post("/v1/inventarios/ciclico", json=request_payload)

        self.assertEqual(200, response_1.status_code)
        self.assertEqual(200, response_2.status_code)
        self.assertEqual(response_1.json(), response_2.json())

        with self.admin_conn.cursor() as cursor:
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
            cursor.execute("SELECT COUNT(*) FROM idempotency_command")
            idem = int(cursor.fetchone()[0])

        self.assertEqual(1, contagens)
        self.assertEqual(2, movs)
        self.assertEqual(3, events)
        self.assertEqual(8.0, saldo)
        self.assertEqual(2, idem)  # seed de movimentacao + inventario

    def test_post_inventario_ciclico_idempotencia_conflito_payload(self) -> None:
        api_module.API_BACKEND = "postgres"
        client = TestClient(api_module.app)
        payload_base = {
            "operador": "op_api_pg",
            "correlation_id": "corr_api_pg_inv_idem_002",
            "motivo": "Contagem ciclica",
            "itens": [
                {
                    "sku_id": "sku_001",
                    "endereco_codigo": "DEP-A-01",
                    "quantidade_contada": 8,
                }
            ],
        }
        payload_conflito = {
            **payload_base,
            "itens": [
                {
                    "sku_id": "sku_001",
                    "endereco_codigo": "DEP-A-01",
                    "quantidade_contada": 7,
                }
            ],
        }

        with patch("wms.interfaces.api.app.get_connection_postgres", new=self._connection_for_api):
            seed = client.post(
                "/v1/movimentacoes",
                json={
                    "sku_id": "sku_001",
                    "tipo_movimentacao": "entrada",
                    "quantidade": 10,
                    "endereco_origem": None,
                    "endereco_destino": "DEP-A-01",
                    "operador": "op_api_pg",
                    "correlation_id": "corr_api_pg_inv_idem_seed_002",
                    "motivo": "Seed inventario",
                },
            )
            self.assertEqual(200, seed.status_code)

            response_1 = client.post("/v1/inventarios/ciclico", json=payload_base)
            response_2 = client.post("/v1/inventarios/ciclico", json=payload_conflito)

        self.assertEqual(200, response_1.status_code)
        self.assertEqual(409, response_2.status_code)

        with self.admin_conn.cursor() as cursor:
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
        self.assertEqual(2, movs)
        self.assertEqual(3, events)
        self.assertEqual(8.0, saldo)

    def test_post_avarias_backend_postgres(self) -> None:
        api_module.API_BACKEND = "postgres"
        client = TestClient(api_module.app)

        with patch("wms.interfaces.api.app.get_connection_postgres", new=self._connection_for_api):
            seed = client.post(
                "/v1/movimentacoes",
                json={
                    "sku_id": "sku_001",
                    "tipo_movimentacao": "entrada",
                    "quantidade": 10,
                    "endereco_origem": None,
                    "endereco_destino": "DEP-A-01",
                    "operador": "op_api_pg",
                    "correlation_id": "corr_api_pg_avr_seed_001",
                    "motivo": "Seed avaria",
                },
            )
            self.assertEqual(200, seed.status_code)

            response = client.post(
                "/v1/avarias",
                json={
                    "sku_id": "sku_001",
                    "endereco_codigo": "DEP-A-01",
                    "quantidade_avaria": 2,
                    "operador": "op_api_pg",
                    "correlation_id": "corr_api_pg_avr_001",
                    "motivo": "Quebra operacional",
                },
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertTrue(payload["movimentacao_id"].startswith("mov_"))
        self.assertEqual("avaria_estoque_registrada", payload["evento_emitido"])

        with self.admin_conn.cursor() as cursor:
            cursor.execute(
                """
                SELECT saldo_disponivel
                FROM saldo_estoque
                WHERE sku_id = 'sku_001' AND endereco_codigo = 'DEP-A-01'
                """
            )
            saldo = float(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM event_store")
            events = int(cursor.fetchone()[0])

        self.assertEqual(8.0, saldo)
        self.assertEqual(2, events)

    def test_post_kanban_politicas_backend_postgres(self) -> None:
        api_module.API_BACKEND = "postgres"
        client = TestClient(api_module.app)

        with patch("wms.interfaces.api.app.get_connection_postgres", new=self._connection_for_api):
            response = client.post(
                "/v1/kanban/politicas",
                json={
                    "sku_id": "sku_001",
                    "elegivel": True,
                    "kanban_ativo": True,
                    "faixa_atual": "amarela",
                    "faixa_verde_min": 20,
                    "faixa_amarela_min": 10,
                    "faixa_vermelha_min": 5,
                    "operador": "op_api_pg",
                    "correlation_id": "corr_api_pg_kanban_001",
                    "motivo": "Politica inicial",
                },
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertTrue(payload["kanban_politica_id"].startswith("kbp_"))
        self.assertTrue(payload["faixa_alterada"])
        self.assertEqual("kanban_politica_atualizada", payload["evento_emitido"])

        with self.admin_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM kanban_politica")
            politicas = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM kanban_historico")
            historicos = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT COUNT(*) FROM event_store WHERE event_name IN ('kanban_politica_atualizada', 'kanban_faixa_atualizada', 'kanban_reposicao_disparada')"
            )
            events = int(cursor.fetchone()[0])

        self.assertEqual(1, politicas)
        self.assertEqual(1, historicos)
        self.assertEqual(3, events)

    def test_post_curva_abcd_processar_backend_postgres(self) -> None:
        api_module.API_BACKEND = "postgres"
        client = TestClient(api_module.app)

        with self.admin_conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO item_master (item_master_id, item_nome)
                VALUES ('itm_002', 'Item API 2')
                ON CONFLICT (item_master_id) DO NOTHING
                """
            )
            cursor.execute(
                """
                INSERT INTO sku (sku_id, sku_codigo, sku_nome, item_master_id, status_ativo)
                VALUES ('sku_002', 'sku_002', 'SKU API 2', 'itm_002', TRUE)
                ON CONFLICT (sku_id) DO NOTHING
                """
            )

        with patch("wms.interfaces.api.app.get_connection_postgres", new=self._connection_for_api):
            response = client.post(
                "/v1/curva-abcd/processar",
                json={
                    "operador": "op_api_pg",
                    "correlation_id": "corr_api_pg_abcd_001",
                    "itens": [
                        {
                            "sku_id": "sku_001",
                            "impacto_economico": 1000,
                            "variabilidade": 0.10,
                            "shelf_life_dias": 60,
                            "dias_sem_venda": 10,
                            "giro_periodo": 12,
                            "lead_time_dias": 2,
                        },
                        {
                            "sku_id": "sku_002",
                            "impacto_economico": 200,
                            "variabilidade": 0.50,
                            "shelf_life_dias": 9,
                            "dias_sem_venda": 20,
                            "giro_periodo": 4,
                            "lead_time_dias": 5,
                        },
                    ],
                },
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual(2, payload["itens_processados"])
        self.assertEqual("curva_abcd_processada", payload["evento_emitido"])

        with self.admin_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM politica_reposicao")
            politicas = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT COUNT(*) FROM event_store WHERE event_name IN ('curva_abcd_item_processado', 'curva_abcd_processada')"
            )
            events = int(cursor.fetchone()[0])

        self.assertEqual(2, politicas)
        self.assertEqual(3, events)

    def test_post_giro_processar_backend_postgres(self) -> None:
        api_module.API_BACKEND = "postgres"
        client = TestClient(api_module.app)

        with patch("wms.interfaces.api.app.get_connection_postgres", new=self._connection_for_api):
            response = client.post(
                "/v1/giro/processar",
                json={
                    "operador": "op_api_pg",
                    "correlation_id": "corr_api_pg_giro_001",
                    "itens": [
                        {
                            "sku_id": "sku_001",
                            "classe_abc": "A",
                            "estoque_atual": 100,
                            "venda_media_diaria_prevista": 5,
                            "total_vendido_periodo": 40,
                            "estoque_medio_periodo": 10,
                            "ruptura_recorrente": False,
                            "lead_time_dias": 2,
                            "shelf_life_dias": 60,
                        }
                    ],
                },
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual(1, payload["itens_processados"])
        self.assertEqual("giro_estoque_processado", payload["evento_emitido"])

        with self.admin_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM politica_reposicao")
            politicas = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT COUNT(*) FROM event_store WHERE event_name IN ('giro_estoque_item_processado', 'giro_estoque_processado')"
            )
            events = int(cursor.fetchone()[0])

        self.assertEqual(1, politicas)
        self.assertEqual(2, events)

    def test_post_sazonalidade_processar_backend_postgres(self) -> None:
        api_module.API_BACKEND = "postgres"
        client = TestClient(api_module.app)

        with patch("wms.interfaces.api.app.get_connection_postgres", new=self._connection_for_api):
            seed = client.post(
                "/v1/curva-abcd/processar",
                json={
                    "operador": "op_api_pg",
                    "correlation_id": "corr_api_pg_sazo_seed_001",
                    "itens": [
                        {
                            "sku_id": "sku_001",
                            "impacto_economico": 1000,
                            "variabilidade": 0.10,
                            "shelf_life_dias": 20,
                            "dias_sem_venda": 10,
                            "giro_periodo": 12,
                            "lead_time_dias": 2,
                        }
                    ],
                },
            )
            self.assertEqual(200, seed.status_code)

            response = client.post(
                "/v1/sazonalidade/processar",
                json={
                    "operador": "op_api_pg",
                    "correlation_id": "corr_api_pg_sazo_001",
                    "itens": [
                        {
                            "sku_id": "sku_001",
                            "fator_sazonal": 1.2,
                            "confianca_modelo": 0.9,
                            "janela_analise_meses": 24,
                            "mudanca_estrutural": False,
                            "origem_motor": "stats_engine",
                            "versao_modelo": "v1",
                        }
                    ],
                },
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual(1, payload["itens_processados"])
        self.assertEqual("sazonalidade_processada", payload["evento_emitido"])

        with self.admin_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM sinal_externo")
            sinais = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT COUNT(*) FROM event_store WHERE event_name IN ('sazonalidade_item_processada', 'sazonalidade_processada')"
            )
            events = int(cursor.fetchone()[0])

        self.assertEqual(1, sinais)
        self.assertEqual(2, events)

    def test_post_orcamento_simular_backend_postgres(self) -> None:
        api_module.API_BACKEND = "postgres"
        client = TestClient(api_module.app)

        with patch("wms.interfaces.api.app.get_connection_postgres", new=self._connection_for_api):
            response = client.post(
                "/v1/orcamento/simular",
                json={
                    "operador": "op_api_pg",
                    "correlation_id": "corr_api_pg_orc_001",
                    "periodo_referencia": "2026-02-01",
                    "categoria_id": "cat_a",
                    "valor_compra_sugerida": 100,
                    "orcamento_total_periodo": 1000,
                    "orcamento_categoria_periodo": 300,
                    "consumo_atual_total": 400,
                    "consumo_atual_categoria": 100,
                },
            )

        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertTrue(payload["aprovado"])
        self.assertEqual("governanca_orcamentaria_processada", payload["evento_emitido"])

        with self.admin_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM orcamento_periodo")
            periodos = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM orcamento_categoria")
            categorias = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT COUNT(*) FROM event_store WHERE event_name = 'governanca_orcamentaria_processada'"
            )
            events = int(cursor.fetchone()[0])

        self.assertEqual(1, periodos)
        self.assertEqual(1, categorias)
        self.assertEqual(1, events)

    def test_post_orcamento_simular_idempotencia_mesmo_payload(self) -> None:
        api_module.API_BACKEND = "postgres"
        client = TestClient(api_module.app)
        request_payload = {
            "operador": "op_api_pg",
            "correlation_id": "corr_api_pg_orc_idem_001",
            "periodo_referencia": "2026-02-01",
            "categoria_id": "cat_a",
            "valor_compra_sugerida": 100,
            "orcamento_total_periodo": 1000,
            "orcamento_categoria_periodo": 300,
            "consumo_atual_total": 400,
            "consumo_atual_categoria": 100,
        }

        with patch("wms.interfaces.api.app.get_connection_postgres", new=self._connection_for_api):
            response_1 = client.post("/v1/orcamento/simular", json=request_payload)
            response_2 = client.post("/v1/orcamento/simular", json=request_payload)

        self.assertEqual(200, response_1.status_code)
        self.assertEqual(200, response_2.status_code)
        self.assertEqual(response_1.json(), response_2.json())

        with self.admin_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM orcamento_periodo")
            periodos = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM orcamento_categoria")
            categorias = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT COUNT(*) FROM event_store WHERE event_name = 'governanca_orcamentaria_processada'"
            )
            events = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM idempotency_command")
            idem = int(cursor.fetchone()[0])

        self.assertEqual(1, periodos)
        self.assertEqual(1, categorias)
        self.assertEqual(1, events)
        self.assertEqual(1, idem)

    def test_post_orcamento_simular_idempotencia_conflito_payload(self) -> None:
        api_module.API_BACKEND = "postgres"
        client = TestClient(api_module.app)
        payload_base = {
            "operador": "op_api_pg",
            "correlation_id": "corr_api_pg_orc_idem_002",
            "periodo_referencia": "2026-02-01",
            "categoria_id": "cat_a",
            "valor_compra_sugerida": 100,
            "orcamento_total_periodo": 1000,
            "orcamento_categoria_periodo": 300,
            "consumo_atual_total": 400,
            "consumo_atual_categoria": 100,
        }
        payload_conflito = {**payload_base, "valor_compra_sugerida": 150}

        with patch("wms.interfaces.api.app.get_connection_postgres", new=self._connection_for_api):
            response_1 = client.post("/v1/orcamento/simular", json=payload_base)
            response_2 = client.post("/v1/orcamento/simular", json=payload_conflito)

        self.assertEqual(200, response_1.status_code)
        self.assertEqual(409, response_2.status_code)

        with self.admin_conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM orcamento_periodo")
            periodos = int(cursor.fetchone()[0])
            cursor.execute("SELECT COUNT(*) FROM orcamento_categoria")
            categorias = int(cursor.fetchone()[0])
            cursor.execute(
                "SELECT COUNT(*) FROM event_store WHERE event_name = 'governanca_orcamentaria_processada'"
            )
            events = int(cursor.fetchone()[0])

        self.assertEqual(1, periodos)
        self.assertEqual(1, categorias)
        self.assertEqual(1, events)


if __name__ == "__main__":
    unittest.main()
