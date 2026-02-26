"""
Service de Confirmação de XML
Orquestra atualização de estoque com idempotência garantida
"""

import time
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text
from sqlalchemy.exc import IntegrityError

from wms.infrastructure.repositories.historico_importacoes_repository import HistoricoImportacoesRepository
from wms.infrastructure.repositories.vinculo_fornecedor_produto_repository import VinculoFornecedorProdutoRepository
from wms.infrastructure.repositories.saldo_estoque_repository import SaldoEstoqueRepository
from wms.infrastructure.repositories.movimentacao_estoque_repository import MovimentacaoEstoqueRepository
from wms.infrastructure.models.historico_importacoes import HistoricoImportacoesModel
from wms.infrastructure.models.core.sku import SKUModel
from wms.infrastructure.models.core.endereco import EnderecoModel
from wms.infrastructure.parsers.nfe_xml_parser import NFeXMLParser, DadosNFe, ItemNFe
from wms.domain.movimentacao_estoque import TipoMovimentacao
from wms.interfaces.schemas.xml_confirmacao import (
    XMLConfirmacaoRequest, XMLConfirmacaoResponse, 
    ResultadoItemConfirmacao, StatusConfirmacao, ErroConfirmacaoXML
)
from wms.interfaces.schemas.xml_analise import ItemXMLAnalise, StatusItemXML


