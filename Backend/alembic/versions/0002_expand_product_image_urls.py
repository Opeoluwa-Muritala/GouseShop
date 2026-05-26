"""Expand product image URL columns

Revision ID: 0002_expand_product_image_urls
Revises: 0001_initial
Create Date: 2026-05-25 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_expand_product_image_urls"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("product_images") as batch_op:
        batch_op.alter_column("url", existing_type=sa.String(length=255), type_=sa.String(length=500))
        batch_op.alter_column("secure_url", existing_type=sa.String(length=255), type_=sa.String(length=500))


def downgrade() -> None:
    with op.batch_alter_table("product_images") as batch_op:
        batch_op.alter_column("secure_url", existing_type=sa.String(length=500), type_=sa.String(length=255))
        batch_op.alter_column("url", existing_type=sa.String(length=500), type_=sa.String(length=255))
