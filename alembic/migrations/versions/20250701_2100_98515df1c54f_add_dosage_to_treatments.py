"""add_dosage_to_treatments

Revision ID: 98515df1c54f
Revises: cafafc906cf3
Create Date: 2025-07-01 21:00:08.763983

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '98515df1c54f'
down_revision = 'cafafc906cf3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('treatments', sa.Column('dosage', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('treatments', 'dosage')
    # ### end Alembic commands ###
