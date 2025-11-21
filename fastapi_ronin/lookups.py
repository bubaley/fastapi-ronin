"""
Lookup implementations for FastAPI Ronin library.

Provides ready-to-use lookup classes for different lookup strategies.
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, ClassVar, Generic, Type
from uuid import UUID

from fastapi import Path
from pydantic import BaseModel

from fastapi_ronin.types import T


class BaseLookup(ABC, BaseModel, Generic[T]):
    """Abstract base class for lookup implementations."""

    lookup_url_kwarg: ClassVar[str] = 'item_id'
    value: T

    @classmethod
    @abstractmethod
    def build(cls, item_id: T = Path(..., alias=lookup_url_kwarg)) -> 'BaseLookup[T]':
        """Create lookup instance."""
        pass


def build_lookup_class(class_name: str, lookup_url_kwarg: str, value_type: Type[T]) -> Type[BaseLookup[T]]:
    def build(cls, value: value_type = Path(alias=lookup_url_kwarg)) -> BaseLookup[T]:  # type: ignore
        return cls(**{'value': value})

    class_dict = {
        '__annotations__': {'value': value_type},
        'lookup_url_kwarg': lookup_url_kwarg,
        'build': classmethod(build),
    }
    return type(class_name, (BaseLookup[T],), class_dict)


# Concrete implementations with type checking

if TYPE_CHECKING:
    IntegerLookup = type('IntegerLookup', (BaseLookup[int],), {})
    StringLookup = type('StringLookup', (BaseLookup[str],), {})
    UUIDLookup = type('UUIDLookup', (BaseLookup[UUID],), {})
else:
    IntegerLookup = build_lookup_class('IntegerLookup', 'item_id', int)
    StringLookup = build_lookup_class('StringLookup', 'item_id', str)
    UUIDLookup = build_lookup_class('StringLookup', 'item_id', UUID)
