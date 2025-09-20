"""fix: ledger created_at server_default 추가

Revision ID: 20250920_fix_created_at
Revises: 7ff6b21c9f02
Create Date: 2025-09-20 18:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20250920_fix_created_at'
down_revision: Union[str, Sequence[str], None] = '7ff6b21c9f02'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - ledgers.created_at에 server_default 추가."""
    
    # 1. ledgers.created_at에 server_default 추가
    op.alter_column('ledgers', 'created_at',
                   existing_type=sa.DateTime(timezone=True),
                   server_default=sa.text('now()'),
                   nullable=True)
    
    # 2. 기존 NULL 값들을 현재 시간으로 업데이트
    op.execute("""
        UPDATE ledgers 
        SET created_at = now()
        WHERE created_at IS NULL
    """)


def downgrade() -> None:
    """Downgrade schema - server_default 제거."""
    
    # server_default 제거
    op.alter_column('ledgers', 'created_at',
                   existing_type=sa.DateTime(timezone=True),
                   server_default=None,
                   nullable=True)
