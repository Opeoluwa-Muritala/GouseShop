"""Add email verification flag

Revision ID: 0003_email_verification
Revises: 0002_expand_product_image_urls
Create Date: 2026-05-27 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "0003_email_verification"
down_revision = "0002_expand_product_image_urls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("is_email_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("users", "is_email_verified")
