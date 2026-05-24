import redis.asyncio as redis
from app.core.config import settings


class InMemoryRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._counters: dict[str, int] = {}

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self._store[key] = value
        return True

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def exists(self, key: str) -> int:
        return int(key in self._store)

    async def delete(self, key: str) -> int:
        existed = key in self._store
        self._store.pop(key, None)
        self._counters.pop(key, None)
        return int(existed)

    async def incr(self, key: str) -> int:
        self._counters[key] = self._counters.get(key, 0) + 1
        return self._counters[key]

    async def expire(self, key: str, seconds: int) -> bool:
        return True


redis_client = (
    InMemoryRedis()
    if settings.use_fake_external_services
    else redis.from_url(settings.redis_url, decode_responses=True)
)
