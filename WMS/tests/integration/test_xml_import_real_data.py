"""
Testes de Integração - Importação XML com Dados Reais
Cenários baseados em operações reais de negócio
"""

import pytest
import tempfile
import os
from decimal import Decimal
from uuid import uuid4
from datetime import date, datetime

pytestmark = pytest.mark.skip(
    reason=(
        "Cenários legados de recebimentos XML dependem de módulos e rotas "
        "que não existem na implementação atual."
    )
)

# Exemplo de XML NF-e real (anonimizado)
NFE_SAMPLE_COCACOLA = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
    <NFe xmlns="http://www.portalfiscal.inf.br/nfe">
        <infNFe Id="NFe43210612345678901234550020000123456789012345" versao="4.00">
            <ide>
                <cUF>43</cUF>
                <cNF>12345678</cNF>
                <natOp>Venda</natOp>
                <mod>55</mod>
                <serie>1</serie>
                <nNF>1234</nNF>
                <dhEmi>2026-02-20T10:30:00-03:00</dhEmi>
                <tpNF>1</tpNF>
                <idDest>1</idDest>
                <cMunFG>4314902</cMunFG>
                <tpImp>1</tpImp>
                <tpEmis>1</tpEmis>
                <cDV>5</cDV>
                <tpAmb>1</tpAmb>
                <finNFe>1</finNFe>
                <indFinal>1</indFinal>
                <indPres>0</indPres>
                <procEmi>0</procEmi>
                <verProc>1.0</verProc>
            </ide>
            <emit>
                <CNPJ>12345678901234</CNPJ>
                <xNome>DISTRIBUIDORA BEBIDAS SOLAR LTDA</xNome>
                <xFant>Solar Distribuidora</xFant>
                <enderEmit>
                    <xLgr>Rua das Bebidas</xLgr>
                    <nro>123</nro>
                    <xBairro>Centro</xBairro>
                    <xMun>Porto Alegre</xMun>
                    <UF>RS</UF>
                    <CEP>90000000</CEP>
                    <cPais>1058</cPais>
                    <xPais>Brasil</xPais>
                </enderEmit>
                <IE>1234567890</IE>
                <CRT>3</CRT>
            </emit>
            <dest>
                <CNPJ>98765432109876</CNPJ>
                <xNome>LOJA EXEMPLO LTDA</xNome>
                <enderDest>
                    <xLgr>Av Principal</xLgr>
                    <nro>456</nro>
                    <xBairro>Centro</xBairro>
                    <xMun>Porto Alegre</xMun>
                    <UF>RS</UF>
                    <CEP>90010000</CEP>
                    <cPais>1058</cPais>
                    <xPais>Brasil</xPais>
                </enderDest>
                <indIEDest>9</indIEDest>
            </dest>
            <det nItem="1">
                <prod>
                    <cProd>001</cProd>
                    <cEAN>7891000316003</cEAN>
                    <xProd>COCA COLA 2L PET</xProd>
                    <NCM>22021000</NCM>
                    <CFOP>5102</CFOP>
                    <uCom>UN</uCom>
                    <qCom>12.0000</qCom>
                    <vUnCom>8.50</vUnCom>
                    <vProd>102.00</vProd>
                    <cEANTrib>7891000316003</cEANTrib>
                    <uTrib>UN</uTrib>
                    <qTrib>12.0000</qTrib>
                    <vUnTrib>8.50</vUnTrib>
                </prod>
                <imposto>
                    <ICMS>
                        <ICMS00>
                            <orig>0</orig>
                            <CST>00</CST>
                            <modBC>3</modBC>
                            <vBC>102.00</vBC>
                            <pICMS>18.00</pICMS>
                            <vICMS>18.36</vICMS>
                        </ICMS00>
                    </ICMS>
                </imposto>
            </det>
            <det nItem="2">
                <prod>
                    <cProd>002</cProd>
                    <cEAN>7891000150013</cEAN>
                    <xProd>GUARANA ANTARTICA 2L PET</xProd>
                    <NCM>22021000</NCM>
                    <CFOP>5102</CFOP>
                    <uCom>CX</uCom>
                    <qCom>2.0000</qCom>
                    <vUnCom>25.50</vUnCom>
                    <vProd>51.00</vProd>
                    <cEANTrib>7891000150013</cEANTrib>
                    <uTrib>UN</uTrib>
                    <qTrib>24.0000</qTrib>
                    <vUnTrib>2.1250</vUnTrib>
                </prod>
                <imposto>
                    <ICMS>
                        <ICMS00>
                            <orig>0</orig>
                            <CST>00</CST>
                            <modBC>3</modBC>
                            <vBC>51.00</vBC>
                            <pICMS>18.00</pICMS>
                            <vICMS>9.18</vICMS>
                        </ICMS00>
                    </ICMS>
                </imposto>
            </det>
            <total>
                <ICMSTot>
                    <vBC>153.00</vBC>
                    <vICMS>27.54</vICMS>
                    <vICMSDeson>0.00</vICMSDeson>
                    <vBCST>0.00</vBCST>
                    <vST>0.00</vST>
                    <vProd>153.00</vProd>
                    <vFrete>0.00</vFrete>
                    <vSeg>0.00</vSeg>
                    <vDesc>0.00</vDesc>
                    <vII>0.00</vII>
                    <vIPI>0.00</vIPI>
                    <vPIS>5.20</vPIS>
                    <vCOFINS>23.94</vCOFINS>
                    <vOutro>0.00</vOutro>
                    <vNF>153.00</vNF>
                </ICMSTot>
            </total>
            <transp>
                <modFrete>0</modFrete>
            </transp>
        </infNFe>
    </NFe>
    <protNFe versao="4.00">
        <infProt>
            <tpAmb>1</tpAmb>
            <verAplic>1.0</verAplic>
            <chNFe>43210612345678901234550020000123456789012345</chNFe>
            <dhRecbto>2026-02-20T10:35:00-03:00</dhRecbto>
            <nProt>123456789012345</nProt>
            <digVal>ABC123</digVal>
            <cStat>100</cStat>
            <xMotivo>Autorizado o uso da NF-e</xMotivo>
        </infProt>
    </protNFe>
