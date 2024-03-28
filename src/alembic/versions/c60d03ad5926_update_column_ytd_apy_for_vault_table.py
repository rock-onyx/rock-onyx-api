"""update column ytd_apy for vault table

Revision ID: c60d03ad5926
Revises: a972614aaed9
Create Date: 2024-03-28 02:22:45.689266

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c60d03ad5926'
down_revision: Union[str, None] = 'a972614aaed9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('vaults', sa.Column('ytd_apy', sa.Float(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('vaults', 'ytd_apy')
    # ### end Alembic commands ###