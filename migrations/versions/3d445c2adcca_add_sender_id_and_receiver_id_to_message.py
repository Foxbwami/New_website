"""Add sender_id and receiver_id to Message

Revision ID: 3d445c2adcca
Revises: 2747f491169d
Create Date: 2025-07-25 16:52:23.811218

"""
from alembic import op
import sqlalchemy as sa
from werkzeug.security import generate_password_hash

# revision identifiers, used by Alembic.
revision = '3d445c2adcca'
down_revision = '2747f491169d'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add column as nullable
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('password_hash', sa.String(length=128), nullable=True))

    # 2. Set default hash for all users
    conn = op.get_bind()
    default_hash = generate_password_hash("changeme")
    conn.execute(
        sa.text("UPDATE user SET password_hash = :hash"),
        {"hash": default_hash}
    )

    # 3. Alter column to NOT NULL
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column('password_hash', nullable=False)

    # Add new fields to Message as needed (example, adjust as per your actual requirements)
    with op.batch_alter_table('message', schema=None) as batch_op:
        # Remove old fields if they exist (comment out if not needed)
        batch_op.drop_column('user_id')
        batch_op.drop_column('sender')
        batch_op.drop_column('created_at')
        batch_op.drop_column('is_read')
        # Add new fields
        batch_op.add_column(sa.Column('sender_id', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('receiver_id', sa.Integer(), nullable=False, server_default='0'))
        batch_op.add_column(sa.Column('is_admin', sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column('timestamp', sa.DateTime(), nullable=True))

    # Remove server defaults if needed (optional tidy-up)
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.alter_column('sender_id', server_default=None)
        batch_op.alter_column('receiver_id', server_default=None)
        batch_op.alter_column('is_admin', server_default=None)

def downgrade():
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_read', sa.BOOLEAN(), nullable=True))
        batch_op.add_column(sa.Column('created_at', sa.DATETIME(), nullable=True))
        batch_op.add_column(sa.Column('sender', sa.VARCHAR(length=50), nullable=True))
        batch_op.add_column(sa.Column('user_id', sa.VARCHAR(length=100), nullable=True))
        batch_op.drop_column('timestamp')
        batch_op.drop_column('is_admin')
        batch_op.drop_column('receiver_id')
        batch_op.drop_column('sender_id')

    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_column('password_hash')