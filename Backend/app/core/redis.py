import redis.asyncio as redis
from time import monotonic
from typing import AsyncIterator

from app.core.config import settings


class InMemoryRedis:
    def __init__(self) -> None:
        self._store: dict[str, str] = {}
        self._counters: dict[str, int] = {}
        self._expires_at: dict[str, float] = {}

    def _is_expired(self, key: str) -> bool:
        expires_at = self._expires_at.get(key)
        if expires_at is None or expires_at > monotonic():
            return False
        self._store.pop(key, None)
        self._counters.pop(key, None)
        self._expires_at.pop(key, None)
        return True

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        self._store[key] = value
        if ex is not None:
            self._expires_at[key] = monotonic() + ex
        else:
            self._expires_at.pop(key, None)
        return True

    async def get(self, key: str) -> str | None:
        if self._is_expired(key):
            return None
        return self._store.get(key)

    async def exists(self, key: str) -> int:
        if self._is_expired(key):
            return 0
        return int(key in self._store or key in self._counters)

    async def delete(self, key: str) -> int:
        existed = key in self._store or key in self._counters
        self._store.pop(key, None)
        self._counters.pop(key, None)
        self._expires_at.pop(key, None)
        return int(existed)

    async def incr(self, key: str) -> int:
        self._is_expired(key)
        self._counters[key] = self._counters.get(key, 0) + 1
        return self._counters[key]

    async def expire(self, key: str, seconds: int) -> bool:
        if self._is_expired(key):
            return False
        if key not in self._store and key not in self._counters:
            return False
        self._expires_at[key] = monotonic() + seconds
        return True

    async def delete_prefix(self, prefix: str) -> int:
        keys = [
            key
            for key in set(self._store) | set(self._counters) | set(self._expires_at)
            if key.startswith(prefix)
        ]
        for key in keys:
            await self.delete(key)
        return len(keys)


class UpstashRedisAdapter:
    def __init__(self, url: str, token: str) -> None:
        try:
            from upstash_redis.asyncio import Redis
        except ImportError as exc:
            raise RuntimeError("Install upstash-redis to use Upstash Redis") from exc

        self._client = Redis(url=url, token=token)

    async def set(self, key: str, value: str, ex: int | None = None) -> bool:
        if ex is None:
            result = await self._client.set(key, value)
        else:
            result = await self._client.set(key, value, ex=ex)
        return bool(result)

    async def get(self, key: str) -> str | None:
        return await self._client.get(key)

    async def exists(self, key: str) -> int:
        result = await self._client.exists(key)
        return int(result or 0)

    async def delete(self, *keys: str) -> int:
        if not keys:
            return 0
        result = await self._client.delete(*keys)
        return int(result or 0)

    async def incr(self, key: str) -> int:
        result = await self._client.incr(key)
        return int(result)

    async def expire(self, key: str, seconds: int) -> bool:
        result = await self._client.expire(key, seconds)
        return bool(result)

    async def scan_iter(self, match: str) -> AsyncIterator[str]:
        cursor = 0
        while True:
            cursor, keys = await self._client.scan(cursor=cursor, match=match)
            for key in keys:
                yield key
            if int(cursor) == 0:
                break


def redis_key(key: str) -> str:
    return f"{settings.redis_key_prefix}{key}"


async def delete_keys_with_prefix(prefix: str) -> int:
    if not prefix:
        raise ValueError("Redis cleanup prefix is required")
    if isinstance(redis_client, InMemoryRedis):
        return await redis_client.delete_prefix(prefix)

    deleted = 0
    batch: list[str] = []
    async for key in redis_client.scan_iter(match=f"{prefix}*"):
        batch.append(key)
        if len(batch) >= 100:
            deleted += await redis_client.delete(*batch)
            batch.clear()
    if batch:
        deleted += await redis_client.delete(*batch)
    return deleted


redis_client = (
    InMemoryRedis()
    if settings.use_fake_redis
    else (
        UpstashRedisAdapter(settings.upstash_redis_rest_url, settings.upstash_redis_rest_token)
        if settings.upstash_redis_rest_url and settings.upstash_redis_rest_token
        else redis.from_url(settings.redis_url, decode_responses=True)
    )
)
