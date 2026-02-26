"""
API de Confirmação de XML NF-e
Endpoint POST /confirmar para efetivação de entrada de estoque
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import time
from uuid import UUID

from wms.infrastructure.database import get_async_session
from wms.application.xml_confirmacao_service import XMLConfirmacaoService
from wms.interfaces.schemas.xml_confirmacao import (
    XMLConfirmacaoRequest, XMLConfirmacaoResponse, XMLConfirmacaoErrorResponse,
    ErroConfirmacaoXML, StatusConfirmacao
)

# Router do endpoint
router = APIRouter(prefix="/wms/v1/xml", tags=["XML Confirmação"])


@router.post("/confirmar",
             response_model=XMLConfirmacaoResponse,
             responses={
                 409: {"model": XMLConfirmacaoErrorResponse, "description": "NF-e já processada"},
                 422: {"model": XMLConfirmacaoErrorResponse, "description": "Erro de validação"},
                 500: {"model": XMLConfirmacaoErrorResponse, "description": "Erro interno"}
             },
             summary="Confirmar XML de NF-e",
             description="""
             Confirma a entrada de estoque baseada na análise prévia do XML.
             
             **Idempotência Absoluta:**
             - Cada NF-e (chave de acesso 44 dígitos) só pode ser processada uma vez
             - Tentativas duplicadas retornam HTTP 409 Conflict
             - Estoque só é atualizado no primeiro processamento bem-sucedido
             
             **Transação Atômica:**
             - Verificação de idempotência
             - Atualização de saldo de estoque
             - Registro no histórico
             - Emissão de evento
             
             Todos os passos são executados em uma única transação.
             """)
async def confirmar_xml(
    request: XMLConfirmacaoRequest,
    db_session: AsyncSession = Depends(get_async_session)
) -> XMLConfirmacaoResponse | JSONResponse:
    """
    Endpoint principal de confirmação de XML
    
    Processa a entrada de estoque com garantia de idempotência
    """
    try:
        # Criar service
        service = XMLConfirmacaoService(db_session)
        
        # Processar confirmação
        resultado = await service.confirmar_xml(request)
        
        # Verificar se é duplicado para retornar status correto
        status_resultado = (
            resultado.status.value
            if isinstance(resultado.status, StatusConfirmacao)
            else str(resultado.status)
        )
        if status_resultado == StatusConfirmacao.DUPLICADO.value:
            return JSONResponse(
                status_code=status.HTTP_409_CONFLICT,
                content={
                    "erro": "NF_E_JA_PROCESSADA",
                    "mensagem": "Esta nota fiscal já foi processada anteriormente",
                    "chave_acesso": request.chave_acesso,
                    "confirmacao_id": resultado.confirmacao_id,
                    "timestamp": time.time()
                }
            )
        
        return resultado
        
    except HTTPException:
        # Propagar exceções HTTP (como 409)
        raise
        
    except Exception as e:
        # Erro inesperado
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "erro": "INTERNAL_ERROR",
                "mensagem": f"Erro interno no processamento: {str(e)}",
                "chave_acesso": request.chave_acesso,
                "timestamp": time.time()
            }
        )


@router.get("/historico/{tenant_id}",
             response_model=Dict[str, Any],
             summary="Histórico de importações",
             description="Retorna histórico de importações XML por tenant")
async def historico_importacoes(
    tenant_id: str,
    limite: int = 100,
    offset: int = 0,
    status_filtro: str = None,
    db_session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Endpoint para consultar histórico de importações
    
    Args:
        tenant_id: ID do tenant
        limite: Limite de resultados (padrão: 100)
        offset: Offset para paginação (padrão: 0)
        status_filtro: Filtro por status (opcional)
    """
    try:
        from wms.infrastructure.repositories.historico_importacoes_repository import HistoricoImportacoesRepository
        from wms.interfaces.schemas.xml_confirmacao import StatusConfirmacao
        
        repo = HistoricoImportacoesRepository(db_session)
        
        # Converter status_filtro se fornecido
        status_enum = None
        if status_filtro:
            try:
                status_enum = StatusConfirmacao(status_filtro.upper())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail={
                        "erro": "INVALID_STATUS",
                        "mensagem": f"Status inválido: {status_filtro}",
                        "valores_validos": [s.value for s in StatusConfirmacao]
                    }
                )
        
        # Buscar registros
        registros = await repo.buscar_por_tenant(
            tenant_id=UUID(tenant_id),
            limite=limite,
            offset=offset,
            status_filtro=status_enum
        )
        
        # Converter para dicionário
        historico = [reg.to_dict() for reg in registros]
        
        # Obter estatísticas
        estatisticas = await repo.obter_estatisticas(tenant_id=UUID(tenant_id))
        
        return {
            "tenant_id": tenant_id,
            "historico": historico,
            "estatisticas": estatisticas,
            "paginacao": {
                "limite": limite,
                "offset": offset,
                "total": len(historico)
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "erro": "INTERNAL_ERROR",
                "mensagem": f"Erro ao consultar histórico: {str(e)}",
                "timestamp": time.time()
            }
        )


@router.get("/estatisticas/{tenant_id}",
            response_model=Dict[str, Any],
            summary="Estatísticas de importações",
            description="Retorna estatísticas detalhadas de importações XML")
