import pytest

from app.core import redis as redis_module
from app.core.redis import UpstashRedisAdapter


class FakeUpstashClient:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.expires: dict[str, int] = {}

    async def set(self, key, value, ex=None):
        self.values[key] = value
        if ex is not None:
            self.expires[key] = ex
        return True

    async def get(self, key):
        return self.values.get(key)

    async def exists(self, key):
        return int(key in self.values)

    async def delete(self, *keys):
        deleted = 0
        for key in keys:
            if key in self.values:
                deleted += 1
                self.values.pop(key, None)
                self.expires.pop(key, None)
        return deleted

    async def incr(self, key):
        self.values[key] = str(int(self.values.get(key, "0")) + 1)
        return int(self.values[key])

    async def expire(self, key, seconds):
        if key not in self.values:
            return False
        self.expires[key] = seconds
        return True

    async def scan(self, cursor=0, match=None):
        prefix = (match or "").removesuffix("*")
        keys = [key for key in self.values if key.startswith(prefix)]
        return 0, keys


@pytest.mark.asyncio
async def test_upstash_adapter_matches_app_redis_interface(monkeypatch):
    adapter = object.__new__(UpstashRedisAdapter)
    adapter._client = FakeUpstashClient()

    assert await adapter.set("test:key", "value", ex=30) is True
    assert adapter._client.expires["test:key"] == 30
    assert await adapter.get("test:key") == "value"
    assert await adapter.exists("test:key") == 1
    assert await adapter.incr("test:counter") == 1
    assert await adapter.expire("test:counter", 60) is True

    keys = [key async for key in adapter.scan_iter(match="test:*")]
    assert set(keys) == {"test:key", "test:counter"}

    monkeypatch.setattr(redis_module, "redis_client", adapter)
    deleted = await redis_module.delete_keys_with_prefix("test:")
    assert deleted == 2
    assert await adapter.exists("test:key") == 0
