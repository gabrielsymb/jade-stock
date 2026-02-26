"""Testes da API minima com backend em memoria."""

from __future__ import annotations

import unittest

try:
    import fastapi  # noqa: F401

    _FASTAPI_AVAILABLE = True
except Exception:
    _FASTAPI_AVAILABLE = False

from tests._sync_asgi_client import SyncASGITestClient as TestClient

if _FASTAPI_AVAILABLE:
    from wms.interfaces.api import app as api_module
else:
    api_module = None


@unittest.skipUnless(_FASTAPI_AVAILABLE, "fastapi nao instalado")
class ApiInMemoryTestCase(unittest.TestCase):
    def setUp(self) -> None:
        api_module.API_BACKEND = "inmemory"
        self.client = TestClient(api_module.app)
        self.addCleanup(self.client.close)

    def test_health(self) -> None:
        response = self.client.get("/v1/health")
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertEqual("ok", payload["status"])
        self.assertEqual("inmemory", payload["backend"])

    def test_post_movimentacoes(self) -> None:
        response = self.client.post(
            "/v1/movimentacoes",
            json={
                "sku_id": "sku_001",
                "tipo_movimentacao": "entrada",
                "quantidade": 10,
                "endereco_origem": None,
                "endereco_destino": "DEP-A-01",
                "operador": "op_api",
                "correlation_id": "corr_api_mov_test_001",
                "motivo": "Carga inicial",
            },
        )
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertTrue(payload["movimentacao_id"].startswith("mov_"))
        self.assertEqual("movimentacao_estoque_registrada", payload["evento_emitido"])

    def test_post_ajustes(self) -> None:
        self.client.post(
            "/v1/movimentacoes",
            json={
                "sku_id": "sku_001",
                "tipo_movimentacao": "entrada",
                "quantidade": 10,
                "endereco_origem": None,
                "endereco_destino": "DEP-A-01",
                "operador": "op_api",
                "correlation_id": "corr_api_mov_seed_001",
                "motivo": "Seed",
            },
        )

        response = self.client.post(
            "/v1/ajustes",
            json={
                "sku_id": "sku_001",
                "endereco_codigo": "DEP-A-01",
                "quantidade_ajuste": -2,
                "operador": "op_api",
                "correlation_id": "corr_api_ajuste_test_001",
                "motivo": "Quebra operacional",
            },
        )
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertTrue(payload["movimentacao_id"].startswith("mov_"))
        self.assertEqual("ajuste_estoque_registrado", payload["evento_emitido"])

    def test_post_recebimentos(self) -> None:
        response = self.client.post(
            "/v1/recebimentos",
            json={
                "nota_fiscal": "NF-API-T-001",
                "fornecedor_id": "forn_api",
                "itens": [
                    {
                        "sku_codigo": "sku_001",
                        "quantidade_esperada": 8,
                        "quantidade_conferida": 7,
                        "endereco_destino": "DEP-A-01",
                        "classificacao_divergencia": "falta",
                    }
                ],
                "operador": "op_api",
                "correlation_id": "corr_api_rec_test_001",
            },
        )
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertTrue(payload["recebimento_id"].startswith("rec_"))
        self.assertEqual("conferido_com_divergencia", payload["status"])
        self.assertEqual(1, payload["itens_processados"])
        self.assertEqual(1, payload["itens_com_divergencia"])

    def test_post_avarias(self) -> None:
        self.client.post(
            "/v1/movimentacoes",
            json={
                "sku_id": "sku_001",
                "tipo_movimentacao": "entrada",
                "quantidade": 10,
                "endereco_origem": None,
                "endereco_destino": "DEP-A-01",
                "operador": "op_api",
                "correlation_id": "corr_api_seed_avaria_001",
                "motivo": "Seed avaria",
            },
        )

        response = self.client.post(
            "/v1/avarias",
            json={
                "sku_id": "sku_001",
                "endereco_codigo": "DEP-A-01",
                "quantidade_avaria": 2,
                "operador": "op_api",
                "correlation_id": "corr_api_avaria_test_001",
                "motivo": "Quebra operacional",
            },
        )
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertTrue(payload["movimentacao_id"].startswith("mov_"))
        self.assertEqual("avaria_estoque_registrada", payload["evento_emitido"])

    def test_post_inventario_ciclico(self) -> None:
        self.client.post(
            "/v1/movimentacoes",
            json={
                "sku_id": "sku_001",
                "tipo_movimentacao": "entrada",
                "quantidade": 10,
                "endereco_origem": None,
                "endereco_destino": "DEP-A-01",
                "operador": "op_api",
                "correlation_id": "corr_api_seed_inv_001",
                "motivo": "Seed inventario",
            },
        )

        response = self.client.post(
            "/v1/inventarios/ciclico",
            json={
                "operador": "op_api",
                "correlation_id": "corr_api_inv_test_001",
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

    def test_post_kanban_politicas(self) -> None:
        response = self.client.post(
            "/v1/kanban/politicas",
            json={
                "sku_id": "sku_001",
                "elegivel": True,
                "kanban_ativo": True,
                "faixa_atual": "amarela",
                "faixa_verde_min": 20,
                "faixa_amarela_min": 10,
                "faixa_vermelha_min": 5,
                "operador": "op_api",
                "correlation_id": "corr_api_kanban_001",
                "motivo": "Politica inicial",
            },
        )
        self.assertEqual(200, response.status_code)
        payload = response.json()
        self.assertTrue(payload["kanban_politica_id"].startswith("kbp_"))
        self.assertTrue(payload["faixa_alterada"])
        self.assertEqual("kanban_politica_atualizada", payload["evento_emitido"])

    def test_post_curva_abcd_processar(self) -> None:
        response = self.client.post(
            "/v1/curva-abcd/processar",
            json={
                "operador": "op_api",
                "correlation_id": "corr_api_abcd_001",
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

    def test_post_giro_processar(self) -> None:
        response = self.client.post(
            "/v1/giro/processar",
            json={
                "operador": "op_api",
                "correlation_id": "corr_api_giro_001",
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

    def test_post_sazonalidade_processar(self) -> None:
        self.client.post(
            "/v1/curva-abcd/processar",
            json={
                "operador": "op_api",
                "correlation_id": "corr_api_sazo_seed_001",
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

        response = self.client.post(
            "/v1/sazonalidade/processar",
            json={
                "operador": "op_api",
                "correlation_id": "corr_api_sazo_001",
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

    def test_post_orcamento_simular(self) -> None:
        response = self.client.post(
            "/v1/orcamento/simular",
            json={
                "operador": "op_api",
                "correlation_id": "corr_api_orc_001",
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

    def test_erro_padronizado_domain_error(self) -> None:
        response = self.client.post(
            "/v1/movimentacoes",
            json={
                "sku_id": "sku_inexistente",
                "tipo_movimentacao": "entrada",
                "quantidade": 1,
                "endereco_origem": None,
                "endereco_destino": "DEP-A-01",
                "operador": "op_api",
                "correlation_id": "corr_api_err_001",
                "motivo": "Teste erro",
            },
        )
        self.assertEqual(400, response.status_code)
        payload = response.json()
        self.assertEqual("domain_error", payload["code"])
        self.assertIsInstance(payload["message"], str)
        self.assertEqual("corr_api_err_001", payload["correlation_id"])

    def test_erro_padronizado_validation_error(self) -> None:
        response = self.client.post(
            "/v1/movimentacoes",
            json={
                "sku_id": "sku_001",
                "tipo_movimentacao": "entrada",
                "quantidade": 1,
                "endereco_origem": None,
                "endereco_destino": "DEP-A-01",
                "operador": "op_api",
                # correlation_id ausente de proposito
            },
        )
        self.assertEqual(422, response.status_code)
        payload = response.json()
        self.assertEqual("validation_error", payload["code"])
        self.assertEqual("payload_invalido", payload["message"])
        self.assertIsInstance(payload["details"], list)


if __name__ == "__main__":
    unittest.main()
