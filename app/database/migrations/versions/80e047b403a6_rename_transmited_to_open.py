"""rename TRANSMITED to OPEN

Revision ID: 80e047b403a6
Revises: d08ecf326c60
Create Date: 2025-12-02 14:49:42.327847

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '80e047b403a6'
down_revision = 'd08ecf326c60'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE orderstatus RENAME VALUE 'TRANSMITTED' TO 'OPEN'")


def downgrade() -> None:
    op.execute("ALTER TYPE orderstatus RENAME VALUE 'OPEN' TO 'TRANSMITTED'")
