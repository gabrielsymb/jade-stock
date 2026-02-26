"""Create vinculo_fornecedor_produto table

Revision ID: 20260225_001
Revises: 20260224_event_store_bounded_context
Create Date: 2026-02-25 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260225_001'
down_revision = '20260224_event_store_bounded_context'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vinculo_fornecedor_produto table with all indexes and constraints"""
    
    # Create enum types
    op.execute("CREATE TYPE IF NOT EXISTS vinculo_status AS ENUM ('ativo', 'inativo', 'em_validacao')")
    op.execute("CREATE TYPE IF NOT EXISTS unidade_medida AS ENUM ('UN', 'CX', 'FD', 'PCT', 'KG', 'L', 'M', 'M2')")
    
    # Create main table
    op.create_table(
        'vinculo_fornecedor_produto',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fornecedor_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('codigo_fornecedor', sa.String(length=100), nullable=False),
        sa.Column('produto_id_interno', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('fator_conversao', sa.Numeric(precision=15, scale=6), nullable=False, default=sa.text('1.0')),
        sa.Column('unidade_origem', sa.Enum('UN', 'CX', 'FD', 'PCT', 'KG', 'L', 'M', 'M2', name='unidade_medida'), nullable=True),
        sa.Column('unidade_destino', sa.Enum('UN', 'CX', 'FD', 'PCT', 'KG', 'L', 'M', 'M2', name='unidade_medida'), nullable=True),
        sa.Column('status', sa.Enum('ativo', 'inativo', 'em_validacao', name='vinculo_status'), nullable=False, default='ativo'),
        sa.Column('vezes_utilizado', sa.Integer(), nullable=False, default=sa.text('0')),
        sa.Column('ultima_importacao', sa.DateTime(), nullable=True),
        sa.Column('peso_confianca', sa.Numeric(precision=5, scale=2), nullable=False, default=sa.text('1.0')),
        sa.Column('criado_em', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('atualizado_em', sa.DateTime(), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('criado_por', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('ultima_validacao', sa.DateTime(), nullable=True),
        sa.CheckConstraint('fator_conversao > 0', name='vinculo_fornecedor_produto_fator_positivo'),
        sa.CheckConstraint('vezes_utilizado >= 0', name='vinculo_fornecedor_produto_uso_nao_negativo'),
        sa.CheckConstraint('peso_confianca >= 0 AND peso_confianca <= 10', name='ck_peso_confianca_range'),
        sa.UniqueConstraint('tenant_id', 'fornecedor_id', 'codigo_fornecedor', name='vinculo_fornecedor_produto_unique'),
        schema='wms'
    )
    
    # Create indexes
    op.create_index(
        'idx_vinculo_fornecedor_produto_fornecedor_codigo',
        'vinculo_fornecedor_produto',
        ['fornecedor_id', 'codigo_fornecedor'],
        schema='wms'
    )
    
    op.create_index(
        'idx_vinculo_fornecedor_produto_produto',
        'vinculo_fornecedor_produto',
        ['produto_id_interno'],
        schema='wms'
    )
    
    op.create_index(
        'idx_vinculo_fornecedor_produto_tenant',
        'vinculo_fornecedor_produto',
        ['tenant_id'],
        schema='wms'
    )
    
    op.create_index(
        'idx_vinculo_fornecedor_produto_status',
        'vinculo_fornecedor_produto',
        ['status'],
        schema='wms'
    )
    
    op.create_index(
        'idx_vinculo_fornecedor_produto_estatisticas',
        'vinculo_fornecedor_produto',
        ['tenant_id', 'status', 'vezes_utilizado'],
        schema='wms'
    )
    
    op.create_index(
        'idx_vinculo_fornecedor_produto_codigo_parcial',
        'vinculo_fornecedor_produto',
        ['codigo_fornecedor'],
        postgresql_using='btree',
        postgresql_ops={'codigo_fornecedor': 'varchar_pattern_ops'},
        schema='wms'
    )
    
    # Create trigger function
    op.execute("""
        CREATE OR REPLACE FUNCTION wms.fn_atualizar_timestamp_vinculo()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.atualizado_em = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger
    op.execute("""
        CREATE TRIGGER trg_vinculo_fornecedor_produto_atualizado
        BEFORE UPDATE ON wms.vinculo_fornecedor_produto
        FOR EACH ROW EXECUTE FUNCTION wms.fn_atualizar_timestamp_vinculo();
    """)
    
    # Create views
    op.execute("""
        CREATE OR REPLACE VIEW wms.v_vinculos_ativos AS
        SELECT 
            vf.id,
            vf.tenant_id,
            f.razao_social as fornecedor_nome,
            f.cnpj as fornecedor_cnpj,
            vf.codigo_fornecedor,
            p.nome as produto_nome,
            p.gtin as produto_gtin,
            vf.fator_conversao,
            vf.unidade_origem,
            vf.unidade_destino,
            vf.vezes_utilizado,
            vf.ultima_importacao,
            vf.peso_confianca,
            vf.criado_em
        FROM wms.vinculo_fornecedor_produto vf
        JOIN fornecedor f ON vf.fornecedor_id = f.id
        JOIN produto p ON vf.produto_id_interno = p.id
        WHERE vf.status = 'ativo'
          AND f.ativo = true
          AND p.ativo = true;
    """)
    
    op.execute("""
        CREATE OR REPLACE VIEW wms.v_estatisticas_vinculos_fornecedor AS
        SELECT 
            vf.tenant_id,
            vf.fornecedor_id,
            f.razao_social as fornecedor_nome,
            COUNT(*) as total_vinculos,
            COUNT(CASE WHEN vf.status = 'ativo' THEN 1 END) as vinculos_ativos,
            SUM(vf.vezes_utilizado) as total_utilizacoes,
            MAX(vf.vezes_utilizado) as max_utilizacoes,
            AVG(vf.peso_confianca) as avg_peso_confianca,
            MAX(vf.ultima_importacao) as ultima_importacao
        FROM wms.vinculo_fornecedor_produto vf
        JOIN fornecedor f ON vf.fornecedor_id = f.id
        GROUP BY vf.tenant_id, vf.fornecedor_id, f.razao_social
        ORDER BY total_utilizacoes DESC;
    """)
    
    # Create utility functions
    op.execute("""
        CREATE OR REPLACE FUNCTION wms.fn_buscar_vinculo_fornecedor(
            p_tenant_id UUID,
            p_fornecedor_id UUID,
            p_codigo_fornecedor VARCHAR(100)
        ) RETURNS TABLE (
            id UUID,
            produto_id_interno UUID,
            fator_conversao DECIMAL(15,6),
            unidade_origem VARCHAR(10),
            unidade_destino VARCHAR(10),
            status VARCHAR(20),
            peso_confianca DECIMAL(5,2)
        ) AS $$
        BEGIN
            RETURN QUERY
            SELECT 
                vf.id,
                vf.produto_id_interno,
                vf.fator_conversao,
                vf.unidade_origem,
                vf.unidade_destino,
                vf.status,
                vf.peso_confianca
            FROM wms.vinculo_fornecedor_produto vf
            WHERE vf.tenant_id = p_tenant_id
              AND vf.fornecedor_id = p_fornecedor_id
              AND vf.codigo_fornecedor = p_codigo_fornecedor
              AND vf.status = 'ativo'
            LIMIT 1;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE OR REPLACE FUNCTION wms.fn_registrar_utilizacao_vinculo(
            p_vinculo_id UUID,
            p_data_utilizacao TIMESTAMP DEFAULT NOW()
        ) RETURNS BOOLEAN AS $$
        BEGIN
            UPDATE wms.vinculo_fornecedor_produto 
            SET 
                vezes_utilizado = vezes_utilizado + 1,
                ultima_importacao = p_data_utilizacao,
                atualizado_em = NOW()
            WHERE id = p_vinculo_id AND status = 'ativo';
            
            RETURN FOUND;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Enable Row Level Security
    op.execute("ALTER TABLE wms.vinculo_fornecedor_produto ENABLE ROW LEVEL SECURITY")
    
    # Create RLS policy
    op.execute("""
        CREATE POLICY vinculos_tenant_isolation ON wms.vinculo_fornecedor_produto
        FOR ALL
        TO app_user
        USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
    """)


def downgrade() -> None:
    """Drop vinculo_fornecedor_produto table and related objects"""
    
    # Drop policies
    op.execute("DROP POLICY IF EXISTS vinculos_tenant_isolation ON wms.vinculo_fornecedor_produto")
    
    # Drop RLS
    op.execute("ALTER TABLE wms.vinculo_fornecedor_produto DISABLE ROW LEVEL SECURITY")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS wms.fn_registrar_utilizacao_vinculo(UUID, TIMESTAMP)")
    op.execute("DROP FUNCTION IF EXISTS wms.fn_buscar_vinculo_fornecedor(UUID, UUID, VARCHAR)")
    
    # Drop views
    op.execute("DROP VIEW IF EXISTS wms.v_estatisticas_vinculos_fornecedor")
    op.execute("DROP VIEW IF EXISTS wms.v_vinculos_ativos")
    
    # Drop trigger
    op.execute("DROP TRIGGER IF EXISTS trg_vinculo_fornecedor_produto_atualizado ON wms.vinculo_fornecedor_produto")
    
    # Drop trigger function
    op.execute("DROP FUNCTION IF EXISTS wms.fn_atualizar_timestamp_vinculo()")
    
    # Drop indexes
    op.drop_index('idx_vinculo_fornecedor_produto_codigo_parcial', schema='wms')
    op.drop_index('idx_vinculo_fornecedor_produto_estatisticas', schema='wms')
    op.drop_index('idx_vinculo_fornecedor_produto_status', schema='wms')
    op.drop_index('idx_vinculo_fornecedor_produto_tenant', schema='wms')
    op.drop_index('idx_vinculo_fornecedor_produto_produto', schema='wms')
    op.drop_index('idx_vinculo_fornecedor_produto_fornecedor_codigo', schema='wms')
    
    # Drop table
    op.drop_table('vinculo_fornecedor_produto', schema='wms')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS vinculo_status")
    op.execute("DROP TYPE IF EXISTS unidade_medida")
