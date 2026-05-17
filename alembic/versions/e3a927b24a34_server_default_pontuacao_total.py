"""server_default_pontuacao_total

Revision ID: e3a927b24a34
Revises: a4a618c0a0da
Create Date: 2026-05-17 02:45:47.071312

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e3a927b24a34'
down_revision: Union[str, None] = 'a4a618c0a0da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_colum('usuario', 'pontuacao_total', server_default='0')


def downgrade() -> None:
    op.alter_colum('usuario', 'pontuacao_total', server_default=None)
