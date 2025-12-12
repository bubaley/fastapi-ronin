import json
from typing import Any, Union

from .base import BaseCacheClient

try:
    from redis.asyncio import Redis  # type: ignore
except ImportError:
    Redis = None


class RedisCacheClient(BaseCacheClient):
    def __init__(self, url: str, **kwargs):
        super().__init__(**kwargs)
        if Redis is None:
            raise ImportError('Redis is not installed. Install it with: pip install fastapi-ronin[redis]')
        self.redis = Redis.from_url(url, encoding='utf-8', decode_responses=True)

    async def _get(self, key: str) -> Any:
        raw = await self.redis.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return None

    async def _set(self, key: str, value: Any, ttl: Union[int, float, None]) -> None:
        try:
            serialized = json.dumps(value)
        except (TypeError, ValueError) as e:
            raise ValueError(f'Value cannot be serialized to JSON: {e}') from e
        await self.redis.set(key, serialized, px=None if ttl is None else int(ttl * 1000))

    async def _delete(self, key: str) -> None:
        await self.redis.delete(key)

    async def _clear(self) -> None:
        pattern = self._make_key('*')
        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=500)
            if keys:
                await self.redis.delete(*keys)
            if cursor == 0:
                break

    async def _exists(self, *keys: str) -> int:
        if not keys:
            return 0
        result = await self.redis.exists(*keys)
        return int(result)

    async def ping(self) -> bool:
        try:
            await self.redis.ping()  # type: ignore
            return True
        except Exception:
            return False

    async def close(self) -> None:
        await self.redis.aclose()
