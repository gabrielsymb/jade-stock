"""
Service de Análise de XML
Orquestra parsing, consulta de vínculos e classificação de itens
"""

import time
import uuid
from typing import List, Dict, Optional, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func

from wms.infrastructure.parsers.nfe_xml_parser import NFeXMLParser, DadosNFe, ItemNFe, NFeXMLParserError
from wms.infrastructure.repositories.vinculo_fornecedor_produto_repository import VinculoFornecedorProdutoRepository
from wms.infrastructure.models.core.sku import SKUModel
from wms.infrastructure.models.core.item_master import ItemMasterModel
from wms.interfaces.schemas.xml_analise import (
    XMLAnaliseRequest, XMLAnaliseResponse, ItemXMLAnalise, 
    StatusItemXML, ErroValidacaoXML
)


class ItemAnaliseResult:
    """Resultado da análise de um item"""
    
    def __init__(self, item: ItemNFe):
        self.item = item
        self.status = StatusItemXML.NEW
        self.produto_id_interno = None
        self.produto_nome = None
        self.fator_conversao = None
        self.unidade_origem = None
        self.unidade_destino = None
        self.peso_confianca = None
        self.mensagem = None
        self.sugestoes = []
        self.vinculos_encontrados = []


class XMLAnaliseService:
    """
    Service para análise de XML de fornecedor
    
    Processa XML, consulta vínculos e classifica status dos itens
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.parser = NFeXMLParser()
        self.vinculo_repository = VinculoFornecedorProdutoRepository(db_session)
    
    async def analisar_xml(self, request: XMLAnaliseRequest) -> XMLAnaliseResponse:
        """
        Analisa XML de fornecedor e classifica status dos itens
        
        Args:
            request: Request com XML e metadados
            
        Returns:
            XMLAnaliseResponse com resultados da análise
        """
        inicio_processamento = time.time()
        processamento_id = str(uuid.uuid4())
        
        try:
            # 1. Parse do XML
            dados_nfe = self.parser.parse_xml(request.xml_content)
            
            # 2. Identificar fornecedor (do XML ou request)
            fornecedor_id = request.fornecedor_id
            
            # 3. Analisar cada item
            itens_analisados = []
            matched_count = 0
            ambiguous_count = 0
            new_count = 0
            
            for item_nfe in dados_nfe.itens:
                resultado = await self._analisar_item(
                    item=item_nfe,
                    tenant_id=request.tenant_id,
                    fornecedor_id=fornecedor_id
                )
                
                # Contabilizar estatísticas
                if resultado.status == StatusItemXML.MATCHED:
                    matched_count += 1
                elif resultado.status == StatusItemXML.AMBIGUOUS:
                    ambiguous_count += 1
                else:
                    new_count += 1
                
                # Criar ItemXMLAnalise
                item_analise = ItemXMLAnalise(
                    codigo_fornecedor=resultado.item.codigo_fornecedor,
                    descricao=resultado.item.descricao,
                    quantidade=resultado.item.quantidade,
                    unidade=resultado.item.unidade,
                    ean=resultado.item.ean,
                    ncm=resultado.item.ncm,
                    status=resultado.status,
                    produto_id_interno=resultado.produto_id_interno,
                    produto_nome=resultado.produto_nome,
                    fator_conversao=resultado.fator_conversao,
                    unidade_origem=resultado.unidade_origem,
                    unidade_destino=resultado.unidade_destino,
                    peso_confianca=resultado.peso_confianca,
                    mensagem=resultado.mensagem,
                    sugestoes=resultado.sugestoes
                )
                
                itens_analisados.append(item_analise)
            
            # 4. Montar response
            tempo_processamento = int((time.time() - inicio_processamento) * 1000)
            
            return XMLAnaliseResponse(
                tenant_id=request.tenant_id,
                fornecedor_id=fornecedor_id,
                fornecedor_nome=dados_nfe.fornecedor_nome,
                nota_fiscal=dados_nfe.nota_fiscal,
                data_emissao=dados_nfe.data_emissao,
                total_items=len(itens_analisados),
                matched_items=matched_count,
                ambiguous_items=ambiguous_count,
                new_items=new_count,
                itens=itens_analisados,
                processamento_id=processamento_id,
                processado_em=datetime.utcnow(),
                tempo_processamento_ms=tempo_processamento
            )
            
        except NFeXMLParserError as e:
            raise e
            
        except Exception as e:
            raise Exception(f"Erro na análise do XML: {str(e)}")
    
    async def _analisar_item(
        self, 
        item: ItemNFe, 
        tenant_id: str, 
        fornecedor_id: Optional[str]
    ) -> ItemAnaliseResult:
        """
        Analisa um item específico consultando vínculos
        
        Args:
            item: Item da NF-e
            tenant_id: ID do tenant
            fornecedor_id: ID do fornecedor
            
        Returns:
            ItemAnaliseResult com status e detalhes
        """
        resultado = ItemAnaliseResult(item)
        
        if not fornecedor_id:
            resultado.status = StatusItemXML.NEW
            resultado.mensagem = "Fornecedor não identificado"
            return resultado
        
        try:
            # 1. Buscar por código exato do fornecedor
            vinculos_codigo = await self.vinculo_repository.list_by_fornecedor(
                tenant_id=tenant_id,
                fornecedor_id=fornecedor_id
            )
            
            # Filtrar por código exato
            vinculos_exatos = [
                v for v in vinculos_codigo 
                if v.codigo_fornecedor == item.codigo_fornecedor
            ]
            
            if len(vinculos_exatos) == 1:
                # MATCHED: Vínculo único encontrado
                vinculo = vinculos_exatos[0]
                resultado.status = StatusItemXML.MATCHED
                resultado.produto_id_interno = str(vinculo.produto_id_interno)
                resultado.fator_conversao = float(vinculo.fator_conversao)
                resultado.unidade_origem = vinculo.unidade_origem.value if vinculo.unidade_origem else None
                resultado.unidade_destino = vinculo.unidade_destino.value if vinculo.unidade_destino else None
                resultado.peso_confianca = float(vinculo.peso_confianca)
                resultado.vinculos_encontrados = [vinculo]
                
                # Buscar nome do produto
                await self._preencher_dados_produto(resultado)
                
            elif len(vinculos_exatos) > 1:
                # AMBIGUOUS: Múltiplos vínculos para mesmo código
                resultado.status = StatusItemXML.AMBIGUOUS
                resultado.vinculos_encontrados = vinculos_exatos
                resultado.mensagem = f"Múltiplos vínculos encontrados para código {item.codigo_fornecedor}"
                
                # Criar sugestões
                resultado.sugestoes = [
                    f"Produto {i+1}: {v.produto_id_interno} (confiança: {v.peso_confianca})"
                    for i, v in enumerate(vinculos_exatos[:3])
                ]
                
            else:
                # 2. Buscar por EAN se disponível
                if item.ean and len(item.ean) >= 8:
                    await self._buscar_por_ean(resultado, tenant_id, item.ean)
                
                # 3. Se ainda não encontrou, buscar por NCM
                if resultado.status == StatusItemXML.NEW and item.ncm:
                    await self._buscar_por_ncm(resultado, tenant_id, item.ncm)
                
                # 4. Se ainda não encontrou, buscar por similaridade de descrição
                if resultado.status == StatusItemXML.NEW:
                    await self._buscar_por_similaridade(resultado, tenant_id, item.descricao)
            
            return resultado
            
        except Exception as e:
            # Erro na análise, mas continuar com NEW
            resultado.status = StatusItemXML.NEW
            resultado.mensagem = f"Erro na análise: {str(e)}"
            return resultado
    
    async def _buscar_por_ean(self, resultado: ItemAnaliseResult, tenant_id: str, ean: str) -> None:
        """Busca vínculos por EAN/GTIN"""
        try:
            # Buscar SKUs pelo EAN
            stmt = select(SKUModel).where(
                and_(
                    SKUModel.ean == ean,
                    SKUModel.status_ativo == True
                )
            )
            sku_result = await self.db_session.execute(stmt)
            skus = sku_result.scalars().all()
            
            if len(skus) == 1:
                sku = skus[0]
                resultado.status = StatusItemXML.MATCHED
                resultado.produto_id_interno = sku.sku_id
                resultado.produto_nome = sku.sku_nome
                resultado.mensagem = f"Match por EAN: {ean}"
                
        except Exception as e:
            print(f"Aviso: Erro ao buscar por EAN {ean}: {str(e)}")
    
    async def _buscar_por_ncm(self, resultado: ItemAnaliseResult, tenant_id: str, ncm: str) -> None:
        """Busca produtos por NCM"""
        try:
            # TODO: Implementar busca por NCM quando o campo for adicionado ao modelo
            # Por enquanto, retorna sem fazer match por NCM
            print(f"Aviso: Busca por NCM {ncm} desabilitada - campo ncm não encontrado nos modelos")
            return
            
            # Buscar produtos pelo NCM (via item_master) - DESABILITADO
            # stmt = select(SKUModel).join(ItemMasterModel).where(
            #     and_(
            #         ItemMasterModel.ncm == ncm,
            #         SKUModel.status_ativo == True
            #     )
            # )
            # sku_result = await self.db_session.execute(stmt)
            # skus = sku_result.scalars().all()
            
            if len(skus) == 1:
                sku = skus[0]
                resultado.status = StatusItemXML.MATCHED
                resultado.produto_id_interno = sku.sku_id
                resultado.produto_nome = sku.sku_nome
                resultado.mensagem = f"Match por NCM: {ncm}"
                
        except Exception as e:
            print(f"Aviso: Erro ao buscar por NCM {ncm}: {str(e)}")
    
    async def _buscar_por_similaridade(self, resultado: ItemAnaliseResult, tenant_id: str, descricao: str) -> None:
        """Busca por similaridade de descrição"""
        try:
            # Buscar por palavras-chave na descrição
            palavras_chave = descricao.split()[:3]  # Primeiras 3 palavras
            
            for palavra in palavras_chave:
                if len(palavra) < 3:
                    continue
                
                stmt = select(SKUModel).where(
                    and_(
                        SKUModel.sku_nome.ilike(f"%{palavra}%"),
                        SKUModel.status_ativo == True
                    )
                ).limit(5)
                
                sku_result = await self.db_session.execute(stmt)
                skus = sku_result.scalars().all()
                
                if skus:
                    resultado.sugestoes.extend([
                        f"Similaridade '{palavra}': {sku.sku_nome} ({sku.sku_id})"
                        for sku in skus[:2]
                    ])
                    
        except Exception as e:
            print(f"Aviso: Erro ao buscar por similaridade: {str(e)}")
    
    async def _preencher_dados_produto(self, resultado: ItemAnaliseResult) -> None:
        """Preenche dados do produto a partir do ID"""
        try:
            stmt = select(SKUModel).where(SKUModel.sku_id == resultado.produto_id_interno)
            sku_result = await self.db_session.execute(stmt)
            sku = sku_result.scalar_one_or_none()
            
            if sku:
                resultado.produto_nome = sku.sku_nome
                
        except Exception as e:
            print(f"Aviso: Erro ao preencher dados do produto: {str(e)}")
    
    async def validar_xml_basico(self, xml_content: str) -> List[ErroValidacaoXML]:
        """
        Validação básica do XML antes do parsing completo
        
        Args:
            xml_content: Conteúdo XML
            
        Returns:
            Lista de erros encontrados
        """
        erros = []
        
        try:
            # Validação de tamanho
            if len(xml_content.encode('utf-8')) > 10 * 1024 * 1024:
                erros.append(ErroValidacaoXML(
                    codigo="XML_TOO_LARGE",
                    mensagem="XML excede tamanho máximo de 10MB",
                    contexto=f"Tamanho: {len(xml_content)} bytes"
                ))
            
            # Validação de estrutura básica
            if not xml_content.strip().startswith('<?xml'):
                erros.append(ErroValidacaoXML(
                    codigo="INVALID_XML_DECLARATION",
                    mensagem="XML deve iniciar com declaração <?xml>",
                    contexto="Primeira linha"
                ))
            
            # Tentar parsing básico
            try:
                ET.fromstring(xml_content)
            except ET.ParseError as e:
                erros.append(ErroValidacaoXML(
                    codigo="XML_PARSE_ERROR",
                    mensagem=f"Erro de parsing: {str(e)}",
                    contexto=str(e)
                ))
                
        except Exception as e:
            erros.append(ErroValidacaoXML(
                codigo="VALIDATION_ERROR",
                mensagem=f"Erro na validação: {str(e)}",
                contexto="Validação básica"
            ))
        
        return erros
