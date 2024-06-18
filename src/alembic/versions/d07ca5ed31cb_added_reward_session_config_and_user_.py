"""Added reward_session_config and user_points_history table

Revision ID: d07ca5ed31cb
Revises: 33e9f6b924d5
Create Date: 2024-06-18 08:30:58.272621

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'd07ca5ed31cb'
down_revision: Union[str, None] = '33e9f6b924d5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('reward_session_config',
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('session_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('start_delay_days', sa.Integer(), nullable=False),
    sa.Column('max_points', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['session_id'], ['reward_sessions.session_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('user_points_history',
    sa.Column('id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('user_points_id', sqlmodel.sql.sqltypes.GUID(), nullable=False),
    sa.Column('point', sa.Float(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['user_points_id'], ['user_points.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('reward_sessions', sa.Column('update_date', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('reward_sessions', 'update_date')
    op.drop_table('user_points_history')
    op.drop_table('reward_session_config')
    # ### end Alembic commands ###
