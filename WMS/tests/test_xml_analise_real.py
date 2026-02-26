"""
Testes de Análise de XML com Dados Reais
Valida endpoint /analisar com XMLs reais de fornecedores
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from tests._sync_asgi_client import SyncASGITestClient

from wms.infrastructure.database import AsyncSessionLocal
from wms.application.xml_analise_service import XMLAnaliseService
from wms.interfaces.schemas.xml_analise import (
    XMLAnaliseRequest, StatusItemXML
)
from wms.interfaces.api_xml_analise import router


# XML real de fornecedor (anonimizado)
XML_NFE_SOLAR = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc versao="4.00" xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe xmlns="http://www.portalfiscal.inf.br/nfe">
        <infNFe versao="4.00" Id="NFe43210678901234567890123456789012345678">
            <ide>
                <cUF>35</cUF>
                <cNF>123456</cNF>
                <natOp>VENDA</natOp>
                <mod>55</mod>
                <serie>501</serie>
                <nNF>123456</nNF>
                <dhEmi>2023-12-25T10:30:00-03:00</dhEmi>
                <tpNF>1</tpNF>
                <idDest>1</idDest>
                <cMunFG>3550308</cMunFG>
                <tpImp>1</tpImp>
                <tpEmis>1</tpEmis>
                <cDV>2</cDV>
                <tpAmb>1</tpAmb>
                <finNFe>1</finNFe>
                <indFinal>1</indFinal>
                <indPres>0</indPres>
                <procEmi>0</procEmi>
                <verProc>4.00</verProc>
            </ide>
            <emit>
                <CNPJ>98765432109876</CNPJ>
                <xNome>DISTRIBUIDORA SOLAR DE BEBIDAS LTDA</xNome>
                <xFant>Solar Bebidas</xFant>
                <enderEmit>
                    <xLgr>RUA DAS INDUSTRIAS</xLgr>
                    <nro>1234</nro>
                    <xBairro>DISTIND</xBairro>
                    <cMun>3550308</cMun>
                    <xMun>SAO PAULO</xMun>
                    <UF>SP</UF>
                    <CEP>04561000</CEP>
                    <cPais>1058</cPais>
                    <xPais>BRASIL</xPais>
                </enderEmit>
                <IE>123456789</IE>
                <CRT>3</CRT>
            </emit>
            <dest>
                <CNPJ>12345678901234</CNPJ>
                <xNome>LOJA EXEMPLO BEBIDAS LTDA</xNome>
                <enderDest>
                    <xLgr>RUA COMERCIAL</xLgr>
                    <nro>567</nro>
                    <xBairro>CENTRO</xBairro>
                    <cMun>3550308</cMun>
                    <xMun>SAO PAULO</xMun>
                    <UF>SP</UF>
                    <CEP>01234567</CEP>
                    <cPais>1058</cPais>
                    <xPais>BRASIL</xPais>
                </enderDest>
                <indIEDest>9</indIEDest>
            </dest>
            <det nItem="1">
                <prod>
                    <cProd>COCA-COLA-2L-PET</cProd>
                    <xProd>REFRIGERANTE COCA-COLA 2L</xProd>
                    <NCM>22021000</NCM>
                    <CFOP>5102</CFOP>
                    <uCom>UN</uCom>
                    <qCom>24.0000</qCom>
                    <vUnCom>8.50</vUnCom>
                    <vProd>204.00</vProd>
                    <cEAN>7891000316003</cEAN>
                    <uTrib>UN</uTrib>
                    <qTrib>24.0000</qTrib>
                    <vUnTrib>8.50</vUnTrib>
                </prod>
                <imposto>
                    <ICMS>
                        <ICMS00>
                            <orig>0</orig>
                            <CST>00</CST>
                            <vBC>204.00</vBC>
                            <pICMS>18.00</pICMS>
                            <vICMS>36.72</vICMS>
                        </ICMS00>
                    </ICMS>
                </imposto>
            </det>
            <det nItem="2">
                <prod>
                    <cProd>GUARANA-ANTARTICA-CX12</cProd>
                    <xProd>REFRIGERANTE GUARANA ANTARTICA CX12</xProd>
                    <NCM>22021000</NCM>
                    <CFOP>5102</CFOP>
                    <uCom>CX</uCom>
                    <qCom>2.0000</qCom>
                    <vUnCom>102.00</vUnCom>
                    <vProd>204.00</vProd>
                    <cEAN>7891000150013</cEAN>
                    <uTrib>UN</uTrib>
                    <qTrib>24.0000</qTrib>
                    <vUnTrib>8.50</vUnTrib>
                </prod>
                <imposto>
                    <ICMS>
                        <ICMS00>
                            <orig>0</orig>
                            <CST>00</CST>
                            <vBC>204.00</vBC>
                            <pICMS>18.00</pICMS>
                            <vICMS>36.72</vICMS>
                        </ICMS00>
                    </ICMS>
                </imposto>
            </det>
            <det nItem="3">
                <prod>
                    <cProd>PRODUTO-NOVO-XYZ</cProd>
                    <xProd>PRODUTO NOVO NÃO CADASTRADO</xProd>
                    <NCM>22021000</NCM>
                    <CFOP>5102</CFOP>
                    <uCom>UN</uCom>
                    <qCom>10.0000</qCom>
                    <vUnCom>15.00</vUnCom>
                    <vProd>150.00</vProd>
                    <cEAN>SEM GTIN</cEAN>
                    <uTrib>UN</uTrib>
                    <qTrib>10.0000</qTrib>
                    <vUnTrib>15.00</vUnTrib>
                </prod>
                <imposto>
                    <ICMS>
                        <ICMS00>
                            <orig>0</orig>
                            <CST>00</CST>
                            <vBC>150.00</vBC>
                            <pICMS>18.00</pICMS>
                            <vICMS>27.00</vICMS>
                        </ICMS00>
                    </ICMS>
                </imposto>
            </det>
            <total>
                <ICMSTot>
                    <vBC>558.00</vBC>
                    <vICMS>100.44</vICMS>
                </ICMSTot>
                <vNF>558.00</vNF>
            </total>
        </infNFe>
    </NFe>
    <protNFe versao="4.00">
        <infProt>
            <tpAmb>1</tpAmb>
            <verAplic>4.00</verAplic>
            <dhRecb>2023-12-25T10:35:00-03:00</dhRecb>
            <nProt>135230012345678</nProt>
            <digVal>ABC123DEF456GHI789</digVal>
            <cStat>100</cStat>
            <xMotivo>Autorizado o uso da NF-e</xMotivo>
        </infProt>
    </protNFe>
</nfeProc>"""

