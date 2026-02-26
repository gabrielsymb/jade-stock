"""
Schemas Pydantic para Endpoint de Confirmação de XML
Contratos de entrada e saída para POST /confirmar
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator, field_validator, ConfigDict


class StatusConfirmacao(str, Enum):
    """Status da confirmação de XML"""
    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    CONCLUIDO = "CONCLUIDO"
    ERRO = "ERRO"
    DUPLICADO = "DUPLICADO"


class ResultadoItemConfirmacao(BaseModel):
    """Resultado da confirmação de um item específico"""
    
    # Dados do item
    codigo_fornecedor: str = Field(..., description="Código do produto no fornecedor")
    produto_id_interno: str = Field(..., description="ID do produto interno confirmado")
    quantidade: float = Field(..., gt=0, description="Quantidade confirmada")
    unidade: str = Field(..., description="Unidade de medida")
    
    # Resultado da operação
    status: str = Field(..., description="Status da operação no item")
    mensagem: Optional[str] = Field(None, description="Mensagem detalhada")
    
    # Dados de estoque
    endereco_destino: Optional[str] = Field(None, description="Endereço onde foi armazenado")
    quantidade_armazenada: Optional[float] = Field(None, description="Quantidade efetivamente armazenada")
    saldo_anterior: Optional[float] = Field(None, description="Saldo anterior do item")
    saldo_atual: Optional[float] = Field(None, description="Saldo atualizado do item")
    
    model_config = ConfigDict(use_enum_values=True)


class XMLConfirmacaoRequest(BaseModel):
    """Request para confirmação de XML de fornecedor"""
    
    # Identificação
    chave_acesso: str = Field(..., min_length=44, max_length=44, description="Chave de acesso da NF-e (44 dígitos)")
    tenant_id: str = Field(..., description="ID do tenant")
    fornecedor_id: Optional[str] = Field(None, description="ID do fornecedor")
    
    # Metadados da análise
    processamento_id: str = Field(..., description="ID do processamento retornado pelo /analisar")
    
    # Validação opcional
    forcar_confirmacao: bool = Field(False, description="Forçar confirmação mesmo com duplicidade")
    observacoes: Optional[str] = Field(None, max_length=1000, description="Observações da confirmação")
    
    # Controle de concorrência
    idempotency_key: Optional[str] = Field(None, description="Chave de idempotência adicional")
    
    @field_validator('chave_acesso')
    @classmethod
    def validate_chave_acesso(cls, v):
        """Valida formato da chave de acesso"""
        if not v.isdigit() or len(v) != 44:
            raise ValueError("Chave de acesso deve ter exatos 44 dígitos numéricos")
        return v
    
    @field_validator('processamento_id')
    @classmethod
    def validate_processamento_id(cls, v):
        """Valida UUID do processamento"""
        if not v or len(v.strip()) == 0:
            raise ValueError("ID do processamento é obrigatório")
        return v.strip()


class XMLConfirmacaoResponse(BaseModel):
    """Response da confirmação de XML"""
    
    # Metadados da operação
    tenant_id: str = Field(..., description="ID do tenant")
    fornecedor_id: Optional[str] = Field(None, description="ID do fornecedor")
    chave_acesso: str = Field(..., description="Chave de acesso da NF-e")
    processamento_id: str = Field(..., description="ID do processamento original")
    confirmacao_id: str = Field(..., description="ID único da confirmação")
    
    # Status da confirmação
    status: StatusConfirmacao = Field(..., description="Status da confirmação")
    mensagem: Optional[str] = Field(None, description="Mensagem detalhada")
    
    # Estatísticas da operação
    total_items: int = Field(..., description="Total de itens processados")
    itens_confirmados: int = Field(..., description="Itens confirmados com sucesso")
    itens_com_erro: int = Field(..., description="Itens com erro na confirmação")
    
    # Resultados detalhados
    itens: List[ResultadoItemConfirmacao] = Field(..., description="Resultados detalhados dos itens")
    
    # Metadados de auditoria
    confirmado_por: Optional[str] = Field(None, description="Usuário que confirmou")
    confirmado_em: datetime = Field(default_factory=datetime.utcnow, description="Data/hora da confirmação")
    tempo_processamento_ms: Optional[int] = Field(None, description="Tempo de processamento em ms")
    
    # Dados da NF-e
    nota_fiscal: Optional[str] = Field(None, description="Número da nota fiscal")
    data_emissao: Optional[datetime] = Field(None, description="Data de emissão da NF-e")
    valor_total: Optional[float] = Field(None, description="Valor total da NF-e")
    
    model_config = ConfigDict(use_enum_values=True)


class ErroConfirmacaoXML(BaseModel):
    """Erros de confirmação de XML"""
    
    codigo: str = Field(..., description="Código do erro")
    mensagem: str = Field(..., description="Mensagem detalhada")
    detalhes: Optional[Dict[str, Any]] = Field(None, description="Detalhes adicionais")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do erro")


class XMLConfirmacaoErrorResponse(BaseModel):
    """Response de erro da confirmação"""
    
    erro: str = Field(..., description="Tipo de erro")
    mensagem: str = Field(..., description="Mensagem detalhada")
    chave_acesso: Optional[str] = Field(None, description="Chave de acesso que gerou o erro")
    confirmacao_id: Optional[str] = Field(None, description="ID da tentativa de confirmação")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp do erro")


# Schemas para documentação OpenAPI
class ConfirmacaoXMLSummary(BaseModel):
    """Resumo da confirmação para estatísticas"""
    
    tenant_id: str
    fornecedor_id: Optional[str]
    chave_acesso: str
    status: StatusConfirmacao
    total_items: int
    itens_confirmados: int
    itens_com_erro: int
    taxa_sucesso: float = Field(..., description="Percentual de itens confirmados")
    confirmacao_id: str
    confirmado_em: datetime


class HistoricoImportacao(BaseModel):
    """Registro histórico de importação para auditoria"""
    
    chave_acesso: str = Field(..., description="Chave de acesso da NF-e")
    tenant_id: str = Field(..., description="ID do tenant")
    fornecedor_id: Optional[str] = Field(None, description="ID do fornecedor")
    processamento_id: str = Field(..., description="ID do processamento /analisar")
    confirmacao_id: Optional[str] = Field(None, description="ID da confirmação")
    status: StatusConfirmacao = Field(..., description="Status da importação")
    data_processamento: datetime = Field(..., description="Data do processamento")
    dados_adicionais: Optional[Dict[str, Any]] = Field(None, description="Dados adicionais em JSON")
    
    model_config = ConfigDict(use_enum_values=True)
