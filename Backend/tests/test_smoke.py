import asyncio

from app.core.redis import InMemoryRedis


async def _assert_redis_expiry_behaviour():
    client = InMemoryRedis()
    await client.set("key", "value", ex=1)
    assert await client.get("key") == "value"
    client._expires_at["key"] = 0
    assert await client.get("key") is None
    assert await client.exists("key") == 0

    assert await client.incr("counter") == 1
    assert await client.expire("counter", 1) is True
    assert await client.exists("counter") == 1
    client._expires_at["counter"] = 0
    assert await client.exists("counter") == 0
    assert await client.incr("counter") == 1


def test_health_guest_cart_and_redis(client):
    health = client.get("/api/v1/health")
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}

    cart = client.get("/api/v1/cart/")
    assert cart.status_code == 400

    asyncio.run(_assert_redis_expiry_behaviour())
