"""
Schemas Pydantic para Endpoint de Análise de XML
Contratos de entrada e saída para POST /analisar
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, field_validator, ConfigDict


class StatusItemXML(str, Enum):
    """Status de análise de item do XML"""
    MATCHED = "MATCHED"
    AMBIGUOUS = "AMBIGUOUS"
    NEW = "NEW"


class ItemXMLAnalise(BaseModel):
    """Resultado da análise de um item do XML"""
    
    # Dados do XML
    codigo_fornecedor: str = Field(..., description="Código do produto no fornecedor")
    descricao: str = Field(..., description="Descrição do produto no XML")
    quantidade: float = Field(..., gt=0, description="Quantidade informada")
    unidade: Optional[str] = Field(None, description="Unidade de medida")
    ean: Optional[str] = Field(None, description="Código EAN/GTIN se informado")
    ncm: Optional[str] = Field(None, description="Código NCM se informado")
    
    # Resultado da análise
    status: StatusItemXML = Field(..., description="Status da análise")
    produto_id_interno: Optional[str] = Field(None, description="ID do produto interno se encontrado")
    produto_nome: Optional[str] = Field(None, description="Nome do produto interno se encontrado")
    fator_conversao: Optional[float] = Field(None, description="Fator de conversão se aplicável")
    unidade_origem: Optional[str] = Field(None, description="Unidade de origem")
    unidade_destino: Optional[str] = Field(None, description="Unidade de destino")
    peso_confianca: Optional[float] = Field(None, description="Peso de confiança do vínculo")
    
    # Metadados
    mensagem: Optional[str] = Field(None, description="Mensagem adicional")
    sugestoes: List[str] = Field(default_factory=list, description="Sugestões para ambiguidades")
    
    model_config = ConfigDict(use_enum_values=True)


class XMLAnaliseRequest(BaseModel):
    """Request para análise de XML de fornecedor"""
    
    xml_content: str = Field(..., description="Conteúdo XML da NF-e")
    tenant_id: str = Field(..., description="ID do tenant")
    fornecedor_id: Optional[str] = Field(None, description="ID do fornecedor (extraível do XML)")
    idempotency_key: Optional[str] = Field(None, description="Chave de idempotência")
    
    @field_validator('xml_content')
    @classmethod
    def validate_xml_content(cls, v):
        """Validação básica do conteúdo XML"""
        if not v.strip():
            raise ValueError("Conteúdo XML não pode estar vazio")
        if len(v) > 10 * 1024 * 1024:  # 10MB
            raise ValueError("Conteúdo XML muito grande (máximo 10MB)")
        return v.strip()


class XMLAnaliseResponse(BaseModel):
    """Response da análise de XML"""
    
    # Metadados da análise
    tenant_id: str = Field(..., description="ID do tenant")
    fornecedor_id: Optional[str] = Field(None, description="ID do fornecedor identificado")
    fornecedor_nome: Optional[str] = Field(None, description="Nome do fornecedor")
    nota_fiscal: Optional[str] = Field(None, description="Número da nota fiscal")
    data_emissao: Optional[datetime] = Field(None, description="Data de emissão da NF-e")
    
    # Estatísticas da análise
    total_items: int = Field(..., description="Total de itens analisados")
    matched_items: int = Field(..., description="Itens com vínculo encontrado")
    ambiguous_items: int = Field(..., description="Itens com múltiplos vínculos")
    new_items: int = Field(..., description="Itens sem vínculo")
    
    # Resultados detalhados
    itens: List[ItemXMLAnalise] = Field(..., description="Análise detalhada dos itens")
    
    # Metadados de processamento
    processamento_id: str = Field(..., description="ID único do processamento")
    processado_em: datetime = Field(default_factory=datetime.utcnow, description="Data/hora do processamento")
    tempo_processamento_ms: Optional[int] = Field(None, description="Tempo de processamento em ms")
    
    model_config = ConfigDict(use_enum_values=True)


class ErroValidacaoXML(BaseModel):
    """Erros de validação do XML"""
    
    codigo: str = Field(..., description="Código do erro")
    mensagem: str = Field(..., description="Mensagem detalhada")
    linha: Optional[int] = Field(None, description="Linha do erro")
    coluna: Optional[int] = Field(None, description="Coluna do erro")
    contexto: Optional[str] = Field(None, description="Contexto do erro")


class XMLAnaliseErrorResponse(BaseModel):
    """Response de erro da análise"""
    
    erro: str = Field(..., description="Tipo de erro")
    mensagem: str = Field(..., description="Mensagem detalhada")
    detalhes: Optional[List[ErroValidacaoXML]] = Field(None, description="Detalhes dos erros")
    processamento_id: Optional[str] = Field(None, description="ID do processamento")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do erro")


# Schemas para documentação OpenAPI
class AnaliseXMLSummary(BaseModel):
    """Resumo da análise para estatísticas"""
    
    tenant_id: str
    fornecedor_id: Optional[str]
    total_items: int
    matched_items: int
    ambiguous_items: int
    new_items: int
    taxa_match: float = Field(..., description="Percentual de itens matched")
    processamento_id: str
    processado_em: datetime
