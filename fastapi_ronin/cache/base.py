from abc import ABC, abstractmethod
from typing import Any, Union

from fastapi_ronin.defaults import CACHE_DEFAULT_NAMESPACE, NOT_SET
from fastapi_ronin.types import TTLType

from .cache_client_interface import CacheClientInterface


class BaseCacheClient(CacheClientInterface, ABC):
    def __init__(
        self,
        namespace: str = CACHE_DEFAULT_NAMESPACE,
        default_ttl: Union[int, float, None] = None,
    ):
        self.namespace = namespace
        self.default_ttl = self._validate_ttl(default_ttl)

    async def get(self, key: str) -> Any:
        return await self._get(self._make_key(key))

    async def set(self, key: str, value: Any, ttl: TTLType = NOT_SET) -> None:
        await self._set(self._make_key(key), value, self._get_ttl(ttl))

    async def delete(self, key: str) -> None:
        await self._delete(self._make_key(key))

    async def clear(self) -> None:
        await self._clear()

    async def exists(self, *keys: str) -> int:
        if not keys:
            return 0
        return await self._exists(*self._make_keys(*keys))

    def _make_key(self, key: str) -> str:
        return f'{self.namespace}:{key}'

    def _make_keys(self, *keys: str) -> tuple[str, ...]:
        return tuple(self._make_key(key) for key in keys)

    def _get_ttl(self, ttl: TTLType) -> Union[int, float, None]:
        _ttl: Union[int, float, None] = None
        if ttl is NOT_SET:
            _ttl = self.default_ttl
        elif ttl is None or isinstance(ttl, (int, float)):
            _ttl = ttl
        else:
            raise ValueError(f'Invalid TTL: {ttl}')
        return self._validate_ttl(_ttl)

    def _validate_ttl(self, ttl: Union[int, float, None]) -> Union[int, float, None]:
        if ttl is not None and ttl <= 0:
            raise ValueError(f'TTL must be positive, got: {ttl} seconds')
        return ttl

    @abstractmethod
    async def _get(self, key: str) -> Any:
        pass

    @abstractmethod
    async def _set(self, key: str, value: Any, ttl: Union[int, float, None]) -> None:
        pass

    @abstractmethod
    async def _delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def _clear(self) -> None:
        pass

    @abstractmethod
    async def _exists(self, *keys: str) -> int:
        pass

    @abstractmethod
    async def ping(self) -> bool:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass
