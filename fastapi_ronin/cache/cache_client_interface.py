from abc import ABC, abstractmethod
from typing import Any

from fastapi_ronin.types import TTLType


class CacheClientInterface(ABC):
    @abstractmethod
    async def get(self, key: str) -> Any:
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: TTLType) -> None:
        pass

    @abstractmethod
    async def delete(self, key: str) -> None:
        pass

    @abstractmethod
    async def clear(self) -> None:
        pass

    @abstractmethod
    async def exists(self, *keys: str) -> int:
        pass

    @abstractmethod
    async def ping(self) -> bool:
        pass

    @abstractmethod
    async def close(self) -> None:
        pass
