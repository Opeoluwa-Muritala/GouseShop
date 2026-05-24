"""Initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-24 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True, index=True),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.Enum("user", "admin", name="userrole", native_enum=False), nullable=False, server_default="user"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("banner_url", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "collections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("banner_url", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "fabrics",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=140), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("banner_url", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "addresses",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("label", sa.String(length=100), nullable=False),
        sa.Column("full_name", sa.String(length=160), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=False),
        sa.Column("country", sa.String(length=80), nullable=False),
        sa.Column("state", sa.String(length=80), nullable=False),
        sa.Column("city", sa.String(length=80), nullable=False),
        sa.Column("street", sa.String(length=255), nullable=False),
        sa.Column("postal_code", sa.String(length=30), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Integer(), nullable=False),
        sa.Column("compare_at_price", sa.Integer(), nullable=True),
        sa.Column("category_id", sa.Integer(), sa.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True),
        sa.Column("fabric_id", sa.Integer(), sa.ForeignKey("fabrics.id", ondelete="SET NULL"), nullable=True),
        sa.Column("gender", sa.Enum("women", "men", "unisex", "kids", name="gender", native_enum=False), nullable=True),
        sa.Column("status", sa.Enum("active", "draft", "archived", "coming_soon", "pre_order", name="productstatus", native_enum=False), nullable=False, server_default="active"),
        sa.Column("is_featured", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_bestseller", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_sale", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_new_arrival", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_coming_soon", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("is_preorder", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("search_vector", sa.Text(), nullable=True),
    )

    op.create_table(
        "product_collections",
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("collection_id", sa.Integer(), sa.ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True),
    )

    op.create_table(
        "product_images",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("url", sa.String(length=255), nullable=False),
        sa.Column("secure_url", sa.String(length=255), nullable=True),
        sa.Column("public_id", sa.String(length=255), nullable=True),
        sa.Column("alt", sa.String(length=255), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("width", sa.Integer(), nullable=True),
        sa.Column("height", sa.Integer(), nullable=True),
        sa.Column("format", sa.String(length=50), nullable=True),
        sa.Column("resource_type", sa.String(length=50), nullable=True),
    )

    op.create_table(
        "variants",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sku", sa.String(length=120), nullable=False, unique=True),
        sa.Column("size", sa.String(length=50), nullable=True),
        sa.Column("color", sa.String(length=80), nullable=True),
        sa.Column("color_hex", sa.String(length=7), nullable=True),
        sa.Column("stock_qty", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("reserved_qty", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("additional_price", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "carts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("session_id", sa.String(length=255), nullable=True, unique=True),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "cart_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("cart_id", sa.Integer(), sa.ForeignKey("carts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("variants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("price_snapshot", sa.Integer(), nullable=False),
        sa.UniqueConstraint("cart_id", "variant_id", name="uq_cart_variant"),
    )

    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.Enum("pending_payment", "paid", "processing", "shipped", "delivered", "cancelled", "refunded", name="orderstatus", native_enum=False), nullable=False, server_default="pending_payment"),
        sa.Column("subtotal", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("shipping_fee", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("discount", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("address_id", sa.Integer(), sa.ForeignKey("addresses.id", ondelete="SET NULL"), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("tracking_number", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "order_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("variants.id", ondelete="SET NULL"), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Integer(), nullable=False),
        sa.Column("product_snapshot", sa.JSON(), nullable=True),
    )

    op.create_table(
        "payments",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("order_id", sa.Integer(), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("provider", sa.Enum("paystack", "flutterwave", "fake", name="paymentprovider", native_enum=False), nullable=False),
        sa.Column("provider_reference", sa.String(length=160), nullable=False, unique=True),
        sa.Column("provider_checkout_url", sa.String(length=500), nullable=True),
        sa.Column("amount", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=10), nullable=False, server_default="USD"),
        sa.Column("status", sa.Enum("pending", "initialized", "paid", "failed", "cancelled", "refunded", name="paymentstatus", native_enum=False), nullable=False, server_default="pending"),
        sa.Column("provider_response", sa.JSON(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "wishlists",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "product_id", name="uq_wishlist_user_product"),
    )

    op.create_table(
        "reviews",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=True),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("user_id", "product_id", name="uq_review_user_product"),
    )

    op.create_table(
        "waitlist",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("products.id", ondelete="CASCADE"), nullable=True),
        sa.Column("variant_id", sa.Integer(), sa.ForeignKey("variants.id", ondelete="CASCADE"), nullable=True),
        sa.Column("notified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("email", "variant_id", name="uq_waitlist_email_variant"),
    )

    op.create_table(
        "newsletter_subscribers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table(
        "email_logs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("recipient", sa.String(length=255), nullable=False),
        sa.Column("subject", sa.String(length=255), nullable=False),
        sa.Column("template", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="pending"),
        sa.Column("provider_message_id", sa.String(length=160), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("email_logs")
    op.drop_table("newsletter_subscribers")
    op.drop_table("waitlist")
    op.drop_table("reviews")
    op.drop_table("wishlists")
    op.drop_table("payments")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("cart_items")
    op.drop_table("carts")
    op.drop_table("variants")
    op.drop_table("product_images")
    op.drop_table("product_collections")
    op.drop_table("products")
    op.drop_table("addresses")
    op.drop_table("fabrics")
    op.drop_table("collections")
    op.drop_table("categories")
    op.drop_table("users")
