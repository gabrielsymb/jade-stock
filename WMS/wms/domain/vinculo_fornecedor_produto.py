"""
Entidade de Domínio: VinculoFornecedorProduto
Responsável por traduzir códigos de fornecedor
"""
from typing import Optional, Dict, Any
from uuid import UUID
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum


class StatusVinculo(str, Enum):
    """Status do vínculo fornecedor-produto"""
    ATIVO = "ativo"
    INATIVO = "inativo"
    EM_VALIDACAO = "em_validacao"


class TipoUnidade(str, Enum):
    """Unidades de medida suportadas"""
    UNIDADE = "UN"
    CAIXA = "CX"
    FARDAMENTO = "FD"
    PACOTE = "PCT"
    QUILOGRAMA = "KG"
    LITRO = "L"
    METRO = "M"
    METRO_QUADRADO = "M2"


@dataclass
class VinculoFornecedorProduto:
    """
    Entidade que representa a tradução entre código do fornecedor e produto interno.
    
    Propósito:
    - Permitir aprendizado contínuo do sistema
    - Suportar múltiplos fornecedores para o mesmo produto
    - Habilitar conversão automática de unidades
    - Manter rastreabilidade de origem
    
    Exemplo Real:
    - Fornecedor: Distribuidora Solar
    - Código Fornecedor: "COCA-COLA-12X350ML"
    - Produto Interno: UUID do "Refrigerante Coca-Cola 2L"
    - Fator Conversão: 12.0 (12 unidades de 350ml = 1 produto interno de 2L)
    """
    
    # Identificação
    id: UUID
    tenant_id: UUID
    fornecedor_id: str  # CNPJ/CPF ou código do fornecedor
    codigo_fornecedor: str
    produto_id_interno: UUID
    
    # Conversão de Unidades
    fator_conversao: Decimal = field(default=Decimal("1.0"))
    unidade_origem: Optional[TipoUnidade] = None
    unidade_destino: Optional[TipoUnidade] = None
    
    # Metadados de Controle
    status: StatusVinculo = field(default=StatusVinculo.ATIVO)
    vezes_utilizado: int = field(default=0)
    ultima_importacao: Optional[datetime] = None
    
    # Auditoria
    criado_em: datetime = field(default_factory=datetime.utcnow)
    atualizado_em: datetime = field(default_factory=datetime.utcnow)
    criado_por: Optional[UUID] = None
    
    # Configuração de Aprendizado
    peso_confianca: Decimal = field(default=Decimal("1.0"))  # Peso para algoritmo futuro
    ultima_validacao: Optional[datetime] = None
    
    def __post_init__(self):
        """Validações pós-inicialização"""
        self._validar_campos_obrigatorios()
        self._validar_regras_negocio()
    
    def _validar_campos_obrigatorios(self):
        """Validação de campos obrigatórios"""
        if not self.id:
            raise ValueError("ID é obrigatório")
        if not self.tenant_id:
            raise ValueError("Tenant ID é obrigatório")
        if not self.fornecedor_id:
            raise ValueError("Fornecedor ID é obrigatório")
        if not self.codigo_fornecedor or not self.codigo_fornecedor.strip():
            raise ValueError("Código do fornecedor é obrigatório")
        if not self.produto_id_interno:
            raise ValueError("Produto ID interno é obrigatório")
    
    def _validar_regras_negocio(self):
        """Validação de regras de negócio"""
        # Código do fornecedor não pode exceder limite
        if len(self.codigo_fornecedor.strip()) > 100:
            raise ValueError("Código do fornecedor não pode exceder 100 caracteres")
        
        # Fator de conversão deve ser positivo
        if self.fator_conversao <= 0:
            raise ValueError("Fator de conversão deve ser maior que zero")
        
        # Peso de confiança deve estar entre 0 e 10
        if not (0 <= self.peso_confianca <= 10):
            raise ValueError("Peso de confiança deve estar entre 0 e 10")
        
        # Vezes utilizado não pode ser negativo
        if self.vezes_utilizado < 0:
            raise ValueError("Vezes utilizado não pode ser negativo")
    
    def calcular_quantidade_convertida(self, quantidade_original: Decimal) -> Decimal:
        """
        Converte quantidade do fornecedor para quantidade interna
        
        Args:
            quantidade_original: Quantidade na unidade do fornecedor
            
        Returns:
            Quantidade convertida para unidade interna
            
        Example:
            vinculo = VinculoFornecedorProduto(
                fator_conversao=Decimal("12.0"),
                unidade_origem=TipoUnidade.CAIXA,
                unidade_destino=TipoUnidade.UNIDADE
            )
            resultado = vinculo.calcular_quantidade_convertida(Decimal("2.5"))  # 2.5 caixas
            # resultado = Decimal("30.0")  # 30 unidades
        """
        return quantidade_original * self.fator_conversao
    
    def registrar_utilizacao(self, data_utilizacao: Optional[datetime] = None):
        """
        Registra utilização do vínculo para estatísticas
        
        Args:
            data_utilizacao: Data da utilização (padrão: agora)
        """
        self.vezes_utilizado += 1
        self.ultima_importacao = data_utilizacao or datetime.utcnow()
        self.atualizado_em = datetime.utcnow()
    
    def desativar(self):
        """Desativa o vínculo temporariamente"""
        self.status = StatusVinculo.INATIVO
        self.atualizado_em = datetime.utcnow()
    
    def reativar(self):
        """Reativa o vínculo"""
        self.status = StatusVinculo.ATIVO
        self.atualizado_em = datetime.utcnow()
    
    def marcar_para_validacao(self):
        """Marca vínculo como necessitando validação manual"""
        self.status = StatusVinculo.EM_VALIDACAO
        self.atualizado_em = datetime.utcnow()
    
    def validar(self):
        """Confirma validação do vínculo"""
        self.status = StatusVinculo.ATIVO
        self.ultima_validacao = datetime.utcnow()
        self.atualizado_em = datetime.utcnow()
    
    def atualizar_fator_conversao(self, novo_fator: Decimal):
        """
        Atualiza fator de conversão com validação
        
        Args:
            novo_fator: Novo fator de conversão
        """
        if novo_fator <= 0:
            raise ValueError("Fator de conversão deve ser maior que zero")
        
        self.fator_conversao = novo_fator
        self.atualizado_em = datetime.utcnow()
    
    def ajustar_peso_confianca(self, novo_peso: Decimal):
        """
        Ajusta peso de confiança para algoritmo de aprendizado
        
        Args:
            novo_peso: Novo peso (0-10)
        """
        if not (0 <= novo_peso <= 10):
            raise ValueError("Peso de confiança deve estar entre 0 e 10")
        
        self.peso_confianca = novo_peso
        self.atualizado_em = datetime.utcnow()
    
    @property
    def descricao_completa(self) -> str:
        """
        Retorna descrição completa do vínculo para logs e debugging
        
        Returns:
            String formatada com informações principais
        """
        return (
            f"Vínculo [{self.id}] "
            f"Fornecedor[{self.fornecedor_id}] "
            f"Código[{self.codigo_fornecedor}] → "
            f"Produto[{self.produto_id_interno}] "
            f"(Fator: {self.fator_conversao}, "
            f"Status: {self.status.value})"
        )
    
    @property
    def eh_recente(self) -> bool:
        """
        Verifica se vínculo é recente (criado nos últimos 30 dias)
        
        Returns:
            True se criado nos últimos 30 dias
        """
        trinta_dias_atras = datetime.utcnow() - timedelta(days=30)
        return self.criado_em >= trinta_dias_atras
    
    @property
    def eh_frequentemente_utilizado(self) -> bool:
        """
        Verifica se vínculo é frequentemente utilizado (>10 vezes)
        
        Returns:
            True se utilizado mais de 10 vezes
        """
        return self.vezes_utilizado > 10
    
    def to_dict(self) -> dict:
        """
        Converte entidade para dicionário (serialização)
        
        Returns:
            Dicionário com todos os campos
        """
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "fornecedor_id": str(self.fornecedor_id),
            "codigo_fornecedor": self.codigo_fornecedor,
            "produto_id_interno": str(self.produto_id_interno),
            "fator_conversao": float(self.fator_conversao),
            "unidade_origem": self.unidade_origem.value if self.unidade_origem else None,
            "unidade_destino": self.unidade_destino.value if self.unidade_destino else None,
            "status": self.status.value,
            "vezes_utilizado": self.vezes_utilizado,
            "ultima_importacao": self.ultima_importacao.isoformat() if self.ultima_importacao else None,
            "peso_confianca": float(self.peso_confianca),
            "criado_em": self.criado_em.isoformat(),
            "atualizado_em": self.atualizado_em.isoformat(),
            "criado_por": str(self.criado_por) if self.criado_por else None,
            "ultima_validacao": self.ultima_validacao.isoformat() if self.ultima_validacao else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "VinculoFornecedorProduto":
        """
        Cria entidade a partir de dicionário (deserialização)
        
        Args:
            data: Dicionário com dados da entidade
            
        Returns:
            Instância de VinculoFornecedorProduto
        """
        return cls(
            id=UUID(data["id"]),
            tenant_id=UUID(data["tenant_id"]),
            fornecedor_id=str(data["fornecedor_id"]),
            codigo_fornecedor=data["codigo_fornecedor"],
            produto_id_interno=UUID(data["produto_id_interno"]),
            fator_conversao=Decimal(str(data["fator_conversao"])),
            unidade_origem=TipoUnidade(data["unidade_origem"]) if data.get("unidade_origem") else None,
            unidade_destino=TipoUnidade(data["unidade_destino"]) if data.get("unidade_destino") else None,
            status=StatusVinculo(data["status"]),
            vezes_utilizado=data["vezes_utilizado"],
            ultima_importacao=datetime.fromisoformat(data["ultima_importacao"]) if data.get("ultima_importacao") else None,
            peso_confianca=Decimal(str(data["peso_confianca"])),
            criado_em=datetime.fromisoformat(data["criado_em"]),
            atualizado_em=datetime.fromisoformat(data["atualizado_em"]),
            criado_por=UUID(data["criado_por"]) if data.get("criado_por") else None,
            ultima_validacao=datetime.fromisoformat(data["ultima_validacao"]) if data.get("ultima_validacao") else None,
        )
