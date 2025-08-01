"""add_enddate_to_condition

Revision ID: 0b23860a8fe9
Revises: 3fa18fb7b87b
Create Date: 2025-07-02 18:50:57.898604

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0b23860a8fe9'
down_revision = '3fa18fb7b87b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('conditions', sa.Column('endDate', sa.Date(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('conditions', 'endDate')
    # ### end Alembic commands ###
