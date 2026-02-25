# Guia de Contribuição - Jade-stock

**Bem-vindo(a)!** 🎉  
Este documento orienta como contribuir com o projeto Jade-stock de forma eficaz e alinhada com nossos padrões.

---

## 🎯 Filosofia de Contribuição

> **"Contribua como se fosse manter"** - Escreva código e documentação que você gostaria de encontrar ao usar este projeto.

### Princípios
- **Clareza antes de otimização prematura**
- **Automação em todo pipeline crítico**
- **Documentação como código vivo**
- **Testes como rede de segurança**
- **Eventos como cola do sistema**

---

## 🚀 Começo Rápido

### 1. Setup do Ambiente
```bash
# Fork e clone
git clone https://github.com/SEU_USERNAME/Jade-stock.git
cd Jade-stock

# Ambiente virtual
python3 -m venv .venv
source .venv/bin/activate

# Dependências
python -m pip install --upgrade pip
python -m pip install -r WMS/requirements-dev.txt
```

### 2. Verificar Setup
```bash
# Testes devem passar
cd WMS
python3 -m unittest discover -s tests -p 'test_*.py' -v

# API deve subir
./scripts/run_api.sh
curl http://127.0.0.1:8001/v1/health
```

---

## 📋 Processo de Contribuição

### 1. Escolher um Tópico
- **Bug:** Verificar [Issues abertas](https://github.com/SEU_ORG/Jade-stock/issues)
- **Feature:** Abrir issue para discussão antes de codar
- **Documentação:** Melhorar docs existentes ou criar novas
- **Testes:** Aumentar cobertura ou adicionar casos de teste

### 2. Criar Branch
```bash
# Padrão de nome de branch
git checkout -b feature/nome-da-feature
git checkout -b fix/descricao-do-bug
git checkout -b docs/melhoria-de-docs
```

### 3. Desenvolver
- **Código:** Seguir padrões do projeto
- **Testes:** Escrever testes para novas funcionalidades
- **Docs:** Atualizar documentação relevante
- **Commits:** Usar conventional commits

### 4. Testar Localmente
```bash
# Suite completa de testes
cd WMS
python3 -m unittest discover -s tests -p 'test_*.py' -v

# Release gate
./scripts/release_gate.sh

# Lint (se configurado)
flake8 wms/
black wms/
```

### 5. Abrir Pull Request
- **Título descritivo:** Seguir conventional commits
- **Descrição detalhada:** O que e por que mudou
- **Links:** Referenciar issues relacionadas
- **Screenshots:** Para mudanças visuais

---

## 📝 Padrões de Código

### Python
```python
# ✅ Bom - type hints, docstring, claro
from typing import Dict, List
from dataclasses import dataclass

@dataclass
class MovimentacaoEstoque:
    """Representa uma movimentação de estoque no WMS.
    
    Attributes:
        sku_id: Identificador único do SKU
        quantidade: Quantidade movimentada (sempre positiva)
        tipo: Tipo da movimentação (entrada, saida, transferencia)
    """
    sku_id: str
    quantidade: float
    tipo: str
    endereco_origem: str | None = None
    endereco_destino: str | None = None

    def __post_init__(self) -> None:
        """Validações pós-inicialização."""
        if self.quantidade <= 0:
            raise ValueError("Quantidade deve ser positiva")
```

### Nomenclatura
- **Classes:** `PascalCase` → `MovimentacaoEstoque`
- **Funções/variáveis:** `snake_case` → `registrar_movimentacao`
- **Constantes:** `UPPER_SNAKE_CASE` → `TENANT_ID_DEFAULT`
- **Privado:** `_prefixo` → `_validar_campos`

### Imports
```python
# ✅ Ordem correta
import os
from dataclasses import dataclass
from typing import Dict, List

from fastapi import FastAPI
from wms.domain.exceptions import DomainError
```

---

## 🧪 Padrões de Testes

### Estrutura de Teste
```python
import unittest
from unittest.mock import Mock

from wms.application.use_cases.registrar_movimentacao_estoque import (
    RegistrarMovimentacaoEstoque,
)
from wms.domain.movimentacao import MovimentacaoEstoque


class TestRegistrarMovimentacaoEstoque(unittest.TestCase):
    """Testes para RegistrarMovimentacaoEstoque."""

    def setUp(self) -> None:
        """Setup para cada teste."""
        self.mov_repo = Mock()
        self.estoque_repo = Mock()
        self.publisher = Mock()
        self.use_case = RegistrarMovimentacaoEstoque(
            self.mov_repo, self.estoque_repo, self.publisher
        )

    def test_registrar_movimentacao_sucesso(self) -> None:
        """Testa registro bem-sucedido de movimentação."""
        # Arrange
        data = MovimentacaoEstoque(
            sku_id="sku_001",
            quantidade=10.0,
            tipo="entrada",
            endereco_destino="DEP-A-01",
        )
        
        # Act
        result = self.use_case.execute(data)
        
        # Assert
        self.assertIsNotNone(result)
        self.mov_repo.registrar.assert_called_once()
        self.publisher.publish.assert_called_once()

    def test_registrar_movimentacao_sem_estoque(self) -> None:
        """Testa falha quando SKU não existe no estoque."""
        # Arrange
        data = MovimentacaoEstoque(
            sku_id="sku_inexistente",
            quantidade=10.0,
            tipo="entrada",
        )
        self.estoque_repo.existe_sku.return_value = False
        
        # Act & Assert
        with self.assertRaises(DomainError):
            self.use_case.execute(data)
```

### Nomenclatura de Testes
- **Métodos:** `test_<unidade>_<cenario>_<resultado_esperado>`
- **Classes:** `Test<NomeDaClasse>`
- **Fixtures:** `setUp` e `tearDown`

---

## 📚 Padrões de Documentação

### Documentos de Código
```python
def calcular_giro_estoque(
    estoque_atual: float,
    venda_media_diaria: float,
    periodo_dias: int = 30,
) -> float:
    """Calcula o giro de estoque em períodos.
    
    Args:
        estoque_atual: Estoque médio no período
        venda_media_diaria: Venda média diária
        periodo_dias: Período de análise em dias
        
    Returns:
        Giro de estoque (número de períodos que o estoque dura)
        
    Raises:
        ValueError: Se venda_media_diaria for zero ou negativa
        
    Example:
        >>> calcular_giro_estoque(100, 10)
        10.0
    """
    if venda_media_diaria <= 0:
        raise ValueError("Venda média diária deve ser positiva")
    
    return estoque_atual / venda_media_diaria
```

### Markdown
- **Títulos:** Hierárquicos e descritivos
- **Código:** Sempre especificar linguagem
- **Links:** Relativos quando possível
- **Imagens:** Com texto alternativo

---

## 🔄 Conventional Commits

### Formato
```
<tipo>[escopo opcional]: <descrição>

[corpo opcional]

[rodapé(s) opcional(is)]
```

### Tipos
- **feat:** Nova funcionalidade
- **fix:** Correção de bug
- **docs:** Documentação
- **style:** Formatação (sem lógica)
- **refactor:** Refatoração
- **test:** Testes
- **chore:** Manutenção

### Exemplos
```bash
feat(wms): adicionar endpoint de curva ABC

Implementar processamento de curva ABC com classificação
automática por impacto econômico e variabilidade.

Closes #123
```

```bash
fix(api): corrigir validação de idempotência

Problema ocorria quando correlation_id era reutilizado
com payload diferente em menos de 24h.
```

```bash
docs(readme): atualizar guia de instalação

Adicionar instruções para PostgreSQL 14+ e ambiente
virtual com Python 3.11.
```

---

## 📋 Checklist de PR

### Antes de Abrir PR
- [ ] **Código** segue padrões do projeto
- [ ] **Testes** novos e existentes passando
- [ ] **Documentação** atualizada
- [ ] **Commits** seguem conventional commits
- [ ] **Branch** atualizado com main

### Após Abrir PR
- [ ] **CI/CD** passando
- [ ] **Revisão** solicitada aos mantenedores
- [ ] **Descrição** completa e clara
- [ ] **Issues** referenciadas

### Antes do Merge
- [ ] **Feedback** incorporado
- [ ] **Conflitos** resolvidos
- [ ] **Testes** finais passando
- [ ] **Documentação** final revisada

---

## 🏗️ Arquitetura e Decisões

### Decisões Arquiteturais
- **Monolito Modular** para equipe enxuta
- **PostgreSQL** com schemas segregados
- **Event Store** para comunicação assíncrona
- **FastAPI** para APIs RESTful
- **Python 3.11+** com type hints

### Padrões de Projeto
- **Domain-Driven Design** para lógica de negócio
- **Repository Pattern** para persistência
- **Factory Method** para criação de objetos
- **Dependency Injection** para testabilidade

### O QUE NÃO FAZER
- ❌ Introduzir microserviços complexos
- ❌ Usar NoSQL sem necessidade clara
- ❌ Adicionar frameworks pesados
- ❌ Quebrar compatibilidade sem migração

---

## 🆘 Como Obter Ajuda

### Para Contribuidores
- **Issues:** Abrir issue para dúvidas
- **Discussions:** Usar GitHub Discussions
- **Documentation:** Consultar [Bíblia do Sistema](./JADE-STOCK-BIBLIA-DO-SISTEMA.md)

### Canais de Comunicação
- **GitHub Issues:** Bugs e features
- **GitHub Discussions:** Dúvidas e ideias
- **Pull Requests:** Revisão de código

### Recursos Internos
- [📖 Bíblia do Sistema](./JADE-STOCK-BIBLIA-DO-SISTEMA.md)
- [🔧 Guia de Setup](./WMS/README.md)
- [📋 Boas Práticas](./DOCS_BOAS_PRACTICES.md)
- [🗂️ Análise de Docs](./ANALISE_DOCUMENTACAO.md)

---

## 🎉 Reconhecimento

### Contribuidores
Todos os contribuidores são reconhecidos em:
- **README.md** na seção de contribuidores
- **Release notes** para contribuições significativas
- **Commits** preservam autoria original

### Tipos de Contribuição
- **Código:** Features, fixes, refatoração
- **Documentação:** Guia, tutoriais, exemplos
- **Testes:** Cobertura, casos de teste
- **Design:** UI/UX, diagramas
- **Comunidade:** Suporte, feedback, divulgação

---

## 📜 Código de Conduta

### Nosso Compromisso
- **Respeito:** Tratar todos com dignidade
- **Inclusão:** Ambiente acolhedor para todos
- **Colaboração:** Espírito construtivo
- **Aprendizado:** Disposição para ensinar e aprender

### O QUE NÃO TOLERAMOS
- Assédio ou discriminação
- Linguagem ofensiva
- Comportamento disruptivo
- Divulgação de informação confidencial

---

## 🚀 Próximos Passos

### Para Começar
1. Leia [Bíblia do Sistema](./JADE-STOCK-BIBLIA-DO-SISTEMA.md)
2. Configure ambiente local
3. Escolha uma issue para começar
4. Faça seu primeiro PR

### Para Evoluir
1. Contribua regularmente
2. Ajude a revisar PRs de outros
3. Participe das discussões
4. Mantenha-se atualizado com roadmap

---

## 📚 Recursos Adicionais

### Aprendizado
- [Python Best Practices](https://docs.python-guide.org/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [PostgreSQL Docs](https://www.postgresql.org/docs/)
- [Domain-Driven Design](https:// VaughnVernon/DDDD)

### Ferramentas
- **VS Code:** Python + Docker extensions
- **Postico:** PostgreSQL client
- **Postman:** API testing
- **Git:** Controle de versão

---

**Obrigado por contribuir!** 🙏  
Juntos construímos um sistema melhor.

---

*Este guia evolui com o projeto • Contribua através de PRs*  
*Última atualização: 2026-02-25 • Versão: 1.0*
