from typing import Any, Optional, Union

from fastapi_ronin.defaults import CACHE_DEFAULT_NAMESPACE, NOT_SET
from fastapi_ronin.types import TTLType

from .cache_client_interface import CacheClientInterface
from .memory import InMemoryCacheClient
from .redis import RedisCacheClient


class CacheClient:
    def __init__(self):
        self._client: Optional[CacheClientInterface] = None
        self._initialized = False

    async def init(
        self,
        redis_url: Optional[str] = None,
        namespace: str = CACHE_DEFAULT_NAMESPACE,
        default_ttl: Union[int, float, None] = None,
    ) -> None:
        if self._initialized:
            return
        kwargs = {'namespace': namespace, 'default_ttl': default_ttl}
        if redis_url:
            self._client = RedisCacheClient(redis_url, **kwargs)
        else:
            self._client = InMemoryCacheClient(**kwargs)
        self._initialized = True

    async def close(self) -> None:
        if not self._initialized or not self._client:
            return

        await self._client.close()
        self._initialized = False
        self._client = None

    async def get(self, key: str) -> Any:
        client = self._ensure_initialized()
        return await client.get(key)

    async def set(self, key: str, value: Any, ttl: TTLType = NOT_SET) -> None:
        client = self._ensure_initialized()
        await client.set(key, value, ttl)

    async def delete(self, key: str) -> None:
        client = self._ensure_initialized()
        await client.delete(key)

    async def clear(self) -> None:
        client = self._ensure_initialized()
        await client.clear()

    async def exists(self, *keys: str) -> int:
        client = self._ensure_initialized()
        return await client.exists(*keys)

    async def ping(self) -> bool:
        client = self._ensure_initialized()
        return await client.ping()

    def is_initialized(self) -> bool:
        return self._initialized

    def _ensure_initialized(self) -> CacheClientInterface:
        if not self._initialized or not self._client:
            raise RuntimeError('Cache client is not initialized. Call await cache.init() before use.')
        return self._client


cache = CacheClient()
