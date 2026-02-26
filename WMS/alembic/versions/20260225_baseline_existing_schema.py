"""baseline_existing_schema

Revision ID: 20260225_baseline
Revises: 
Create Date: 2026-02-25 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20260225_baseline'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create baseline migration from existing schema"""
    
    # =====================================
    # Schema CORE
    # =====================================
    
    # 1) Cadastro mínimo
    op.create_table('item_master',
        sa.Column('item_master_id', sa.Text(), nullable=False),
        sa.Column('item_nome', sa.Text(), nullable=False),
        sa.Column('categoria_id', sa.Text(), nullable=True),
        sa.Column('classe_abc', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_by', sa.Text(), nullable=True),
        sa.Column('correlation_id', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('item_master_id')
    )
    
    op.create_table('sku',
        sa.Column('sku_id', sa.Text(), nullable=False),
        sa.Column('sku_codigo', sa.Text(), nullable=False),
        sa.Column('sku_nome', sa.Text(), nullable=False),
        sa.Column('item_master_id', sa.Text(), nullable=True),
        sa.Column('ean', sa.Text(), nullable=True),
        sa.Column('unidade_medida', sa.Text(), nullable=True),
        sa.Column('status_ativo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('variacao_volume', sa.Text(), nullable=True),
        sa.Column('variacao_cor', sa.Text(), nullable=True),
        sa.Column('variacao_tamanho', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_by', sa.Text(), nullable=True),
        sa.Column('correlation_id', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('sku_id'),
        sa.UniqueConstraint('sku_codigo'),
        sa.ForeignKeyConstraint(['item_master_id'], ['item_master.item_master_id'])
    )
    
    op.create_index('uq_sku_ean_not_null', 'sku', ['ean'], unique=True, 
                    postgresql_where=sa.text("ean IS NOT NULL"))
    
    op.create_table('endereco',
        sa.Column('endereco_codigo', sa.Text(), nullable=False),
        sa.Column('zona_codigo', sa.Text(), nullable=False),
        sa.Column('prateleira_codigo', sa.Text(), nullable=True),
        sa.Column('posicao_codigo', sa.Text(), nullable=True),
        sa.Column('tipo_endereco', sa.Text(), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('capacidade_maxima', sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('created_by', sa.Text(), nullable=True),
        sa.Column('correlation_id', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('endereco_codigo')
    )
    
    # 2) Estoque e movimentação
    op.create_table('saldo_estoque',
        sa.Column('saldo_estoque_id', sa.Text(), nullable=False),
        sa.Column('sku_id', sa.Text(), nullable=False),
        sa.Column('endereco_codigo', sa.Text(), nullable=False),
        sa.Column('saldo_disponivel', sa.Numeric(precision=18, scale=4), nullable=False, server_default='0'),
        sa.Column('saldo_avariado', sa.Numeric(precision=18, scale=4), nullable=False, server_default='0'),
        sa.Column('saldo_bloqueado', sa.Numeric(precision=18, scale=4), nullable=False, server_default='0'),
        sa.Column('saldo_total', sa.Numeric(precision=18, scale=4), nullable=False, server_default='0'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_by', sa.Text(), nullable=True),
        sa.Column('correlation_id', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('saldo_estoque_id'),
        sa.UniqueConstraint('sku_id', 'endereco_codigo', name='uq_saldo_sku_endereco'),
        sa.ForeignKeyConstraint(['sku_id'], ['sku.sku_id']),
        sa.ForeignKeyConstraint(['endereco_codigo'], ['endereco.endereco_codigo'])
    )
    
    op.create_index('ix_saldo_sku', 'saldo_estoque', ['sku_id'])
    op.create_index('ix_saldo_endereco', 'saldo_estoque', ['endereco_codigo'])
    
    op.create_table('movimentacao_estoque',
        sa.Column('movimentacao_id', sa.Text(), nullable=False),
        sa.Column('tipo_movimentacao', sa.Text(), nullable=False),
        sa.Column('sku_id', sa.Text(), nullable=False),
        sa.Column('quantidade', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('endereco_origem', sa.Text(), nullable=True),
        sa.Column('endereco_destino', sa.Text(), nullable=True),
        sa.Column('motivo', sa.Text(), nullable=True),
        sa.Column('actor_id', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.Text(), nullable=True),
        sa.Column('correlation_id', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('schema_version', sa.Text(), nullable=False, server_default='1.0'),
        sa.PrimaryKeyConstraint('movimentacao_id'),
        sa.ForeignKeyConstraint(['sku_id'], ['sku.sku_id']),
        sa.ForeignKeyConstraint(['endereco_origem'], ['endereco.endereco_codigo']),
        sa.ForeignKeyConstraint(['endereco_destino'], ['endereco.endereco_codigo'])
    )
    
    op.create_index('ix_movimentacao_sku', 'movimentacao_estoque', ['sku_id', 'created_at'])
    op.create_index('ix_movimentacao_corr', 'movimentacao_estoque', ['correlation_id'])
    
    # 3) Recebimento
    op.create_table('recebimento',
        sa.Column('recebimento_id', sa.Text(), nullable=False),
        sa.Column('nota_fiscal_numero', sa.Text(), nullable=False),
        sa.Column('fornecedor_id', sa.Text(), nullable=True),
        sa.Column('status_conferencia', sa.Text(), nullable=False),
        sa.Column('possui_avaria', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('divergencia_quantidade', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('actor_id', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.Text(), nullable=True),
        sa.Column('correlation_id', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('schema_version', sa.Text(), nullable=False, server_default='1.0'),
        sa.PrimaryKeyConstraint('recebimento_id'),
        sa.UniqueConstraint('nota_fiscal_numero', 'correlation_id', name='uq_recebimento_nota_corr')
    )
    
    op.create_index('ix_recebimento_nota', 'recebimento', ['nota_fiscal_numero'])
    
    op.create_table('recebimento_item',
        sa.Column('recebimento_item_id', sa.Text(), nullable=False),
        sa.Column('recebimento_id', sa.Text(), nullable=False),
        sa.Column('sku_id', sa.Text(), nullable=False),
        sa.Column('endereco_destino', sa.Text(), nullable=False),
        sa.Column('quantidade_esperada', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('quantidade_conferida', sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column('divergencia', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('classificacao_divergencia', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('correlation_id', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('recebimento_item_id'),
        sa.ForeignKeyConstraint(['recebimento_id'], ['recebimento.recebimento_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sku_id'], ['sku.sku_id']),
        sa.ForeignKeyConstraint(['endereco_destino'], ['endereco.endereco_codigo'])
    )
    
    op.create_index('ix_recebimento_item_rec', 'recebimento_item', ['recebimento_id'])
    op.create_index('ix_recebimento_item_sku', 'recebimento_item', ['sku_id'])
    
    # 4) Event store
    op.create_table('event_store',
        sa.Column('event_id', sa.Text(), nullable=False),
        sa.Column('event_name', sa.Text(), nullable=False),
        sa.Column('event_type', sa.Text(), nullable=False),
        sa.Column('bounded_context', sa.Text(), nullable=False, server_default='wms'),
        sa.Column('aggregate_type', sa.Text(), nullable=True),
        sa.Column('aggregate_id', sa.Text(), nullable=True),
        sa.Column('occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actor_id', sa.Text(), nullable=True),
        sa.Column('tenant_id', sa.Text(), nullable=True),
        sa.Column('correlation_id', sa.Text(), nullable=False),
        sa.Column('causation_id', sa.Text(), nullable=True),
        sa.Column('schema_version', sa.Text(), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('event_id')
    )
    
    op.create_index('ix_event_store_name_time', 'event_store', ['event_name', 'occurred_at'])
    op.create_index('ix_event_store_type_time', 'event_store', ['event_type', 'occurred_at'])
    op.create_index('ix_event_store_context_time', 'event_store', ['bounded_context', 'occurred_at'])
    op.create_index('ix_event_store_aggregate_time', 'event_store', ['aggregate_type', 'aggregate_id', 'occurred_at'])
    op.create_index('ix_event_store_corr', 'event_store', ['correlation_id'])
    
    # 5) Idempotência de comandos
    op.create_table('idempotency_command',
        sa.Column('idempotency_key', sa.Text(), nullable=False),
        sa.Column('operation_name', sa.Text(), nullable=False),
        sa.Column('correlation_id', sa.Text(), nullable=False),
        sa.Column('request_hash', sa.Text(), nullable=False),
        sa.Column('response_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.Text(), nullable=False, server_default='processing'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.PrimaryKeyConstraint('idempotency_key')
    )
    
    op.create_index('ix_idempotency_corr', 'idempotency_command', ['correlation_id'])


def downgrade() -> None:
    """Drop all baseline tables"""
    
    # Drop em ordem reversa das FKs
    op.drop_index('ix_idempotency_corr', table_name='idempotency_command')
    op.drop_table('idempotency_command')
    
    op.drop_index('ix_event_store_corr', table_name='event_store')
    op.drop_index('ix_event_store_aggregate_time', table_name='event_store')
    op.drop_index('ix_event_store_context_time', table_name='event_store')
    op.drop_index('ix_event_store_type_time', table_name='event_store')
    op.drop_index('ix_event_store_name_time', table_name='event_store')
    op.drop_table('event_store')
    
    op.drop_index('ix_recebimento_item_sku', table_name='recebimento_item')
    op.drop_index('ix_recebimento_item_rec', table_name='recebimento_item')
    op.drop_table('recebimento_item')
    
    op.drop_index('ix_recebimento_nota', table_name='recebimento')
    op.drop_table('recebimento')
    
    op.drop_index('ix_movimentacao_corr', table_name='movimentacao_estoque')
    op.drop_index('ix_movimentacao_sku', table_name='movimentacao_estoque')
    op.drop_table('movimentacao_estoque')
    
    op.drop_index('ix_saldo_endereco', table_name='saldo_estoque')
    op.drop_index('ix_saldo_sku', table_name='saldo_estoque')
    op.drop_table('saldo_estoque')
    
    op.drop_table('endereco')
    
    op.drop_index('uq_sku_ean_not_null', table_name='sku')
    op.drop_table('sku')
    
    op.drop_table('item_master')