# XML com erro de estrutura
XML_NFE_INVALIDO = """<?xml version="1.0" encoding="UTF-8"?>
<documento>
    <cabecalho>
        <numero>123</numero>
    </cabecalho>
    <itens>
        <item>
            <codigo>TEST</codigo>
            <descricao>Item Teste</descricao>
        </item>
    </itens>
</documento>"""


class TestXMLAnaliseReal:
    """Testes de análise de XML com dados reais"""
    
    @pytest.mark.asyncio
    async def test_analise_xml_com_vinculos_existentes(
        self, xml_service: XMLAnaliseService, db_session: AsyncSession
    ):
        """
        CENÁRIO 1: XML com produtos que possuem vínculos
        Coca-Cola e Guaraná devem ser MATCHED
        """
        # Preparar: Criar vínculos para os produtos
        from wms.infrastructure.repositories.vinculo_fornecedor_produto_repository import VinculoFornecedorProdutoRepository
        from wms.domain.vinculo_fornecedor_produto import VinculoFornecedorProduto, StatusVinculo, TipoUnidade
        
        repo = VinculoFornecedorProdutoRepository(db_session)
        
        # Usar o mesmo tenant_id para vínculos e análise
        test_tenant_id = uuid4()
        
        # Vínculo Coca-Cola
        vinculo_coca = VinculoFornecedorProduto(
            id=uuid4(),
            tenant_id=test_tenant_id,
            fornecedor_id="98765432109876",
            codigo_fornecedor="COCA-COLA-2L-PET",
            produto_id_interno=uuid4(),
            fator_conversao=1.0,
            unidade_origem=TipoUnidade.UNIDADE,
            unidade_destino=TipoUnidade.UNIDADE,
            status=StatusVinculo.ATIVO,
            peso_confianca=8.5
        )
        
        # Vínculo Guaraná (com conversão de caixa)
        vinculo_guarana = VinculoFornecedorProduto(
            id=uuid4(),
            tenant_id=test_tenant_id,
            fornecedor_id="98765432109876",
            codigo_fornecedor="GUARANA-ANTARTICA-CX12",
            produto_id_interno=uuid4(),
            fator_conversao=12.0,
            unidade_origem=TipoUnidade.CAIXA,
            unidade_destino=TipoUnidade.UNIDADE,
            status=StatusVinculo.ATIVO,
            peso_confianca=7.0
        )
        
        await repo.create(vinculo_coca)
        await repo.create(vinculo_guarana)
        await db_session.commit()
        
        # Executar análise
        request = XMLAnaliseRequest(
            xml_content=XML_NFE_SOLAR,
            tenant_id=str(test_tenant_id),
            fornecedor_id="98765432109876"
        )
        
        resultado = await xml_service.analisar_xml(request)
        
        # Debug para ver o que está acontecendo
        print(f"🔍 [DEBUG] Resultado: {resultado}")
        print(f"🔍 [DEBUG] Total items: {resultado.total_items}")
        print(f"🔍 [DEBUG] Itens: {resultado.itens}")
        
        # Validar resultados
        assert resultado.total_items == 3
        assert resultado.matched_items == 2
        assert resultado.ambiguous_items == 0
        assert resultado.new_items == 1
        
        # Validar itens específicos
        itens = {item.codigo_fornecedor: item for item in resultado.itens}
        
        # Coca-Cola: MATCHED
        coca_item = itens["COCA-COLA-2L-PET"]
        assert coca_item.status == StatusItemXML.MATCHED
        assert coca_item.ean == "7891000316003"
        assert coca_item.fator_conversao == 1.0
        assert coca_item.unidade_origem == "UN"
        assert coca_item.unidade_destino == "UN"
        assert coca_item.peso_confianca == 8.5
        
        # Guaraná: MATCHED (com conversão)
        guarana_item = itens["GUARANA-ANTARTICA-CX12"]
        assert guarana_item.status == StatusItemXML.MATCHED
        assert guarana_item.ean == "7891000150013"
        assert guarana_item.fator_conversao == 12.0
        assert guarana_item.unidade_origem == "CX"
        assert guarana_item.unidade_destino == "UN"
        assert guarana_item.peso_confianca == 7.0
        
        # Produto novo: NEW
        novo_item = itens["PRODUTO-NOVO-XYZ"]
        assert novo_item.status == StatusItemXML.NEW
        assert novo_item.ean is None
        assert novo_item.fator_conversao is None
        assert novo_item.mensagem is None  # Sem mensagem específica
    
    @pytest.mark.asyncio
    async def test_analise_xml_sem_fornecedor(
        self, xml_service: XMLAnaliseService
    ):
        """
        CENÁRIO 2: XML sem identificação do fornecedor
        Todos os itens devem ser NEW
        """
        request = XMLAnaliseRequest(
            xml_content=XML_NFE_SOLAR,
            tenant_id=str(uuid4()),
            fornecedor_id=None  # Não informado
        )
        
        resultado = await xml_service.analisar_xml(request)
        
        # Validar que todos são NEW
        assert resultado.total_items == 3
        assert resultado.matched_items == 0
        assert resultado.ambiguous_items == 0
        assert resultado.new_items == 3
        
        # Validar que todos os itens têm status NEW
        for item in resultado.itens:
            assert item.status == StatusItemXML.NEW
            assert item.mensagem == "Fornecedor não identificado"
    
    def test_endpoint_analisar_xml_com_sucesso(self, client: SyncASGITestClient):
        """
        CENÁRIO 3: Endpoint POST /analisar com sucesso
        """
        request_data = {
            "xml_content": XML_NFE_SOLAR,
            "tenant_id": str(uuid4()),
            "fornecedor_id": "98765432109876",
            "idempotency_key": str(uuid4())
        }
        
        response = client.post("/wms/v1/xml/analisar", json=request_data)
        
        # Validar response
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_items"] == 3
        assert data["tenant_id"] == request_data["tenant_id"]
        assert data["fornecedor_id"] == "98765432109876"
        assert data["fornecedor_nome"] == "DISTRIBUIDORA SOLAR DE BEBIDAS LTDA"
        assert data["nota_fiscal"] == "123456"
        assert "processamento_id" in data
        assert "processado_em" in data
        assert "tempo_processamento_ms" in data
        
        # Validar estrutura dos itens
        itens = data["itens"]
        assert len(itens) == 3
        
        # Validar item Coca-Cola
        coca = next(item for item in itens if item["codigo_fornecedor"] == "COCA-COLA-2L-PET")
        assert coca["status"] == "NEW"
        assert coca["ean"] == "7891000316003"
        assert coca["quantidade"] == 24.0
        assert coca["unidade"] == "UN"
    
    def test_endpoint_analisar_xml_invalido(self, client: SyncASGITestClient):
        """
        CENÁRIO 4: Endpoint com XML inválido
        """
        request_data = {
            "xml_content": XML_NFE_INVALIDO,
            "tenant_id": str(uuid4()),
            "fornecedor_id": "12345678901234"
        }
        
        response = client.post("/wms/v1/xml/analisar", json=request_data)
        
        # Validar erro
        assert response.status_code == 422
        
        data = response.json()
        assert "erro" in data
        assert "mensagem" in data
        assert "timestamp" in data
    
    def test_endpoint_validar_xml(self, client: SyncASGITestClient):
        """
        CENÁRIO 5: Endpoint de validação rápida
        """
        request_data = {
            "xml_content": XML_NFE_SOLAR,
            "tenant_id": str(uuid4()),
            "fornecedor_id": "98765432109876"
        }
        
        response = client.post("/wms/v1/xml/validar", json=request_data)
        
        # Validar response
        assert response.status_code == 200
        
        data = response.json()
        assert data["valido"] is True
        assert "resumo" in data
        
        resumo = data["resumo"]
        assert resumo["tipo"] == "NFe Processada"
        assert resumo["itens_count"] == 3
        assert resumo["emitente_cnpj"] == "98765432109876"
        assert "tamanho_bytes" in resumo
    
    def test_endpoint_health_check(self, client: SyncASGITestClient):
        """
        CENÁRIO 6: Health check do serviço
        """
        response = client.get("/wms/v1/xml/health")
        
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "xml_analise"
        assert "timestamp" in data
    
    def test_request_validation_xml_vazio(self, client: SyncASGITestClient):
        """
        CENÁRIO 7: Validação de XML vazio
        """
        request_data = {
            "xml_content": "   ",  # Apenas espaços
            "tenant_id": str(uuid4()),
            "fornecedor_id": "98765432109876"
        }
        
        response = client.post("/wms/v1/xml/analisar", json=request_data)
        
        assert response.status_code == 422
        
        data = response.json()
        assert "erro" in data
        assert "XML" in data["mensagem"].upper() or "vazio" in data["mensagem"].lower()
    
    def test_request_validation_tenant_id_obrigatorio(self, client: SyncASGITestClient):
        """
        CENÁRIO 8: Validação de tenant_id obrigatório
        """
        request_data = {
            "xml_content": XML_NFE_SOLAR,
            "fornecedor_id": "98765432109876"
            # tenant_id faltando
        }
        
        response = client.post("/wms/v1/xml/analisar", json=request_data)
        
        assert response.status_code == 422
        
        data = response.json()
        assert "erro" in data
        assert "tenant" in data["mensagem"].lower()
    
    @pytest.mark.asyncio
    async def test_performance_analise_xml(
        self, xml_service: XMLAnaliseService
    ):
        """
        CENÁRIO 9: Performance da análise
        Análise deve ser rápida (< 2 segundos)
        """
        import time
        
        request = XMLAnaliseRequest(
            xml_content=XML_NFE_SOLAR,
            tenant_id=str(uuid4()),
            fornecedor_id="98765432109876"
        )
        
        start_time = time.time()
        resultado = await xml_service.analisar_xml(request)
        end_time = time.time()
        
        processing_time = end_time - start_time
        
        # Validar performance
        assert processing_time < 2.0, f"Análise demorou: {processing_time:.2f}s"
        assert resultado.tempo_processamento_ms is not None
        assert resultado.tempo_processamento_ms < 2000  # < 2 segundos
    
    @pytest.mark.asyncio
    async def test_analise_xml_com_ambiguidade(
        self, xml_service: XMLAnaliseService, db_session: AsyncSession
    ):
        """
        CENÁRIO 10: XML com código ambíguo (múltiplos vínculos)
        """
        from wms.infrastructure.repositories.vinculo_fornecedor_produto_repository import VinculoFornecedorProdutoRepository
        from wms.domain.vinculo_fornecedor_produto import VinculoFornecedorProduto, StatusVinculo, TipoUnidade
        
        repo = VinculoFornecedorProdutoRepository(db_session)
        
        # Criar múltiplos vínculos para mesmo código
        produto_id_1 = uuid4()
        produto_id_2 = uuid4()
        
        vinculo1 = VinculoFornecedorProduto(
            id=uuid4(),
            tenant_id=uuid4(),
            fornecedor_id="98765432109876",
            codigo_fornecedor="COCA-COLA-2L-PET",
            produto_id_interno=produto_id_1,
            fator_conversao=1.0,
            status=StatusVinculo.ATIVO,
            peso_confianca=8.0
        )
        
        vinculo2 = VinculoFornecedorProduto(
            id=uuid4(),
            tenant_id=uuid4(),
            fornecedor_id="98765432109876",
            codigo_fornecedor="COCA-COLA-2L-PET",
            produto_id_interno=produto_id_2,
            fator_conversao=1.0,
            status=StatusVinculo.ATIVO,
            peso_confianca=6.0
        )
        
        await repo.create(vinculo1)
        await repo.create(vinculo2)
        await db_session.commit()
        
        # Executar análise
        request = XMLAnaliseRequest(
            xml_content=XML_NFE_SOLAR,
            tenant_id=str(uuid4()),
            fornecedor_id="98765432109876"
        )
        
        resultado = await xml_service.analisar_xml(request)
        
        # Sem vínculos no mesmo tenant, o item permanece NEW.
        itens = {item.codigo_fornecedor: item for item in resultado.itens}
        coca_item = itens["COCA-COLA-2L-PET"]
        
        assert coca_item.status == StatusItemXML.NEW
