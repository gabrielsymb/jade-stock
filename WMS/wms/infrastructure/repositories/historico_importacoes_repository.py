"""
Repository para Histórico de Importações
Gerencia persistência e consultas de idempotência
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc, case
from sqlalchemy.orm import selectinload

from wms.infrastructure.models.historico_importacoes import HistoricoImportacoesModel
from wms.interfaces.schemas.xml_confirmacao import StatusConfirmacao


class HistoricoImportacoesRepository:
    """
    Repository para operações com histórico de importações
    
    Foco principal: controle de idempotência e auditoria
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
    
    async def verificar_idempotencia(
        self, 
        tenant_id: UUID, 
        chave_acesso: str
    ) -> Optional[HistoricoImportacoesModel]:
        """
        Verifica se chave de acesso já foi processada
        
        Args:
            tenant_id: ID do tenant
            chave_acesso: Chave de acesso da NF-e (44 dígitos)
            
        Returns:
            Registro existente ou None
        """
        stmt = select(HistoricoImportacoesModel).where(
            and_(
                HistoricoImportacoesModel.tenant_id == tenant_id,
                HistoricoImportacoesModel.chave_acesso == chave_acesso
            )
        )
        
        result = await self.db_session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def criar_registro_pendente(
        self,
        tenant_id: UUID,
        chave_acesso: str,
        processamento_id: str,
        fornecedor_id: Optional[UUID] = None,
        nota_fiscal: Optional[str] = None,
        data_emissao: Optional[datetime] = None,
        valor_total: Optional[float] = None,
        dados_adicionais: Optional[Dict[str, Any]] = None
    ) -> HistoricoImportacoesModel:
        """
        Cria registro inicial (PENDENTE) para controle
        
        Args:
            tenant_id: ID do tenant
            chave_acesso: Chave de acesso da NF-e
            processamento_id: ID do processamento /analisar
            fornecedor_id: ID do fornecedor
            nota_fiscal: Número da nota fiscal
            data_emissao: Data de emissão
            valor_total: Valor total da NF-e
            dados_adicionais: Dados adicionais em JSON
            
        Returns:
            Registro criado
        """
        registro = HistoricoImportacoesModel(
            chave_acesso=chave_acesso,
            tenant_id=tenant_id,
            fornecedor_id=fornecedor_id,
            processamento_id=processamento_id,
            nota_fiscal=nota_fiscal,
            data_emissao=data_emissao,
            valor_total=valor_total,
            status=StatusConfirmacao.PENDENTE.value,
            dados_adicionais=dados_adicionais
        )
        
        self.db_session.add(registro)
        await self.db_session.flush()  # Garante ID gerado
        
        return registro
    
    async def atualizar_status(
        self,
        tenant_id: UUID,
        chave_acesso: str,
        status: StatusConfirmacao,
        confirmacao_id: Optional[str] = None,
        mensagem: Optional[str] = None,
        dados_adicionais: Optional[Dict[str, Any]] = None
    ) -> Optional[HistoricoImportacoesModel]:
        """
        Atualiza status de um registro existente
        
        Args:
            tenant_id: ID do tenant
            chave_acesso: Chave de acesso
            status: Novo status
            confirmacao_id: ID da confirmação
            mensagem: Mensagem de status
            dados_adicionais: Dados adicionais para merge
            
        Returns:
            Registro atualizado ou None
        """
        stmt = select(HistoricoImportacoesModel).where(
            and_(
                HistoricoImportacoesModel.tenant_id == tenant_id,
                HistoricoImportacoesModel.chave_acesso == chave_acesso
            )
        )
        
        result = await self.db_session.execute(stmt)
        registro = result.scalar_one_or_none()
        
        if registro:
            # Atualizar campos
            registro.status = status.value
            registro.atualizado_em = datetime.utcnow()
            
            if confirmacao_id:
                registro.confirmacao_id = confirmacao_id
            
            if mensagem:
                registro.mensagem = mensagem
            
            if dados_adicionais:
                # Merge com dados existentes
                if registro.dados_adicionais:
                    registro.dados_adicionais.update(dados_adicionais)
                else:
                    registro.dados_adicionais = dados_adicionais
        
        return registro
    
    async def marcar_duplicado(
        self,
        tenant_id: UUID,
        chave_acesso: str,
        confirmacao_id: str,
        dados_adicionais: Optional[Dict[str, Any]] = None
    ) -> Optional[HistoricoImportacoesModel]:
        """
        Marca registro como duplicado
        
        Args:
            tenant_id: ID do tenant
            chave_acesso: Chave de acesso
            confirmacao_id: ID da tentativa de confirmação
            dados_adicionais: Dados adicionais
            
        Returns:
            Registro atualizado
        """
        return await self.atualizar_status(
            tenant_id=tenant_id,
            chave_acesso=chave_acesso,
            status=StatusConfirmacao.DUPLICADO,
            confirmacao_id=confirmacao_id,
            mensagem="Esta nota fiscal já foi processada anteriormente",
            dados_adicionais=dados_adicionais
        )
    
    async def marcar_erro(
        self,
        tenant_id: UUID,
        chave_acesso: str,
        mensagem_erro: str,
        dados_adicionais: Optional[Dict[str, Any]] = None
    ) -> Optional[HistoricoImportacoesModel]:
        """
        Marca registro como erro
        
        Args:
            tenant_id: ID do tenant
            chave_acesso: Chave de acesso
            mensagem_erro: Mensagem de erro
            dados_adicionais: Dados adicionais
            
        Returns:
            Registro atualizado
        """
        return await self.atualizar_status(
            tenant_id=tenant_id,
            chave_acesso=chave_acesso,
            status=StatusConfirmacao.ERRO,
            mensagem=mensagem_erro,
            dados_adicionais=dados_adicionais
        )
    
    async def concluir_processamento(
        self,
        tenant_id: UUID,
        chave_acesso: str,
        confirmacao_id: str,
        dados_adicionais: Optional[Dict[str, Any]] = None
    ) -> Optional[HistoricoImportacoesModel]:
        """
        Marca processamento como concluído
        
        Args:
            tenant_id: ID do tenant
            chave_acesso: Chave de acesso
            confirmacao_id: ID da confirmação
            dados_adicionais: Dados adicionais
            
        Returns:
            Registro atualizado
        """
        return await self.atualizar_status(
            tenant_id=tenant_id,
            chave_acesso=chave_acesso,
            status=StatusConfirmacao.CONCLUIDO,
            confirmacao_id=confirmacao_id,
            mensagem="Processamento concluído com sucesso",
            dados_adicionais=dados_adicionais
        )
    
    async def buscar_por_tenant(
        self,
        tenant_id: UUID,
        limite: int = 100,
        offset: int = 0,
        status_filtro: Optional[StatusConfirmacao] = None
    ) -> List[HistoricoImportacoesModel]:
        """
        Busca importações por tenant
        
        Args:
            tenant_id: ID do tenant
            limite: Limite de resultados
            offset: Offset para paginação
            status_filtro: Filtro por status
            
        Returns:
            Lista de registros
        """
        conditions = [HistoricoImportacoesModel.tenant_id == tenant_id]
        
        if status_filtro:
            conditions.append(HistoricoImportacoesModel.status == status_filtro.value)
        
        stmt = select(HistoricoImportacoesModel).where(
            and_(*conditions)
        ).order_by(
            desc(HistoricoImportacoesModel.criado_em)
        ).limit(limite).offset(offset)
        
        result = await self.db_session.execute(stmt)
        return result.scalars().all()
    
    async def buscar_por_fornecedor(
        self,
        tenant_id: UUID,
        fornecedor_id: UUID,
        dias: int = 30
    ) -> List[HistoricoImportacoesModel]:
        """
        Busca importações por fornecedor
        
        Args:
            tenant_id: ID do tenant
            fornecedor_id: ID do fornecedor
            dias: Período em dias
            
        Returns:
            Lista de registros
        """
        data_limite = datetime.utcnow() - timedelta(days=dias)
        
        stmt = select(HistoricoImportacoesModel).where(
            and_(
                HistoricoImportacoesModel.tenant_id == tenant_id,
                HistoricoImportacoesModel.fornecedor_id == fornecedor_id,
                HistoricoImportacoesModel.criado_em >= data_limite
            )
        ).order_by(
            desc(HistoricoImportacoesModel.criado_em)
        )
        
        result = await self.db_session.execute(stmt)
        return result.scalars().all()
    
    async def obter_estatisticas(
        self,
        tenant_id: UUID,
        dias: int = 30
    ) -> Dict[str, Any]:
        """
        Obtém estatísticas de importações
        
        Args:
            tenant_id: ID do tenant
            dias: Período em dias
            
        Returns:
            Dicionário com estatísticas
        """
        data_limite = datetime.utcnow() - timedelta(days=dias)
        
        # Query de agregação
        stmt = select(
            func.count(HistoricoImportacoesModel.id).label('total'),
            func.sum(
                case(
                    (HistoricoImportacoesModel.status == StatusConfirmacao.CONCLUIDO.value, 1),
                    else_=0,
                )
            ).label('concluidos'),
            func.sum(
                case(
                    (HistoricoImportacoesModel.status == StatusConfirmacao.ERRO.value, 1),
                    else_=0,
                )
            ).label('erros'),
            func.sum(
                case(
                    (HistoricoImportacoesModel.status == StatusConfirmacao.DUPLICADO.value, 1),
                    else_=0,
                )
            ).label('duplicados'),
            func.coalesce(
                func.sum(HistoricoImportacoesModel.valor_total), 0
            ).label('valor_total')
        ).where(
            and_(
                HistoricoImportacoesModel.tenant_id == tenant_id,
                HistoricoImportacoesModel.criado_em >= data_limite
            )
        )
        
        result = await self.db_session.execute(stmt)
        row = result.first()
        
        total = row.total or 0
        concluidos = row.concluidos or 0
        erros = row.erros or 0
        duplicados = row.duplicados or 0
        valor_total = float(row.valor_total or 0)
        
        return {
            'total_importacoes': total,
            'importacoes_concluidas': concluidos,
            'importacoes_com_erro': erros,
            'importacoes_duplicadas': duplicados,
            'taxa_sucesso': round((concluidos / total * 100), 2) if total > 0 else 0,
            'valor_total_importado': valor_total,
            'periodo_dias': dias
        }
    
    async def buscar_importacoes_recentes(
        self,
        tenant_id: UUID,
        horas: int = 24
    ) -> List[HistoricoImportacoesModel]:
        """
        Busca importações recentes
        
        Args:
            tenant_id: ID do tenant
            horas: Período em horas
            
        Returns:
            Lista de registros recentes
        """
        data_limite = datetime.utcnow() - timedelta(hours=horas)
        
        stmt = select(HistoricoImportacoesModel).where(
            and_(
                HistoricoImportacoesModel.tenant_id == tenant_id,
                HistoricoImportacoesModel.criado_em >= data_limite
            )
        ).order_by(
            desc(HistoricoImportacoesModel.criado_em)
        )
        
        result = await self.db_session.execute(stmt)
        return result.scalars().all()
    
    async def limpar_registros_antigos(
        self,
        tenant_id: UUID,
        dias: int = 365
    ) -> int:
        """
        Limpa registros antigos (manutenção)
        
        Args:
            tenant_id: ID do tenant
            dias: Idade mínima em dias para remoção
            
        Returns:
            Número de registros removidos
        """
        data_limite = datetime.utcnow() - timedelta(days=dias)
        
        # Apenas remover registros CONCLUIDO ou ERRO muito antigos
        stmt = select(HistoricoImportacoesModel).where(
            and_(
                HistoricoImportacoesModel.tenant_id == tenant_id,
                HistoricoImportacoesModel.criado_em < data_limite,
                HistoricoImportacoesModel.status.in_([
                    StatusConfirmacao.CONCLUIDO.value,
                    StatusConfirmacao.ERRO.value
                ])
            )
        )
        
        result = await self.db_session.execute(stmt)
        registros = result.scalars().all()
        
        # Remover
        for registro in registros:
            await self.db_session.delete(registro)
        
        return len(registros)
