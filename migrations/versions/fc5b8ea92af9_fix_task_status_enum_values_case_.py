"""Fix task status enum values case mismatch

Revision ID: fc5b8ea92af9
Revises: 
Create Date: 2025-09-20 11:31:00.008570

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fc5b8ea92af9'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Update existing 'pending' values to 'Pending' to match the model definition
    op.execute("UPDATE task SET status = 'Pending' WHERE status = 'pending'")
    op.execute("UPDATE task SET status = 'In Progress' WHERE status = 'in progress'")
    op.execute("UPDATE task SET status = 'Completed' WHERE status = 'completed'")


def downgrade():
    # Revert back to lowercase values
    op.execute("UPDATE task SET status = 'pending' WHERE status = 'Pending'")
    op.execute("UPDATE task SET status = 'in progress' WHERE status = 'In Progress'")
    op.execute("UPDATE task SET status = 'completed' WHERE status = 'Completed'")
