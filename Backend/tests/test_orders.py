import asyncio

import pytest

from app.core.database import async_session
from app.models.cart import Cart, CartItem
from app.models.catalog import Product, Variant
from app.models.user import Address, User
from app.services.auth_service import build_tokens

pytestmark = pytest.mark.db


async def _create_checkout_fixture(email: str, quantity: int = 1, stock_qty: int = 3):
    async with async_session() as session:
        user = User(email=email, password_hash="hash", is_email_verified=True)
        other_user = User(email=f"other-{email}", password_hash="hash", is_email_verified=True)
        session.add_all([user, other_user])
        await session.flush()

        address = Address(
            user_id=user.id,
            label="Home",
            full_name="Test User",
            phone="123",
            country="NG",
            state="Lagos",
            city="Lagos",
            street="1 Test Street",
            postal_code="100001",
        )
        other_address = Address(
            user_id=other_user.id,
            label="Other",
            full_name="Other User",
            phone="456",
            country="NG",
            state="Lagos",
            city="Lagos",
            street="2 Test Street",
            postal_code="100002",
        )
        product = Product(name=f"Product {email}", slug=f"product-{email}", price=1000)
        session.add_all([address, other_address, product])
        await session.flush()

        variant = Variant(product_id=product.id, sku=f"SKU-{email}", stock_qty=stock_qty, reserved_qty=0)
        cart = Cart(user_id=user.id)
        session.add_all([variant, cart])
        await session.flush()

        cart_item = CartItem(cart_id=cart.id, variant_id=variant.id, quantity=quantity, price_snapshot=1000)
        session.add(cart_item)
        await session.commit()

        token = build_tokens(user)["access_token"]
        return token, address.id, other_address.id


def test_checkout_address_and_inventory_rules(client):
    token, address_id, other_address_id = asyncio.run(_create_checkout_fixture("order@example.com"))
    success = client.post(
        "/api/v1/orders/",
        json={"address_id": address_id, "notes": "Leave at desk"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert success.status_code == 200
    assert success.json()["address_id"] == address_id
    assert success.json()["notes"] == "Leave at desk"

    token, _, other_address_id = asyncio.run(_create_checkout_fixture("bad-address@example.com"))
    wrong_address = client.post(
        "/api/v1/orders/",
        json={"address_id": other_address_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert wrong_address.status_code == 400
    assert wrong_address.json()["detail"] == "Shipping address not found"

    token, address_id, _ = asyncio.run(_create_checkout_fixture("stock@example.com", quantity=2, stock_qty=1))
    insufficient_stock = client.post(
        "/api/v1/orders/",
        json={"address_id": address_id},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert insufficient_stock.status_code == 400
    assert insufficient_stock.json()["detail"] == "Insufficient inventory"
