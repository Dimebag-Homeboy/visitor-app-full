"""empty message

Revision ID: adf23e639647
Revises: b3b6b3025e14
Create Date: 2026-06-02 13:48:46.322721

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'adf23e639647'
down_revision: Union[str, None] = 'b3b6b3025e14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
