"""Remove start_time column from schedules

Revision ID: cbc8f2b8be6c
Revises: c1c18bc9e200
Create Date: 2025-09-06 17:56:38.956895

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cbc8f2b8be6c'
down_revision: Union[str, Sequence[str], None] = 'c1c18bc9e200'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # start_time 컬럼 삭제
    op.drop_column('schedules', 'start_time')


def downgrade():
    # start_time 컬럼 복원
    op.add_column('schedules', sa.Column('start_time', sa.DateTime(), nullable=False))

    # 데이터 복원
    op.execute("""
        UPDATE schedules 
        SET start_time = event_date + event_time
        WHERE event_date IS NOT NULL AND event_time IS NOT NULL
    """)