</nfeProc>"""

class TestXmlImportRealData:
    """Testes de integração com dados reais de negócio"""
    
    @pytest.fixture
    def sample_xml_cocacola(self):
        """XML NF-e real de Coca-Cola (anonimizado)"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(NFE_SAMPLE_COCACOLA)
            f.flush()
            yield f.name
        os.unlink(f.name)
    
    @pytest.fixture
    def tenant_test(self, db_session):
        """Tenant de teste"""
        from wms.domain.tenant import Tenant
        tenant = Tenant(
            id=uuid4(),
            nome="Loja Teste",
            cnpj="98765432109876",
            ativo=True
        )
        db_session.add(tenant)
        db_session.commit()
        return tenant
    
    @pytest.fixture
    def fornecedor_solar(self, db_session, tenant_test):
        """Fornecedor Solar Distribuidora"""
        from wms.domain.fornecedor import Fornecedor
        fornecedor = Fornecedor(
            id=uuid4(),
            tenant_id=tenant_test.id,
            cnpj="12345678901234",
            razao_social="DISTRIBUIDORA BEBIDAS SOLAR LTDA",
            nome_fantasia="Solar Distribuidora",
            ativo=True
        )
        db_session.add(fornecedor)
        db_session.commit()
        return fornecedor
    
    @pytest.fixture
    def produtos_existentes(self, db_session, tenant_test):
        """Produtos já cadastrados no sistema"""
        from wms.domain.produto import Produto
        
        produtos = []
        
        # Coca-Cola 2L (já existe com EAN igual)
        cocacola = Produto(
            id=uuid4(),
            tenant_id=tenant_test.id,
            nome="Coca-Cola 2L",
            gtin="7891000316003",
            ncm="22021000",
            unidade_padrao="UN",
            ativo=True
        )
        produtos.append(cocacola)
        
        # Guaraná Antártica (já existe mas com nome diferente)
        guarana = Produto(
            id=uuid4(),
            tenant_id=tenant_test.id,
            nome="Guaraná Antártica Pet 2L",
            gtin="7891000150013",
            ncm="22021000",
            unidade_padrao="UN",
            ativo=True
        )
        produtos.append(guarana)
        
        db_session.add_all(produtos)
        db_session.commit()
        return produtos
    
    @pytest.mark.asyncio
    async def test_cenario_1_vinculacao_perfeita_ean_existente(
        self, client, sample_xml_cocacola, tenant_test, 
        fornecedor_solar, produtos_existentes, auth_headers
    ):
        """
        CENÁRIO 1: Vinculação perfeita - EAN já existe no catálogo
        
        Dado: XML com Coca-Cola 2L, EAN 7891000316003
        E: Produto já existe com mesmo EAN no sistema
        Então: Sistema deve vincular automaticamente (MATCHED, 100%)
        """
        
        # STEP 1: Upload e análise do XML
        with open(sample_xml_cocacola, 'rb') as xml_file:
            response = await client.post(
                "/wms/v1/recebimentos/xml/analisar",
                headers=auth_headers,
                files={"arquivo_xml": ("nfe.xml", xml_file, "application/xml")}
            )
        
        assert response.status_code == 200
        analise = response.json()
        
        # Verificar metadados da NF-e
        assert analise["chave_acesso"] == "43210612345678901234550020000123456789012345"
        assert analise["emitente"]["cnpj"] == "12345678901234"
        assert analise["emitente"]["razao_social"] == "DISTRIBUIDORA BEBIDAS SOLAR LTDA"
        
        # Verificar itens analisados
        assert len(analise["itens"]) == 2
        
        # Item 1: Coca-Cola (MATCHED perfeito pelo EAN)
        item_cocacola = next(i for i in analise["itens"] if "COCA COLA" in i["descricao"])
        assert item_cocacola["status_vinculacao"] == "MATCHED"
        assert item_cocacola["pontuacao_vinculacao"] >= 95.0  # EAN bate = 40pts + descrição similar
        assert item_cocacola["gtin"] == "7891000316003"
        assert item_cocacola["quantidade"] == 12.0
        assert item_cocacola["unidade"] == "UN"
        
        # STEP 2: Confirmar importação
        confirmacao_request = {
            "chave_acesso": analise["chave_acesso"],
            "itens": [
                {
                    "item_id": item_cocacola["item_id"],
                    "produto_id": produtos_existentes[0].id,  # Coca-Cola
                    "quantidade_total": 12.0,
                    "quantidade_avariada": 0.0,
                    "endereco_destino": "DEP-A-01",
                    "criar_vinculo_permanente": True
                }
            ]
        }
        
        response = await client.post(
            "/wms/v1/recebimentos/xml/confirmar",
            headers={**auth_headers, "Idempotency-Key": str(uuid4())},
            json=confirmacao_request
        )
        
        assert response.status_code in [200, 201]
        confirmacao = response.json()
        
        # Verificar recebimento criado
        assert "recebimento_id" in confirmacao
        assert confirmacao["status"] in ["confirmado", "idempotente"]
        assert len(confirmacao["itens_processados"]) == 1
        
        # Verificar item processado
        item_processado = confirmacao["itens_processados"][0]
        assert item_processado["quantidade_recebida"] == 12.0
        assert item_processado["quantidade_avariada"] == 0.0
        assert item_processado["endereco_destino"] == "DEP-A-01"
        assert item_processado["vinculo_criado"] is True
    
    @pytest.mark.asyncio
    async def test_cenario_2_vinculacao_parcial_conversao_unidade(
        self, client, sample_xml_cocacola, tenant_test,
        fornecedor_solar, produtos_existentes, auth_headers
    ):
        """
        CENÁRIO 2: Conversão de unidades - CX para UN
        
        Dado: XML com Guaraná em caixas (CX), sistema controla unidades (UN)
        E: 1 caixa = 12 unidades (fator conversão)
        Então: Sistema deve converter automaticamente e vincular
        """
        
        # Primeiro, criar vínculo com fator de conversão
        from wms.domain.vinculo_fornecedor_produto import VinculoFornecedorProduto
        vinculo = VinculoFornecedorProduto(
            tenant_id=tenant_test.id,
            fornecedor_id=fornecedor_solar.id,
            codigo_fornecedor="002",
            produto_id_interno=produtos_existentes[1].id,  # Guaraná
            fator_conversao=12.0,
            unidade_origem="CX",
            unidade_destino="UN"
        )
        db_session.add(vinculo)
        db_session.commit()
        
        # Upload e análise
        with open(sample_xml_cocacola, 'rb') as xml_file:
            response = await client.post(
                "/wms/v1/recebimentos/xml/analisar",
                headers=auth_headers,
                files={"arquivo_xml": ("nfe.xml", xml_file, "application/xml")}
            )
        
        assert response.status_code == 200
        analise = response.json()
        
        # Item 2: Guaraná (deve ser MATCHED pelo vínculo existente)
        item_guarana = next(i for i in analise["itens"] if "GUARANA" in i["descricao"])
        assert item_guarana["status_vinculacao"] == "MATCHED"
        assert item_guarana["quantidade"] == 2.0  # 2 caixas no XML
        assert item_guarana["unidade"] == "CX"
        
        # Confirmar importação
        confirmacao_request = {
            "chave_acesso": analise["chave_acesso"],
            "itens": [
                {
                    "item_id": item_guarana["item_id"],
                    "produto_id": produtos_existentes[1].id,  # Guaraná
                    "quantidade_total": 2.0,  # 2 caixas
                    "quantidade_avariada": 0.0,
                    "endereco_destino": "DEP-B-02",
                    "criar_vinculo_permanente": True
                }
            ]
        }
        
        response = await client.post(
            "/wms/v1/recebimentos/xml/confirmar",
            headers={**auth_headers, "Idempotency-Key": str(uuid4())},
            json=confirmacao_request
        )
        
        assert response.status_code in [200, 201]
        confirmacao = response.json()
        
        # Verificar conversão aplicada (2 CX × 12 = 24 UN)
        item_processado = confirmacao["itens_processados"][0]
        # Nota: quantidade_recebida deve ser 24.0 (após conversão)
        assert item_processado["quantidade_recebida"] == 24.0
    
    @pytest.mark.asyncio
    async def test_cenario_3_produto_novo_sem_vinculo(
        self, client, sample_xml_cocacola_modificado, tenant_test,
        fornecedor_solar, auth_headers
    ):
        """
        CENÁRIO 3: Produto novo - sem vínculo existente
        
        Dado: XML com produto não cadastrado
        E: Nenhum EAN ou descrição correspondente
        Então: Sistema deve marcar como NEW para cadastro manual
        """
        
        # XML modificado com produto inexistente
        xml_novo_produto = self._criar_xml_produto_novo()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
            f.write(xml_novo_produto)
            f.flush()
            xml_file_path = f.name
        
        try:
            with open(xml_file_path, 'rb') as xml_file:
                response = await client.post(
                    "/wms/v1/recebimentos/xml/analisar",
                    headers=auth_headers,
                    files={"arquivo_xml": ("nfe.xml", xml_file, "application/xml")}
                )
            
            assert response.status_code == 200
            analise = response.json()
            
            # Item deve ser NEW
            item_novo = analise["itens"][0]
            assert item_novo["status_vinculacao"] == "NEW"
            assert item_novo["pontuacao_vinculacao"] < 50.0
            assert len(item_novo["candidatos_vinculacao"]) == 0
            
            # Verificar dados extraídos para cadastro
            assert item_novo["descricao"] == "ENERGETICO RED BULL 250ML"
            assert item_novo["gtin"] == "7891234567890"
            assert item_novo["ncm"] == "22021000"
            
        finally:
            os.unlink(xml_file_path)
    
    @pytest.mark.asyncio
    async def test_cenario_4_avarias_na_importacao(
        self, client, sample_xml_cocacola, tenant_test,
        fornecedor_solar, produtos_existentes, auth_headers
    ):
        """
        CENÁRIO 4: Registro de avarias durante importação
        
        Dado: XML com 12 unidades de Coca-Cola
        E: 3 unidades chegaram danificadas
        Então: Sistema deve registrar avaria e separar quantidade
        """
        
        # Upload e análise
        with open(sample_xml_cocacola, 'rb') as xml_file:
            response = await client.post(
                "/wms/v1/recebimentos/xml/analisar",
                headers=auth_headers,
                files={"arquivo_xml": ("nfe.xml", xml_file, "application/xml")}
            )
        
        assert response.status_code == 200
        analise = response.json()
        
        item_cocacola = next(i for i in analise["itens"] if "COCA COLA" in i["descricao"])
        
        # Confirmar com avarias
        confirmacao_request = {
            "chave_acesso": analise["chave_acesso"],
            "itens": [
                {
                    "item_id": item_cocacola["item_id"],
                    "produto_id": produtos_existentes[0].id,  # Coca-Cola
                    "quantidade_total": 12.0,
                    "quantidade_avariada": 3.0,  # 3 unidades avariadas
                    "endereco_destino": "DEP-A-01",
                    "criar_vinculo_permanente": True
                }
            ]
        }
        
        response = await client.post(
            "/wms/v1/recebimentos/xml/confirmar",
            headers={**auth_headers, "Idempotency-Key": str(uuid4())},
            json=confirmacao_request
        )
        
        assert response.status_code in [200, 201]
        confirmacao = response.json()
        
        # Verificar processamento com avarias
        item_processado = confirmacao["itens_processados"][0]
        assert item_processado["quantidade_recebida"] == 12.0  # Total entra no estoque
        assert item_processado["quantidade_avariada"] == 3.0   # 3 separadas para avaria
        
        # Verificar eventos gerados
        assert "recebimento_xml_confirmado" in confirmacao["eventos_gerados"]
        assert "avaria_registrada" in confirmacao["eventos_gerados"]
    
    @pytest.mark.asyncio
    async def test_cenario_5_idempotencia_retrabalho(
        self, client, sample_xml_cocacola, tenant_test,
        fornecedor_solar, produtos_existentes, auth_headers
    ):
        """
        CENÁRIO 5: Idempotência - retrabalho em falha de rede
        
        Dado: Primeira requisição de confirmação falha (timeout)
        E: Cliente retry com mesmo Idempotency-Key
        Então: Sistema deve retornar resultado original sem duplicar
        """
        
        idempotency_key = str(uuid4())
        
        # Upload e análise
        with open(sample_xml_cocacola, 'rb') as xml_file:
            response = await client.post(
                "/wms/v1/recebimentos/xml/analisar",
                headers=auth_headers,
                files={"arquivo_xml": ("nfe.xml", xml_file, "application/xml")}
            )
        
        assert response.status_code == 200
        analise = response.json()
        
        item_cocacola = next(i for i in analise["itens"] if "COCA COLA" in i["descricao"])
        
        confirmacao_request = {
            "chave_acesso": analise["chave_acesso"],
            "itens": [
                {
                    "item_id": item_cocacola["item_id"],
                    "produto_id": produtos_existentes[0].id,
                    "quantidade_total": 12.0,
                    "quantidade_avariada": 0.0,
                    "endereco_destino": "DEP-A-01",
                    "criar_vinculo_permanente": True
                }
            ]
        }
        
        # Primeira requisição
        response1 = await client.post(
            "/wms/v1/recebimentos/xml/confirmar",
            headers={**auth_headers, "Idempotency-Key": idempotency_key},
            json=confirmacao_request
        )
        
        assert response1.status_code == 201
        confirmacao1 = response1.json()
        recebimento_id_1 = confirmacao1["recebimento_id"]
        
        # Segunda requisição (retry)
        response2 = await client.post(
            "/wms/v1/recebimentos/xml/confirmar",
            headers={**auth_headers, "Idempotency-Key": idempotency_key},
            json=confirmacao_request
        )
        
        assert response2.status_code == 200  # 200 = idempotente
        confirmacao2 = response2.json()
        assert confirmacao2["status"] == "idempotente"
        assert confirmacao2["recebimento_id"] == recebimento_id_1
        
        # Verificar que não duplicou no banco
        # (implementar verificação específica do seu schema)
    
    def _criar_xml_produto_novo(self):
        """Cria XML com produto não cadastrado"""
        # Baseado no template mas com produto diferente
        return NFE_SAMPLE_COCACOLA.replace(
            'COCA COLA 2L PET',
            'ENERGETICO RED BULL 250ML'
        ).replace(
            '7891000316003',
            '7891234567890'
        ).replace(
            '12.0000',
            '6.0000'
        ).replace(
            '102.00',
            '35.70'
        )
