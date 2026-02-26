"""
Testes de Integridade SQLAlchemy ↔ Banco
Valida que models SQLAlchemy correspondem ao schema real
"""

import pytest
import pytest_asyncio
import asyncio
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from wms.infrastructure.database import engine, AsyncSessionLocal, Base
from wms.infrastructure.models.core.item_master import ItemMasterModel
from wms.infrastructure.models.core.sku import SKUModel
from wms.infrastructure.models.core.endereco import EnderecoModel


class TestSQLAlchemyIntegrity:
    """Testes de integridade entre models e schema do banco"""
    
    @pytest_asyncio.fixture
    async def clean_db(self, db_session: AsyncSession):
        """Limpa tabelas antes de cada teste"""
        # Limpeza usando TRUNCATE CASCADE para respeitar FKs de outras tabelas.
        await db_session.execute(
            text("TRUNCATE TABLE public.sku, public.item_master, public.endereco CASCADE")
        )
        await db_session.commit()
        yield
        # Cleanup após teste
        await db_session.rollback()
        await db_session.execute(
            text("TRUNCATE TABLE public.sku, public.item_master, public.endereco CASCADE")
        )
        await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_create_item_master_model(self, db_session: AsyncSession, clean_db):
        """Testa criação de ItemMaster via ORM"""
        # Criar item master
        item = ItemMasterModel(
            item_master_id="TEST-001",
            item_nome="Item Teste SQLAlchemy",
            categoria_id="CAT-001",
            classe_abc="A",
            created_by="test_user"
        )
        
        # Persistir
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)
        
        # Validar persistência
        assert item.item_master_id == "TEST-001"
        assert item.item_nome == "Item Teste SQLAlchemy"
        assert item.created_at is not None
        assert item.updated_at is not None
        
        # Validar via query SQL direta
        result = await db_session.execute(
            text("SELECT * FROM item_master WHERE item_master_id = :id"),
            {"id": "TEST-001"}
        )
        row = result.fetchone()
        
        assert row is not None
        assert row[1] == "Item Teste SQLAlchemy"  # item_nome
        assert row[2] == "CAT-001"  # categoria_id
    
    @pytest.mark.asyncio
    async def test_create_sku_model_with_fk(self, db_session: AsyncSession, clean_db):
        """Testa criação de SKU com FK para item_master"""
        # Primeiro criar item master
        item = ItemMasterModel(
            item_master_id="TEST-002",
            item_nome="Item Pai Teste",
            created_by="test_user"
        )
        db_session.add(item)
        await db_session.commit()
        
        # Criar SKU com FK
        sku = SKUModel(
            sku_id="SKU-001",
            sku_codigo="TEST-001",
            sku_nome="SKU Teste SQLAlchemy",
            item_master_id="TEST-002",  # FK válida
            ean="7891000316003",
            status_ativo=True,
            created_by="test_user"
        )
        
        db_session.add(sku)
        await db_session.commit()
        await db_session.refresh(sku)
        
        # Validar relacionamento
        assert sku.item_master_id == "TEST-002"
        assert sku.ean == "7891000316003"
        assert sku.status_ativo is True
        
        # Validar FK via query
        result = await db_session.execute(
            text("""
                SELECT s.*, i.item_nome 
                FROM sku s 
                LEFT JOIN item_master i ON s.item_master_id = i.item_master_id 
                WHERE s.sku_id = :id
            """),
            {"id": "SKU-001"}
        )
        row = result.fetchone()
        
        assert row is not None
        assert row[-1] == "Item Pai Teste"  # item_nome do join
    
    @pytest.mark.asyncio
    async def test_create_endereco_model(self, db_session: AsyncSession, clean_db):
        """Testa criação de Endereço via ORM"""
        endereco = EnderecoModel(
            endereco_codigo="DEP-A-01",
            zona_codigo="DEP",
            prateleira_codigo="A",
            posicao_codigo="01",
            tipo_endereco="reserva",
            capacidade_maxima=100.5,
            ativo=True,
            created_by="test_user"
        )
        
        db_session.add(endereco)
        await db_session.commit()
        await db_session.refresh(endereco)
        
        # Validar persistência
        assert endereco.endereco_codigo == "DEP-A-01"
        assert endereco.zona_codigo == "DEP"
        assert endereco.tipo_endereco == "reserva"
        assert float(endereco.capacidade_maxima) == 100.5
        assert endereco.ativo is True
    
    @pytest.mark.asyncio
    async def test_model_validations(self, db_session: AsyncSession, clean_db):
        """Testa validações dos models"""
        # Teste ItemMaster - nome obrigatório
        with pytest.raises(ValueError, match="Nome do item é obrigatório"):
            item = ItemMasterModel(
                item_master_id="TEST-003",
                item_nome="",  # Inválido
                created_by="test_user"
            )
            db_session.add(item)
            await db_session.commit()
        
        await db_session.rollback()
        
        # Teste SKU - EAN inválido
        with pytest.raises(ValueError, match="EAN deve conter apenas dígitos"):
            sku = SKUModel(
                sku_id="SKU-002",
                sku_codigo="TEST-002",
                sku_nome="SKU Teste",
                ean="789100031600A",  # Inválido: contém letra
                created_by="test_user"
            )
            db_session.add(sku)
            await db_session.commit()
        
        await db_session.rollback()
        
        # Teste Endereço - tipo inválido
        with pytest.raises(ValueError, match="Tipo de endereço deve ser um de"):
            endereco = EnderecoModel(
                endereco_codigo="DEP-B-01",
                zona_codigo="DEP",
                tipo_endereco="invalido",  # Inválido
                created_by="test_user"
            )
            db_session.add(endereco)
            await db_session.commit()
    
    @pytest.mark.asyncio
    async def test_unique_constraints(self, db_session: AsyncSession, clean_db):
        """Testa constraints de unicidade"""
        # Criar SKU
        sku1 = SKUModel(
            sku_id="SKU-003",
            sku_codigo="UNIQUE-001",
            sku_nome="SKU Único 1",
            created_by="test_user"
        )
        db_session.add(sku1)
        await db_session.commit()
        
        # Tentar criar SKU com mesmo código (deve falhar)
        with pytest.raises(Exception):  # SQLAlchemy vai levantar exceção de constraint
            sku2 = SKUModel(
                sku_id="SKU-004",
                sku_codigo="UNIQUE-001",  # Duplicado
                sku_nome="SKU Único 2",
                created_by="test_user"
            )
            db_session.add(sku2)
            await db_session.commit()
        await db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_model_to_dict_conversion(self, db_session: AsyncSession, clean_db):
        """Testa conversão de models para dicionário"""
        item = ItemMasterModel(
            item_master_id="TEST-004",
            item_nome="Item Teste Dict",
            categoria_id="CAT-DICT",
            created_by="test_user"
        )
        
        # Converter para dict sem persistir
        item_dict = item.to_dict()
        
        assert item_dict['item_master_id'] == "TEST-004"
        assert item_dict['item_nome'] == "Item Teste Dict"
        assert item_dict['categoria_id'] == "CAT-DICT"
        assert 'created_at' in item_dict
        assert 'updated_at' in item_dict
    
    @pytest.mark.asyncio
    async def test_relationship_loading(self, db_session: AsyncSession, clean_db):
        """Testa carregamento de relacionamentos"""
        # Criar item master
        item = ItemMasterModel(
            item_master_id="TEST-005",
            item_nome="Item com SKUs",
            created_by="test_user"
        )
        db_session.add(item)
        await db_session.commit()
        
        # Criar múltiplos SKUs
        skus = [
            SKUModel(
                sku_id="SKU-005",
                sku_codigo="MULTI-001",
                sku_nome="SKU Multi 1",
                item_master_id="TEST-005",
                created_by="test_user"
            ),
            SKUModel(
                sku_id="SKU-006",
                sku_codigo="MULTI-002",
                sku_nome="SKU Multi 2",
                item_master_id="TEST-005",
                created_by="test_user"
            )
        ]
        
        for sku in skus:
            db_session.add(sku)
        await db_session.commit()
        
        # Carregar item com relacionamento
        result = await db_session.execute(
            select(ItemMasterModel).where(ItemMasterModel.item_master_id == "TEST-005")
        )
        item_loaded = result.scalar_one()
        
        # Validar relacionamento (lazy loading)
        assert item_loaded.item_master_id == "TEST-005"
        
        # Carregar SKUs relacionados
        result = await db_session.execute(
            select(SKUModel).where(SKUModel.item_master_id == "TEST-005")
        )
        skus_loaded = result.scalars().all()
        
        assert len(skus_loaded) == 2
        assert {sku.sku_codigo for sku in skus_loaded} == {"MULTI-001", "MULTI-002"}
    
    @pytest.mark.asyncio
    async def test_timestamps_auto_update(self, db_session: AsyncSession, clean_db):
        """Testa atualização automática de timestamps"""
        # Criar item
        item = ItemMasterModel(
            item_master_id="TEST-006",
            item_nome="Item Timestamp",
            created_by="test_user"
        )
        db_session.add(item)
        await db_session.commit()
        
        created_at_original = item.created_at
        updated_at_original = item.updated_at
        
        # Pequena pausa para garantir diferença de timestamp
        await asyncio.sleep(0.01)
        
        # Atualizar item
        item.item_nome = "Item Timestamp Atualizado"
        await db_session.commit()
        await db_session.refresh(item)
        
        # Validar timestamps
        assert item.created_at is not None
        assert created_at_original is not None
        updated_at_before = updated_at_original
        updated_at_after = item.updated_at
        if updated_at_before.tzinfo is None:
            updated_at_before = updated_at_before.replace(tzinfo=timezone.utc)
        if updated_at_after.tzinfo is None:
            updated_at_after = updated_at_after.replace(tzinfo=timezone.utc)
        assert updated_at_after > updated_at_before  # Deve ser atualizado
    
    @pytest.mark.asyncio
    async def test_database_schema_consistency(self, db_session: AsyncSession):
        """Testa consistência entre models e schema real do banco"""
        # Verificar se tabelas existem
        result = await db_session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('item_master', 'sku', 'endereco')
            ORDER BY table_name
        """))
        tables = [row[0] for row in result.fetchall()]
        
        expected_tables = ['endereco', 'item_master', 'sku']
        assert tables == expected_tables, f"Tabelas esperadas: {expected_tables}, encontradas: {tables}"
        
        # Verificar estrutura da tabela item_master
        result = await db_session.execute(text("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'item_master' 
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """))
        columns = {row[0]: {'type': row[1], 'nullable': row[2]} for row in result.fetchall()}
        
        # Colunas obrigatórias devem existir
        required_columns = ['item_master_id', 'item_nome', 'created_at', 'updated_at']
        for col in required_columns:
            assert col in columns, f"Coluna {col} não encontrada na tabela item_master"
            if col in ['item_master_id', 'item_nome']:
                assert columns[col]['nullable'] == 'NO', f"Coluna {col} deve ser NOT NULL"
