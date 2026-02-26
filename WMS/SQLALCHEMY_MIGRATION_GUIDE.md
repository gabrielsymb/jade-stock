# GUIA DE MIGRAÇÃO: SQL → SQLALCHEMY

## VISÃO GERAL

Este documento descreve o processo completo de migração do projeto Jade-stock de SQL puro para SQLAlchemy + Alembic, mantendo compatibilidade e sem causar regressões.

## ESTRUTURA IMPLEMENTADA

### 1. Configuração Database
```
WMS/
├── wms/
│   └── infrastructure/
│       └── database/
│           ├── __init__.py
│           └── engine.py          # Engine, session, base
```

**Componentes:**
- **Engine:** SQLAlchemy 2.0 async com PostgreSQL+asyncpg
- **Session:** Factory assíncrono com dependency injection
- **Base:** Declarativa com naming convention
- **Metadata:** Centralizada para Alembic

### 2. Models SQLAlchemy
```
WMS/
├── wms/
│   └── infrastructure/
│       └── models/
│           ├── __init__.py
│           ├── core/              # Schema core
│           │   ├── item_master.py
│           │   ├── sku.py
│           │   └── endereco.py
│           └── xml_import/        # Schema XML import
│               └── vinculo_fornecedor_produto.py
```

**Características:**
- Validações embutidas via `@validates`
- Relacionamentos com FKs
- Métodos utilitários (to_dict, __repr__)
- Compatibilidade com schema existente

### 3. Alembic Profissional
```
WMS/
├── alembic/
│   ├── alembic.ini           # Configuração
│   ├── env.py               # Ambiente SQLAlchemy
│   ├── script.py.mako       # Template de migrations
│   └── versions/            # Migrations versionadas
│       ├── 20260225_baseline_existing_schema.py
│       └── 20260225_001_create_vinculo_fornecedor_produto.py
```

**Features:**
- Suporte a operações assíncronas
- Filtros inteligentes (exclui tabelas de teste)
- Naming convention automática
- Upgrade/downgrade completos

## FLUXO DE MIGRAÇÃO

### Fase 1: Setup (✅ Concluído)
1. **Adicionar dependências:**
   ```bash
   pip install sqlalchemy>=2.0 asyncpg alembic
   ```

2. **Configurar engine e session**
3. **Configurar Alembic completo**
4. **Criar migration baseline**

### Fase 2: Models Core (✅ Concluído)
1. **Implementar models principais:**
   - ItemMasterModel
   - SKUModel  
   - EnderecoModel

2. **Adicionar validações e relacionamentos**
3. **Criar testes de integridade**

### Fase 3: Migração Gradual (🔄 Em Andamento)
1. **Manter SQL existente funcionando**
2. **Implementar novos recursos com SQLAlchemy**
3. **Migrar tabelas uma por uma**
4. **Atualizar testes gradualmente**

### Fase 4: Consolidação (⏳ Pendente)
1. **Remover SQL redundante**
2. **Padronizar tudo com ORM**
3. **Otimizar performance**

## COMANDOS ÚTEIS

### Setup Inicial
```bash
# Instalar dependências
pip install -r requirements.txt

# Inicializar Alembic (se necessário)
cd WMS
alembic init alembic

# Criar migration baseline
alembic revision --autogenerate -m "baseline_existing_schema"
```

### Operações Alembic
```bash
# Aplicar todas as migrations
alembic upgrade head

# Aplicar migration específica
alembic upgrade 20260225_baseline

# Reverter migration
alembic downgrade -1

# Gerar nova migration
alembic revision --autogenerate -m "descrição da mudança"
```

### Testes de Integridade
```bash
# Executar testes de integridade
cd WMS
python -m pytest tests/test_sqlalchemy_integrity.py -v

# Testar migração em ambiente isolado
python -m pytest tests/test_migration_integrity.py -v
```

## VALIDAÇÕES

### 1. Testes de Integridade
Os testes em `test_sqlalchemy_integrity.py` validam:
- ✅ Criação via ORM corresponde ao schema
- ✅ FKs e relacionamentos funcionam
- ✅ Constraints de unicidade são respeitadas
- ✅ Validações de dados funcionam
- ✅ Timestamps são atualizados automaticamente

### 2. Consistência de Schema
```sql
-- Verificar correspondência models ↔ tabelas
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public' 
    AND table_name IN ('item_master', 'sku', 'endereco')
ORDER BY table_name, ordinal_position;
```

### 3. Performance Baseline
```python
# Comparar performance ORM vs SQL direto
import time

# Via ORM
start = time.time()
session.query(ItemMasterModel).all()
orm_time = time.time() - start

# Via SQL direto
start = time.time()
session.execute(text("SELECT * FROM item_master"))
sql_time = time.time() - start

print(f"ORM: {orm_time:.4f}s, SQL: {sql_time:.4f}s")
```

## DECISÕES TÉCNICAS

### PKs como TEXT (Manter por enquanto)
**Decisão:** Manter PKs como TEXT para compatibilidade
**Justificativa:** Evitar quebra de FKs existentes
**Futuro:** Migrar para UUID em fase separada

### Async/Await
**Decisão:** SQLAlchemy 2.0 com async/await
**Justificativa:** Compatibilidade com FastAPI moderno
**Implementação:** AsyncSession com async engine

### Naming Convention
**Decisão:** Convention automática via metadata
**Benefícios:** Índices e constraints padronizados
**Exemplo:** `uq_sku_ean_not_null`, `ix_sku_item_master`

## RISCOS E MITIGAÇÃO

### Risco: Performance
**Mitigação:**
- Índices otimizados mantidos
- Queries complexas podem permanecer em SQL
- Monitoramento de performance implementado

### Risco: Complexidade
**Mitigação:**
- Documentação detalhada
- Exemplos práticos
- Testes abrangentes

### Risco: Regressão
**Mitigação:**
- Migration baseline segura
- Testes de integridade
- Rollback fácil via Alembic

## PRÓXIMOS PASSOS

1. **Implementar Services para models core**
2. **Migrar tabelas extended**
3. **Atualizar testes existentes**
4. **Criar dashboard de migração**
5. **Documentar patterns de uso**

## CRITÉRIOS DE SUCESSO

- [ ] Todos os testes existentes continuam passando
- [ ] Novos models funcionam corretamente
- [ ] Migrations aplicam sem erros
- [ ] Performance aceitável
- [ ] Documentação completa
- [ ] Time produtivo com nova stack

## REFERÊNCIAS

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [Alembic Documentation](https://alembic.sqlalchemy.org/)
- [FastAPI + SQLAlchemy](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- [PostgreSQL + AsyncPG](https://magicstack.github.io/asyncpg/current/)
