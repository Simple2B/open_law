"""entity_id

Revision ID: ad0ed27f417f
Revises: 3d45df38ffa9
Create Date: 2023-06-12 12:03:44.954134

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "ad0ed27f417f"
down_revision = "3d45df38ffa9"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.add_column(sa.Column("entity_id", sa.Integer(), nullable=False))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("notifications", schema=None) as batch_op:
        batch_op.drop_column("entity_id")

    # ### end Alembic commands ###
