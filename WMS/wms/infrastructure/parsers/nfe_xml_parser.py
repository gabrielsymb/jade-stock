"""
Parser Seguro de XML NF-e
Extração e validação de dados de notas fiscais eletrônicas
"""

import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re
from datetime import datetime

from wms.interfaces.schemas.xml_analise import StatusItemXML


@dataclass
class ItemNFe:
    """Item extraído da NF-e"""
    codigo_fornecedor: str
    descricao: str
    quantidade: float
    unidade: Optional[str]
    ean: Optional[str]
    ncm: Optional[str]
    numero_item: int


@dataclass
class DadosNFe:
    """Dados gerais da NF-e"""
    fornecedor_cnpj: Optional[str]
    fornecedor_nome: Optional[str]
    nota_fiscal: Optional[str]
    data_emissao: Optional[datetime]
    itens: List[ItemNFe]


class NFeXMLParserError(Exception):
    """Erros específicos do parser de NF-e"""
    pass


class NFeXMLParser:
    """
    Parser seguro e robusto para XML de NF-e
    
    Valida estrutura, extrai dados e trata erros de forma segura
    """
    
    # Namespaces XML da NF-e
    NAMESPACES = {
        'nfe': 'http://www.portalfiscal.inf.br/nfe',
        'xs': 'http://www.w3.org/2001/XMLSchema'
    }
    
    def __init__(self):
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.max_items = 1000  # Limite de itens por NF-e
    
    def parse_xml(self, xml_content: str) -> DadosNFe:
        """
        Parse do conteúdo XML da NF-e
        
        Args:
            xml_content: Conteúdo XML da nota fiscal
            
        Returns:
            DadosNFe com informações extraídas
            
        Raises:
            NFeXMLParserError: Em caso de erro no parsing
        """
        try:
            # Validações básicas
            self._validate_xml_content(xml_content)
            
            # Parse do XML
            root = ET.fromstring(xml_content)
            
            # Validar estrutura da NF-e
            self._validate_nfe_structure(root)
            
            # Extrair dados gerais
            fornecedor_cnpj, fornecedor_nome = self._extract_fornecedor_data(root)
            nota_fiscal, data_emissao = self._extract_nfe_header(root)
            
            # Extrair itens
            itens = self._extract_items(root)
            
            return DadosNFe(
                fornecedor_cnpj=fornecedor_cnpj,
                fornecedor_nome=fornecedor_nome,
                nota_fiscal=nota_fiscal,
                data_emissao=data_emissao,
                itens=itens
            )
            
        except ET.ParseError as e:
            raise NFeXMLParserError(f"Erro de parsing XML: {str(e)}")
        except Exception as e:
            raise NFeXMLParserError(f"Erro inesperado no parsing: {str(e)}")
    
    def _validate_xml_content(self, xml_content: str) -> None:
        """Validações básicas do conteúdo XML"""
        if not xml_content or not xml_content.strip():
            raise NFeXMLParserError("Conteúdo XML está vazio")
        
        if len(xml_content.encode('utf-8')) > self.max_file_size:
            raise NFeXMLParserError(
                f"XML muito grande. Máximo: {self.max_file_size / 1024 / 1024:.1f}MB"
            )
        
        # Validação básica de estrutura XML
        if not xml_content.strip().startswith('<?xml'):
            raise NFeXMLParserError("XML não inicia com declaração <?xml>")
        
        if '<nfeProc' not in xml_content and '<NFe' not in xml_content:
            raise NFeXMLParserError("XML não parece ser uma NF-e válida")
    
    def _validate_nfe_structure(self, root: ET.Element):
        """Valida estrutura básica da NF-e"""
        # Verificar se é NF-e ou NFe processada
        if root.tag.endswith('nfeProc'):
            # Tenta encontrar NFe com namespace ou sem namespace
            nfe_elem = root.find('.//nfe:NFe', self.NAMESPACES)
            if nfe_elem is None:
                nfe_elem = root.find('.//NFe')
        elif root.tag.endswith('NFe'):
            nfe_elem = root
        else:
            raise NFeXMLParserError("XML não contém elemento NFe ou nfeProc")
        
        if nfe_elem is None:
            raise NFeXMLParserError("Elemento NFe não encontrado")
        
        # Verificar versão - primeiro no NFe, depois no infNFe
        versao = nfe_elem.get('versao')
        if not versao:
            # Tenta buscar em infNFe
            infnfe_elem = nfe_elem.find('.//nfe:infNFe', self.NAMESPACES)
            if infnfe_elem is None:
                infnfe_elem = nfe_elem.find('.//infNFe')
            if infnfe_elem is not None:
                versao = infnfe_elem.get('versao')
        
        if not versao:
            raise NFeXMLParserError("Versão da NF-e não informada")
        
        # Validar versões suportadas (4.00 é a mais comum)
        versoes_suportadas = ['4.00', '3.10', '3.00']
        if versao not in versoes_suportadas:
            raise NFeXMLParserError(
                f"Versão {versao} não suportada. Suportadas: {versoes_suportadas}"
            )
    
    def _extract_fornecedor_data(self, root: ET.Element) -> Tuple[Optional[str], Optional[str]]:
        """Extrai dados do fornecedor (emitente)"""
        try:
            # Buscar emitente
            emitente = root.find('.//nfe:emit', self.NAMESPACES)
            if emitente is None:
                return None, None
            
            cnpj = self._safe_get_text(emitente, 'nfe:CNPJ', self.NAMESPACES)
            nome = self._safe_get_text(emitente, 'nfe:xNome', self.NAMESPACES)
            
            # Limpar CNPJ (remover caracteres não numéricos)
            if cnpj:
                cnpj = re.sub(r'\D', '', cnpj)
            
            return cnpj, nome
            
        except Exception as e:
            # Log do erro, mas não falhar o parsing inteiro
            print(f"Aviso: Erro ao extrair dados do fornecedor: {str(e)}")
            return None, None
    
    def _extract_nfe_header(self, root: ET.Element) -> Tuple[Optional[str], Optional[datetime]]:
        """Extrai cabeçalho da NF-e (número e data)"""
        try:
            ide = root.find('.//nfe:ide', self.NAMESPACES)
            if ide is None:
                return None, None
            
            nNF = self._safe_get_text(ide, 'nfe:nNF', self.NAMESPACES)
            dhEmi = self._safe_get_text(ide, 'nfe:dhEmi', self.NAMESPACES)
            
            # Converter data
            data_emissao = None
            if dhEmi:
                try:
                    # Formato ISO 8601: 2023-12-25T10:30:00-03:00
                    data_emissao = datetime.fromisoformat(dhEmi.replace('Z', '+00:00'))
                except ValueError:
                    # Tentar formato sem timezone
                    try:
                        data_emissao = datetime.strptime(dhEmi[:19], '%Y-%m-%dT%H:%M:%S')
                    except ValueError:
                        data_emissao = None
            
            return nNF, data_emissao
            
        except Exception as e:
            print(f"Aviso: Erro ao extrair cabeçalho da NF-e: {str(e)}")
            return None, None
    
    def _extract_items(self, root: ET.Element) -> List[ItemNFe]:
        """Extrai itens da NF-e"""
        try:
            det_elements = root.findall('.//nfe:det', self.NAMESPACES)
            
            if not det_elements:
                raise NFeXMLParserError("Nenhum item encontrado na NF-e")
            
            if len(det_elements) > self.max_items:
                raise NFeXMLParserError(
                    f"Número de itens ({len(det_elements)}) excede o limite ({self.max_items})"
                )
            
            itens = []
            for i, det in enumerate(det_elements, 1):
                try:
                    item = self._extract_item_data(det, i)
                    itens.append(item)
                except Exception as e:
                    # Continuar processando outros itens
                    print(f"Aviso: Erro ao extrair item {i}: {str(e)}")
                    continue
            
            if not itens:
                raise NFeXMLParserError("Não foi possível extrair nenhum item válido")
            
            return itens
            
        except Exception as e:
            raise NFeXMLParserError(f"Erro ao extrair itens: {str(e)}")
    
    def _extract_item_data(self, det_elem: ET.Element, numero_item: int) -> ItemNFe:
        """Extrai dados de um item específico"""
        # Produto
        prod = det_elem.find('nfe:prod', self.NAMESPACES)
        if prod is None:
            raise NFeXMLParserError(f"Elemento prod não encontrado no item {numero_item}")
        
        # Código do produto (cProd)
        codigo_fornecedor = self._safe_get_text(prod, 'nfe:cProd', self.NAMESPACES)
        if not codigo_fornecedor:
            raise NFeXMLParserError(f"cProd não encontrado no item {numero_item}")
        
        # Descrição (xProd)
        descricao = self._safe_get_text(prod, 'nfe:xProd', self.NAMESPACES)
        if not descricao:
            raise NFeXMLParserError(f"xProd não encontrado no item {numero_item}")
        
        # Quantidade (qCom) e unidade (uCom)
        qcom = self._safe_get_text(prod, 'nfe:qCom', self.NAMESPACES)
        ucom = self._safe_get_text(prod, 'nfe:uCom', self.NAMESPACES)
        
        if not qcom:
            raise NFeXMLParserError(f"qCom não encontrado no item {numero_item}")
        
        try:
            quantidade = float(qcom.replace(',', '.'))
            if quantidade <= 0:
                raise ValueError("Quantidade deve ser maior que zero")
        except ValueError:
            raise NFeXMLParserError(f"qCom inválido no item {numero_item}: {qcom}")
        
        # EAN/GTIN (cEAN)
        ean = self._safe_get_text(prod, 'nfe:cEAN', self.NAMESPACES)
        if ean == 'SEM GTIN':
            ean = None
        
        # NCM
        ncm = self._safe_get_text(prod, 'nfe:NCM', self.NAMESPACES)
        
        return ItemNFe(
            codigo_fornecedor=codigo_fornecedor.strip(),
            descricao=descricao.strip(),
            quantidade=quantidade,
            unidade=ucom.strip() if ucom else None,
            ean=ean.strip() if ean else None,
            ncm=ncm.strip() if ncm else None,
            numero_item=numero_item
        )
    
    def _safe_get_text(self, parent: ET.Element, tag: str, namespaces: Dict[str, str]) -> Optional[str]:
        """Extração segura de texto de elemento XML"""
        try:
            elem = parent.find(tag, namespaces)
            if elem is not None and elem.text:
                return elem.text.strip()
            return None
        except Exception:
            return None
    
    def get_xml_summary(self, xml_content: str) -> Dict[str, Any]:
        """
        Retorna resumo do XML para validação rápida
        
        Args:
            xml_content: Conteúdo XML
            
        Returns:
            Dicionário com resumo dos dados
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Identificar tipo
            if root.tag.endswith('nfeProc'):
                tipo = "NFe Processada"
            elif root.tag.endswith('NFe'):
                tipo = "NFe"
            else:
                tipo = "Desconhecido"
            
            # Contar itens
            det_count = len(root.findall('.//nfe:det', self.NAMESPACES))
            
            # Extrair CNPJ emitente
            emitente = root.find('.//nfe:emit', self.NAMESPACES)
            cnpj = self._safe_get_text(emitente, 'nfe:CNPJ', self.NAMESPACES) if emitente else None
            
            return {
                'tipo': tipo,
                'itens_count': det_count,
                'emitente_cnpj': cnpj,
                'tamanho_bytes': len(xml_content.encode('utf-8')),
                'namespaces_found': list(root.attrib.keys()) if root.attrib else []
            }
            
        except Exception as e:
            return {
                'erro': str(e),
                'tipo': 'Erro',
                'tamanho_bytes': len(xml_content.encode('utf-8')) if xml_content else 0
            }
