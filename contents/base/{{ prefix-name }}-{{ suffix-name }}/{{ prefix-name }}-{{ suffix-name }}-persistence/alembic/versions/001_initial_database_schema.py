"""Initial database schema

Revision ID: 001
Revises: 
Create Date: 2025-06-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial database schema."""
    # Create {{ prefix_name }} table
    op.create_table(
        '{{ prefix_name }}',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, default='ACTIVE'),
        sa.Column('metadata_', postgresql.JSONB(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False, default=1),
    )
    
    # Create indexes for performance
    op.create_index('ix_{{ prefix_name }}_name', '{{ prefix_name }}', ['name'])
    op.create_index('ix_{{ prefix_name }}_status', '{{ prefix_name }}', ['status'])
    op.create_index('ix_{{ prefix_name }}_created_at', '{{ prefix_name }}', ['created_at'])
    op.create_index('ix_{{ prefix_name }}_updated_at', '{{ prefix_name }}', ['updated_at'])
    
    # Create unique constraint on name
    op.create_unique_constraint('uq_{{ prefix_name }}_name', '{{ prefix_name }}', ['name'])


def downgrade() -> None:
    """Drop initial database schema."""
    op.drop_table('{{ prefix_name }}')