async def estatisticas_importacoes(
    tenant_id: str,
    dias: int = 30,
    db_session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Endpoint para consultar estatísticas de importações
    
    Args:
        tenant_id: ID do tenant
        dias: Período em dias (padrão: 30)
    """
    try:
        from wms.infrastructure.repositories.historico_importacoes_repository import HistoricoImportacoesRepository
        
        repo = HistoricoImportacoesRepository(db_session)
        estatisticas = await repo.obter_estatisticas(tenant_id=UUID(tenant_id), dias=dias)
        
        return {
            "tenant_id": tenant_id,
            "periodo_analisado": {
                "dias": dias,
                "data_inicio": (time.time() - dias * 24 * 3600),
                "data_fim": time.time()
            },
            "estatisticas": estatisticas
        }
        
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "erro": "INTERNAL_ERROR",
                "mensagem": f"Erro ao obter estatísticas: {str(e)}",
                "timestamp": time.time()
            }
        )


@router.get("/verificar/{tenant_id}/{chave_acesso}",
            response_model=Dict[str, Any],
            summary="Verificar status da NF-e",
            description="Verifica se uma NF-e já foi processada")
async def verificar_status_nfe(
    tenant_id: str,
    chave_acesso: str,
    db_session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Endpoint para verificar status de processamento de NF-e
    
    Args:
        tenant_id: ID do tenant
        chave_acesso: Chave de acesso da NF-e (44 dígitos)
    """
    try:
        from wms.infrastructure.repositories.historico_importacoes_repository import HistoricoImportacoesRepository
        
        # Validar chave de acesso
        if len(chave_acesso) != 44 or not chave_acesso.isdigit():
            return JSONResponse(
                status_code=400,
                content={
                    "erro": "INVALID_CHAVE_ACESSO",
                    "mensagem": "Chave de acesso deve ter exatos 44 dígitos numéricos"
                }
            )
        
        repo = HistoricoImportacoesRepository(db_session)
        registro = await repo.verificar_idempotencia(
            tenant_id=UUID(tenant_id),
            chave_acesso=chave_acesso
        )
        
        if registro:
            return {
                "tenant_id": tenant_id,
                "chave_acesso": chave_acesso,
                "processado": True,
                "status": registro.status,
                "processamento_id": registro.processamento_id,
                "confirmacao_id": registro.confirmacao_id,
                "data_processamento": registro.criado_em.isoformat(),
                "mensagem": registro.mensagem
            }
        else:
            return {
                "tenant_id": tenant_id,
                "chave_acesso": chave_acesso,
                "processado": False,
                "status": None,
                "mensagem": "NF-e ainda não foi processada"
            }
        
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "erro": "INTERNAL_ERROR",
                "mensagem": f"Erro ao verificar status: {str(e)}",
                "timestamp": time.time()
            }
        )


@router.delete("/limpar-historico/{tenant_id}",
             response_model=Dict[str, Any],
             summary="Limpar histórico antigo",
             description="Remove registros antigos do histórico (manutenção)")
async def limpar_historico_antigo(
    tenant_id: str,
    dias: int = 365,
    confirmacao: bool = False,
    db_session: AsyncSession = Depends(get_async_session)
) -> Dict[str, Any]:
    """
    Endpoint para limpeza de histórico antigo
    
    ATENÇÃO: Operação destrutiva, requer confirmação explícita
    
    Args:
        tenant_id: ID do tenant
        dias: Idade mínima em dias para remoção (padrão: 365)
        confirmacao: Confirmação explícita (deve ser True)
    """
    try:
        from wms.infrastructure.repositories.historico_importacoes_repository import HistoricoImportacoesRepository
        
        if not confirmacao:
            raise HTTPException(
                status_code=400,
                detail={
                    "erro": "CONFIRMACAO_OBRIGATORIA",
                    "mensagem": "Esta operação requer confirmação explícita. Envie ?confirmacao=true"
                }
            )
        
        if dias < 30:
            raise HTTPException(
                status_code=400,
                detail={
                    "erro": "PERIODO_MINIMO",
                    "mensagem": "Período mínimo para limpeza é 30 dias"
                }
            )
        
        repo = HistoricoImportacoesRepository(db_session)
        registros_removidos = await repo.limpar_registros_antigos(
            tenant_id=UUID(tenant_id),
            dias=dias
        )
        
        return {
            "tenant_id": tenant_id,
            "operacao": "limpeza_historico",
            "periodo_removido_dias": dias,
            "registros_removidos": registros_removidos,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "erro": "INTERNAL_ERROR",
                "mensagem": f"Erro na limpeza: {str(e)}",
                "timestamp": time.time()
            }
        )


# Middleware para logging de requisições
async def log_confirmacoes(request: Request, call_next):
    """Middleware para logging de requisições de confirmação"""
    start_time = time.time()
    
    # Log básico da requisição
    if "/confirmar" in str(request.url):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] CONFIRMACAO Request: {request.method} {request.url}")
    
    # Processar requisição
    response = await call_next(request)
    
    # Log de tempo de processamento
    process_time = time.time() - start_time
    if "/confirmar" in str(request.url):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] CONFIRMACAO Response: {response.status_code} in {process_time:.3f}s")
    
    return response


# Exception handlers foram movidos para o app principal (wms/interfaces/api/app.py)
# Isso resolve o problema de APIRouter não suportar exception_handler
