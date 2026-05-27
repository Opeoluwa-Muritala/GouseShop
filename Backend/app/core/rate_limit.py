from fastapi import HTTPException, Request, status

from app.core.redis import redis_client, redis_key


def rate_limit(name: str, limit: int, window_seconds: int):
    async def dependency(request: Request) -> None:
        client = request.client.host if request.client else "unknown"
        key = redis_key(f"rate:{name}:{client}")
        count = await redis_client.incr(key)
        if count == 1:
            await redis_client.expire(key, window_seconds)
        if count > limit:
            raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded")

    return dependency