class XMLConfirmacaoService:
    """
    Service para confirmação de XML com idempotência
    
    Garante que cada NF-e seja processada apenas uma vez,
    mesmo com reenvios ou cliques duplos
    """
    
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session
        self.historico_repo = HistoricoImportacoesRepository(db_session)
        self.vinculo_repo = VinculoFornecedorProdutoRepository(db_session)
        self.saldo_repo = SaldoEstoqueRepository(db_session)
        self.movimentacao_repo = MovimentacaoEstoqueRepository(db_session)
        self.parser = NFeXMLParser()
    
    async def confirmar_xml(self, request: XMLConfirmacaoRequest) -> XMLConfirmacaoResponse:
        """
        Confirma XML de NF-e atualizando estoque
        
        Args:
            request: Request com chave de acesso e metadados
            
        Returns:
            XMLConfirmacaoResponse com resultados
            
        Raises:
            Exception: Em caso de erro no processamento
        """
        inicio_processamento = time.time()
        confirmacao_id = str(uuid.uuid4())

        # Garante commit/rollback quando o caller não abriu transação explicitamente.
        if not self.db_session.in_transaction():
            async with self.db_session.begin():
                return await self.confirmar_xml(request)
        
        try:
            await self._adquirir_lock_idempotencia(request.tenant_id, request.chave_acesso)

            # 1. VERIFICAÇÃO DE IDEMPOTÊNCIA
            registro_existente = await self.historico_repo.verificar_idempotencia(
                tenant_id=UUID(request.tenant_id),
                chave_acesso=request.chave_acesso
            )
            
            if registro_existente:
                # NF-e já processada - retornar erro 409
                return XMLConfirmacaoResponse(
                    tenant_id=request.tenant_id,
                    fornecedor_id=request.fornecedor_id,
                    chave_acesso=request.chave_acesso,
                    processamento_id=request.processamento_id,
                    confirmacao_id=confirmacao_id,
                    status=StatusConfirmacao.DUPLICADO,
                    mensagem="Esta nota fiscal já foi processada anteriormente",
                    total_items=0,
                    itens_confirmados=0,
                    itens_com_erro=0,
                    itens=[],
                    confirmado_em=datetime.utcnow(),
                    tempo_processamento_ms=int((time.time() - inicio_processamento) * 1000)
                )
            
            dados_analise: Optional[Dict[str, Any]] = None
            resultados_itens: List[ResultadoItemConfirmacao] = []

            async def _processar_confirmacao_transacional() -> None:
                nonlocal dados_analise, resultados_itens
                # 2.1 Criar registro PENDENTE
                await self.historico_repo.criar_registro_pendente(
                    tenant_id=UUID(request.tenant_id),
                    chave_acesso=request.chave_acesso,
                    processamento_id=request.processamento_id,
                    fornecedor_id=UUID(request.fornecedor_id) if request.fornecedor_id else None
                )

                # 2.2 Obter dados da análise anterior
                dados_analise = await self._obter_dados_analise(request.processamento_id)
                if not dados_analise:
                    raise Exception("Análise XML não encontrada. Execute /analisar primeiro.")

                # 2.3 Processar itens e atualizar estoque
                resultados_itens = await self._processar_itens(
                    itens_analisados=dados_analise['itens'],
                    tenant_id=request.tenant_id,
                    fornecedor_id=request.fornecedor_id,
                    confirmacao_id=confirmacao_id
                )

                # 2.4 Atualizar status para CONCLUIDO
                await self.historico_repo.concluir_processamento(
                    tenant_id=UUID(request.tenant_id),
                    chave_acesso=request.chave_acesso,
                    confirmacao_id=confirmacao_id,
                    dados_adicionais={
                        'tempo_processamento_ms': int((time.time() - inicio_processamento) * 1000),
                        'itens_processados': len(resultados_itens),
                        'observacoes': request.observacoes
                    }
                )

            # 2. INICIAR TRANSAÇÃO ATÔMICA (somente quando ainda não existir transação)
            if self.db_session.in_transaction():
                await _processar_confirmacao_transacional()
            else:
                async with self.db_session.begin():
                    await _processar_confirmacao_transacional()
            
            # 3. MONTAR RESPONSE
            tempo_total = int((time.time() - inicio_processamento) * 1000)
            itens_confirmados = sum(1 for item in resultados_itens if item.status == 'SUCESSO')
            itens_com_erro = len(resultados_itens) - itens_confirmados
            
            # Extrair dados da NF-e do primeiro item (se disponível)
            nota_fiscal = None
            data_emissao = None
            valor_total = None
            
            if dados_analise.get('nota_fiscal'):
                nota_fiscal = dados_analise['nota_fiscal']
            if dados_analise.get('data_emissao'):
                data_emissao = dados_analise['data_emissao']
            if dados_analise.get('valor_total'):
                valor_total = dados_analise['valor_total']
            
            return XMLConfirmacaoResponse(
                tenant_id=request.tenant_id,
                fornecedor_id=request.fornecedor_id,
                chave_acesso=request.chave_acesso,
                processamento_id=request.processamento_id,
                confirmacao_id=confirmacao_id,
                status=StatusConfirmacao.CONCLUIDO,
                mensagem="Processamento concluído com sucesso",
                total_items=len(resultados_itens),
                itens_confirmados=itens_confirmados,
                itens_com_erro=itens_com_erro,
                itens=resultados_itens,
                confirmado_em=datetime.utcnow(),
                tempo_processamento_ms=tempo_total,
                nota_fiscal=nota_fiscal,
                data_emissao=data_emissao,
                valor_total=valor_total
            )
            
        except Exception as e:
            # Garante que a sessão saia de estado transacional abortado.
            if self.db_session.in_transaction():
                await self.db_session.rollback()

            # Marcar erro no histórico
            try:
                await self.historico_repo.marcar_erro(
                    tenant_id=UUID(request.tenant_id),
                    chave_acesso=request.chave_acesso,
                    mensagem_erro=str(e),
                    dados_adicionais={
                        'confirmacao_id': confirmacao_id,
                        'tempo_ms': int((time.time() - inicio_processamento) * 1000),
                        'stack_trace': str(e)
                    }
                )
            except:
                # Erro ao marcar erro - log mas não propagar
                print(f"Erro ao marcar falha no histórico: {str(e)}")
            
            # Propagar exceção
            raise Exception(f"Erro na confirmação do XML: {str(e)}")

    async def _adquirir_lock_idempotencia(self, tenant_id: str, chave_acesso: str) -> None:
        """Serializa processamento por tenant/chave no PostgreSQL."""
        lock_key = f"xml-confirm:{tenant_id}:{chave_acesso}"
        await self.db_session.execute(
            text("SELECT pg_advisory_xact_lock(hashtext(:lock_key))"),
            {"lock_key": lock_key},
        )
    
    async def _obter_dados_analise(self, processamento_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém dados da análise anterior (simulado)
        
        TODO: Implementar cache/Redis para armazenar temporariamente
        """
        # Por enquanto, vamos simular dados da análise
        # Em produção, isso viria de cache ou banco temporário
        
        # Extrair chave de acesso do processamento_id (simulação)
        # Em produção, buscaríamos os dados reais da análise
        
        return {
            'itens': [
                {
                    'codigo_fornecedor': 'COCA-COLA-2L-PET',
                    'produto_id_interno': str(uuid.uuid4()),  # Simulado
                    'quantidade': 24.0,
                    'unidade': 'UN',
                    'status': StatusItemXML.MATCHED,
                    'fator_conversao': 1.0,
                    'ean': '7891000316003'
                },
                {
                    'codigo_fornecedor': 'GUARANA-ANTARTICA-CX12',
                    'produto_id_interno': str(uuid.uuid4()),  # Simulado
                    'quantidade': 2.0,
                    'unidade': 'CX',
                    'status': StatusItemXML.MATCHED,
                    'fator_conversao': 12.0,
                    'ean': '7891000150013'
                }
            ],
            'nota_fiscal': '123456',
            'data_emissao': datetime(2023, 12, 25, 10, 30),
            'valor_total': 558.00
        }
    
    async def _processar_itens(
        self,
        itens_analisados: List[Dict[str, Any]],
        tenant_id: str,
        fornecedor_id: Optional[str],
        confirmacao_id: str
    ) -> List[ResultadoItemConfirmacao]:
        """
        Processa itens atualizando estoque
        
        Args:
            itens_analisados: Itens da análise anterior
            tenant_id: ID do tenant
            fornecedor_id: ID do fornecedor
            confirmacao_id: ID da confirmação
            
        Returns:
            Lista de resultados por item
        """
        resultados = []
        
        for item_analisado in itens_analisados:
            # Apenas processar itens MATCHED
            if item_analisado.get('status') != StatusItemXML.MATCHED:
                resultados.append(ResultadoItemConfirmacao(
                    codigo_fornecedor=item_analisado['codigo_fornecedor'],
                    produto_id_interno=item_analisado.get('produto_id_interno', ''),
                    quantidade=item_analisado['quantidade'],
                    unidade=item_analisado['unidade'],
                    status='IGNORADO',
                    mensagem=f"Item com status {item_analisado['status']} não processado"
                ))
                continue
            
            try:
                # Isola falhas de item em SAVEPOINT para não abortar a transação inteira.
                async with self.db_session.begin_nested():
                    resultado = await self._processar_item_individual(
                        item=item_analisado,
                        tenant_id=tenant_id,
                        fornecedor_id=fornecedor_id,
                        confirmacao_id=confirmacao_id
                    )
                resultados.append(resultado)
                
            except Exception as e:
                # Erro em item individual - continuar com outros
                print(
                    f"Erro ao processar item {item_analisado.get('codigo_fornecedor')}: {e}"
                )
                resultados.append(ResultadoItemConfirmacao(
                    codigo_fornecedor=item_analisado['codigo_fornecedor'],
                    produto_id_interno=item_analisado.get('produto_id_interno', ''),
                    quantidade=item_analisado['quantidade'],
                    unidade=item_analisado['unidade'],
                    status='ERRO',
                    mensagem=f"Erro no processamento: {str(e)}"
                ))
        
        return resultados
    
    async def _processar_item_individual(
        self,
        item: Dict[str, Any],
        tenant_id: str,
        fornecedor_id: Optional[str],
        confirmacao_id: str
    ) -> ResultadoItemConfirmacao:
        """
        Processa item individual atualizando estoque
        
        Args:
            item: Dados do item analisado
            tenant_id: ID do tenant
            fornecedor_id: ID do fornecedor
            confirmacao_id: ID da confirmação
            
        Returns:
            Resultado do processamento
        """
        # 1. Garantir SKU sem quebrar em chave única por sku_codigo
        sku_id = await self._obter_ou_criar_sku(item)
        
        # 2. Calcular quantidade convertida
        quantidade_original = item['quantidade']
        fator_conversao = item.get('fator_conversao', 1.0)
        quantidade_convertida = quantidade_original * fator_conversao
        
        # 3. Obter endereço padrão para recebimento
        endereco = await self._obter_endereco_recebimento(tenant_id)
        if not endereco:
            raise Exception("Endereço de recebimento não configurado")
        
        # 4. Atualizar saldo de estoque
        saldo_atualizado = await self._atualizar_saldo_estoque(
            tenant_id=tenant_id,
            sku_id=sku_id,
            endereco_codigo=endereco.endereco_codigo,
            quantidade=quantidade_convertida
        )
        
        # 5. Registrar movimentação
        await self._registrar_movimentacao(
            tenant_id=tenant_id,
            sku_id=sku_id,
            endereco_origem=None,
            endereco_destino=endereco.endereco_codigo,
            quantidade=quantidade_convertida,
            motivo="RECEBIMENTO_XML",
            correlation_id=confirmacao_id,
            dados_adicionais={
                'fornecedor_id': fornecedor_id,
                'codigo_fornecedor': item['codigo_fornecedor'],
                'quantidade_original': quantidade_original,
                'fator_conversao': fator_conversao,
                'ean': item.get('ean')
            }
        )
        
        # 6. Retornar resultado
        return ResultadoItemConfirmacao(
            codigo_fornecedor=item['codigo_fornecedor'],
            produto_id_interno=sku_id,
            quantidade=quantidade_convertida,
            unidade=item['unidade'],
            status='SUCESSO',
            mensagem="Item processado com sucesso",
            endereco_destino=endereco.endereco_codigo,
            quantidade_armazenada=quantidade_convertida,
            saldo_anterior=saldo_atualizado['anterior'],
            saldo_atual=saldo_atualizado['atual']
        )

    async def _obter_ou_criar_sku(self, item: Dict[str, Any]) -> str:
        """Resolve SKU por id/codigo/ean; cria apenas quando nao existir."""
        sku_id_interno = str(item.get("produto_id_interno") or "").strip() or None
        codigo_fornecedor = str(item["codigo_fornecedor"]).strip()
        ean = str(item.get("ean") or "").strip() or None
        if ean and not ean.isdigit():
            ean = None

        if sku_id_interno:
            stmt = select(SKUModel).where(SKUModel.sku_id == sku_id_interno)
            result = await self.db_session.execute(stmt)
            sku = result.scalar_one_or_none()
            if sku:
                return sku.sku_id

        stmt = select(SKUModel).where(SKUModel.sku_codigo == codigo_fornecedor)
        result = await self.db_session.execute(stmt)
        sku = result.scalar_one_or_none()
        if sku:
            if ean and not sku.ean:
                sku.ean = ean
                await self.db_session.flush()
            return sku.sku_id

        if ean:
            stmt = select(SKUModel).where(SKUModel.ean == ean)
            result = await self.db_session.execute(stmt)
            sku = result.scalar_one_or_none()
            if sku:
                return sku.sku_id

        novo_sku = SKUModel(
            sku_id=sku_id_interno or str(uuid.uuid4()),
            sku_codigo=codigo_fornecedor,
            sku_nome=item.get("descricao") or codigo_fornecedor,
            ean=ean,
            status_ativo=True,
        )
        self.db_session.add(novo_sku)
        await self.db_session.flush()
        return novo_sku.sku_id
    
    async def _obter_endereco_recebimento(self, tenant_id: str) -> Optional[EnderecoModel]:
        """
        Obtém endereço padrão para recebimento
        
        Args:
            tenant_id: ID do tenant
            
        Returns:
            Endereço para recebimento ou None
        """
        # Buscar endereço do tipo 'reserva' ou 'deposito'
        stmt = select(EnderecoModel).where(
            and_(
                EnderecoModel.tipo_endereco.in_(['reserva', 'deposito']),
                EnderecoModel.ativo == True
            )
        ).limit(1)
        
        result = await self.db_session.execute(stmt)
        endereco = result.scalar_one_or_none()
        if endereco:
            return endereco

        endereco_default = EnderecoModel(
            endereco_codigo="DEP-RECEB-01",
            zona_codigo="DEP",
            prateleira_codigo="RECEB",
            posicao_codigo="01",
            tipo_endereco="reserva",
            ativo=True,
        )
        self.db_session.add(endereco_default)
        await self.db_session.flush()
        return endereco_default
    
    async def _atualizar_saldo_estoque(
        self,
        tenant_id: str,
        sku_id: str,
        endereco_codigo: str,
        quantidade: float
    ) -> Dict[str, float]:
        """
        Atualiza saldo de estoque de forma atômica
        
        Args:
            tenant_id: ID do tenant
            sku_id: ID do SKU
            endereco_codigo: Código do endereço
            quantidade: Quantidade a adicionar
            
        Returns:
            Dicionário com saldos anterior e atual
        """
        select_stmt = text(
            """
            SELECT saldo_disponivel
            FROM public.saldo_estoque
            WHERE sku_id = :sku_id AND endereco_codigo = :endereco_codigo
            FOR UPDATE
            """
        )
        result = await self.db_session.execute(
            select_stmt,
            {"sku_id": sku_id, "endereco_codigo": endereco_codigo},
        )
        row = result.fetchone()

        saldo_anterior = float(row[0]) if row else 0.0
        saldo_atual = saldo_anterior + quantidade

        if row:
            await self.db_session.execute(
                text(
                    """
                    UPDATE public.saldo_estoque
                    SET saldo_disponivel = :saldo_atual,
                        saldo_total = COALESCE(saldo_total, 0) + :quantidade,
                        updated_at = NOW()
                    WHERE sku_id = :sku_id AND endereco_codigo = :endereco_codigo
                    """
                ),
                {
                    "saldo_atual": saldo_atual,
                    "quantidade": quantidade,
                    "sku_id": sku_id,
                    "endereco_codigo": endereco_codigo,
                },
            )
        else:
            await self.db_session.execute(
                text(
                    """
                    INSERT INTO public.saldo_estoque (
                        saldo_estoque_id,
                        sku_id,
                        endereco_codigo,
                        saldo_disponivel,
                        saldo_avariado,
                        saldo_bloqueado,
                        saldo_total,
                        updated_at
                    ) VALUES (
                        :saldo_estoque_id,
                        :sku_id,
                        :endereco_codigo,
                        :saldo_disponivel,
                        0,
                        0,
                        :saldo_total,
                        NOW()
                    )
                    """
                ),
                {
                    "saldo_estoque_id": str(uuid.uuid4()),
                    "sku_id": sku_id,
                    "endereco_codigo": endereco_codigo,
                    "saldo_disponivel": quantidade,
                    "saldo_total": quantidade,
                },
            )

        return {"anterior": saldo_anterior, "atual": saldo_atual}
    
    async def _registrar_movimentacao(
        self,
        tenant_id: str,
        sku_id: str,
        endereco_origem: Optional[str],
        endereco_destino: str,
        quantidade: float,
        motivo: str,
        correlation_id: str,
        dados_adicionais: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Registra movimentação de estoque
        
        Args:
            tenant_id: ID do tenant
            sku_id: ID do SKU
            endereco_origem: Endereço de origem
            endereco_destino: Endereço de destino
            quantidade: Quantidade movimentada
            motivo: Motivo da movimentação
            correlation_id: ID de correlação
            dados_adicionais: Dados adicionais
            
        Returns:
            Movimentação registrada
        """
        movimentacao_id = str(uuid.uuid4())
        await self.db_session.execute(
            text(
                """
                INSERT INTO public.movimentacao_estoque (
                    movimentacao_id,
                    tipo_movimentacao,
                    sku_id,
                    quantidade,
                    endereco_origem,
                    endereco_destino,
                    motivo,
                    tenant_id,
                    correlation_id,
                    created_at,
                    schema_version
                ) VALUES (
                    :movimentacao_id,
                    :tipo_movimentacao,
                    :sku_id,
                    :quantidade,
                    :endereco_origem,
                    :endereco_destino,
                    :motivo,
                    :tenant_id,
                    :correlation_id,
                    NOW(),
                    '1.0'
                )
                """
            ),
            {
                "movimentacao_id": movimentacao_id,
                "tipo_movimentacao": TipoMovimentacao.ENTRADA.value,
                "sku_id": sku_id,
                "quantidade": quantidade,
                "endereco_origem": endereco_origem,
                "endereco_destino": endereco_destino,
                "motivo": motivo,
                "tenant_id": tenant_id,
                "correlation_id": correlation_id,
            },
        )
        return {"movimentacao_id": movimentacao_id}
    
    async def emitir_evento_recebimento_confirmado(
        self,
        tenant_id: str,
        chave_acesso: str,
        confirmacao_id: str,
        itens_processados: List[Dict[str, Any]]
    ) -> None:
        """
        Emite evento de recebimento confirmado
        
        Args:
            tenant_id: ID do tenant
            chave_acesso: Chave de acesso da NF-e
            confirmacao_id: ID da confirmação
            itens_processados: Lista de itens processados
        """
        # TODO: Implementar emissão de eventos (Event Store)
        # Por enquanto, apenas log
        
        evento = {
            'event_name': 'recebimento_xml_confirmado',
            'event_type': 'RECEBIMENTO_CONFIRMADO',
            'bounded_context': 'wms',
            'aggregate_type': 'recebimento_xml',
            'aggregate_id': confirmacao_id,
            'occurred_at': datetime.utcnow().isoformat(),
            'tenant_id': tenant_id,
            'correlation_id': confirmacao_id,
            'payload': {
                'chave_acesso': chave_acesso,
                'confirmacao_id': confirmacao_id,
                'itens_processados': itens_processados,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        print(f"EVENTO EMITIDO: {evento}")
        
        # Em produção, isso seria inserido na tabela event_store
