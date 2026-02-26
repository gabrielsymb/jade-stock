"""
API de Análise de XML NF-e
Endpoint POST /analisar para processamento de notas fiscais
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import time

from wms.infrastructure.database import get_async_session
from wms.application.xml_analise_service import XMLAnaliseService
from wms.infrastructure.parsers.nfe_xml_parser import NFeXMLParserError
from wms.interfaces.schemas.xml_analise import (
    XMLAnaliseRequest, XMLAnaliseResponse, XMLAnaliseErrorResponse,
    ErroValidacaoXML
)

# Router do endpoint
router = APIRouter(prefix="/wms/v1/xml", tags=["XML Análise"])


@router.post("/analisar", 
             response_model=XMLAnaliseResponse,
             responses={
                 400: {"model": XMLAnaliseErrorResponse, "description": "Erro de validação"},
                 422: {"model": XMLAnaliseErrorResponse, "description": "Erro de parsing"},
                 500: {"model": XMLAnaliseErrorResponse, "description": "Erro interno"}
             },
             summary="Analisar XML de NF-e",
             description="""
             Analisa um XML de nota fiscal eletrônica e classifica o status de cada item
             com base na tabela de vínculos fornecedor-produto.
             
             **Status possíveis:**
             - **MATCHED**: Vínculo único encontrado
             - **AMBIGUOUS**: Múltiplos vínculos encontrados
             - **NEW**: Nenhum vínculo encontrado
             
             **Nenhuma atualização de estoque é realizada neste endpoint.**
             """)
async def analisar_xml(
    request: XMLAnaliseRequest,
    db_session: AsyncSession = Depends(get_async_session)
) -> XMLAnaliseResponse | JSONResponse:
    """
    Endpoint principal de análise de XML
    
    Processa o XML, consulta vínculos e retorna classificação dos itens
    """
    try:
        # Validar estrutura básica do XML primeiro
        from wms.infrastructure.parsers.nfe_xml_parser import NFeXMLParser
        
        parser = NFeXMLParser()
        resumo = parser.get_xml_summary(request.xml_content)
        
        if "erro" in resumo:
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                content={
                    "erro": "XML_INVALIDO",
                    "mensagem": f"XML inválido: {resumo['erro']}",
                    "timestamp": time.time()
                }
            )
        
        # Criar service
        service = XMLAnaliseService(db_session)
        
        # Validar idempotência se fornecida
        if request.idempotency_key:
            # TODO: Implementar verificação de idempotência
            pass
        
        # Processar análise
        resultado = await service.analisar_xml(request)
        
        return resultado
        
    except HTTPException:
        raise
    except NFeXMLParserError as e:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "erro": "XML_INVALIDO",
                "mensagem": str(e),
                "timestamp": time.time(),
            },
        )
    except Exception as e:
        # Erro inesperado
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "erro": "INTERNAL_ERROR",
                "mensagem": f"Erro interno no processamento: {str(e)}",
                "timestamp": time.time()
            }
        )


@router.post("/validar",
             response_model=Dict[str, Any],
             summary="Validar estrutura XML",
             description="Valida estrutura básica do XML sem processar completamente")
async def validar_xml(
    request: XMLAnaliseRequest,
    db_session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Endpoint de validação rápida de XML
    
    Retorna informações básicas sobre o XML sem processamento completo
    """
    try:
        from wms.infrastructure.parsers.nfe_xml_parser import NFeXMLParser
        
        parser = NFeXMLParser()
        resumo = parser.get_xml_summary(request.xml_content)
        
        return {
            "valido": "erro" not in resumo,
            "resumo": resumo,
            "tenant_id": request.tenant_id,
            "fornecedor_id": request.fornecedor_id
        }
        
    except Exception as e:
        return {
            "valido": False,
            "erro": str(e),
            "tenant_id": request.tenant_id,
            "fornecedor_id": request.fornecedor_id
        }


@router.get("/status/{processamento_id}",
            response_model=Dict[str, Any],
            summary="Status do processamento",
            description="Retorna status de um processamento anterior")
async def status_processamento(
    processamento_id: str,
    db_session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Endpoint para consultar status de processamento
    
    TODO: Implementar cache/redis para tracking de processamentos
    """
    return {
        "processamento_id": processamento_id,
        "status": "completed",
        "mensagem": "Processamento concluído com sucesso"
    }


@router.get("/health",
            response_model=Dict[str, str],
            summary="Health check",
            description="Verifica saúde do serviço de análise")
async def health_check() -> Dict[str, str]:
    """Health check do serviço"""
    return {
        "status": "healthy",
        "service": "xml_analise",
        "timestamp": str(int(time.time()))
    }


# Middleware para logging de requisições
async def log_requests(request: Request, call_next):
    """Middleware para logging de requisições XML"""
    start_time = time.time()
    
    # Log básico da requisição
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] XML Request: {request.method} {request.url}")
    
    # Processar requisição
    response = await call_next(request)
    
    # Log de tempo de processamento
    process_time = time.time() - start_time
    print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] XML Response: {response.status_code} in {process_time:.3f}s")
    
    return response


# Handlers de erro personalizados (implementados na app FastAPI principal)
# @router.exception_handler(ValueError) - APIRouter não possui exception_handler
