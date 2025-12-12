import time
from typing import Any, Optional, Union

from .base import BaseCacheClient


class InMemoryCacheClient(BaseCacheClient):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._store: dict[str, tuple[Any, Optional[float]]] = {}

    async def _get(self, key: str) -> Any:
        item = self._store.get(key)
        if item is None:
            return None

        value, expire = item
        if expire is not None and expire < time.time():
            await self._delete(key)
            return None

        return value

    async def _set(self, key: str, value: Any, ttl: Union[int, float, None]) -> None:
        expire = time.time() + ttl if ttl else None
        self._store[key] = (value, expire)

    async def _delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def _clear(self) -> None:
        namespace_prefix = f'{self.namespace}:'
        keys_to_delete = [key for key in self._store.keys() if key.startswith(namespace_prefix)]
        for key in keys_to_delete:
            del self._store[key]

    async def _exists(self, *keys: str) -> int:
        if not keys:
            return 0
        count = 0
        for key in keys:
            item = self._store.get(key)
            if item is not None:
                _, expire = item
                if expire is None or expire >= time.time():
                    count += 1
                else:
                    await self._delete(key)
        return count

    async def ping(self) -> bool:
        return True

    async def close(self) -> None:
        pass
