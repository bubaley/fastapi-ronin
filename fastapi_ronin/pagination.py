"""
Concrete pagination implementations for FastAPI Ronin library.

Provides ready-to-use pagination classes for different pagination strategies.
"""

import math
from abc import ABC, abstractmethod
from typing import Any, Generic, List

from fastapi import Query
from pydantic import BaseModel
from tortoise.queryset import QuerySet

from fastapi_ronin.types import ModelType


class Pagination(ABC, BaseModel, Generic[ModelType]):
    """Abstract base class for pagination implementations."""

    @classmethod
    @abstractmethod
    def build(cls, **kwargs) -> 'Pagination':
        """Create pagination instance from query parameters."""
        pass

    @abstractmethod
    def paginate(self, queryset: QuerySet[ModelType]) -> QuerySet[ModelType]:
        """Apply pagination to a queryset."""
        pass

    async def fill_meta(self, queryset: QuerySet[ModelType], data: List[Any]) -> None:
        """Fill pagination metadata (like total count, pages, etc.)."""
        pass


# Concrete implementations


class DisabledPagination(Pagination[ModelType]):
    """Pagination class that disables pagination."""

    @classmethod
    def build(cls) -> 'DisabledPagination':
        return cls()

    def paginate(self, queryset: QuerySet[ModelType]) -> QuerySet[ModelType]:
        return queryset


class LimitOffsetPagination(Pagination[ModelType]):
    """Limit/Offset based pagination."""

    offset: int = 0
    limit: int = 10
    total: int = 0

    @classmethod
    def build(
        cls,
        offset: int = Query(0, ge=0, description='Number of records to skip'),
        limit: int = Query(10, ge=1, le=100, description='Number of records to return'),
    ) -> 'LimitOffsetPagination':
        return cls(offset=offset, limit=limit)

    def paginate(self, queryset: QuerySet[ModelType]) -> QuerySet[ModelType]:
        return queryset.offset(self.offset).limit(self.limit)

    async def fill_meta(self, queryset: QuerySet[ModelType], data: List[Any]) -> None:
        self.total = await queryset.count()


class PageNumberPagination(Pagination[ModelType]):
    """Page number based pagination."""

    page: int = 1
    size: int = 10
    total: int = 0
    pages: int = 0

    @classmethod
    def build(
        cls,
        page: int = Query(1, ge=1, description='Page number'),
        size: int = Query(10, ge=1, le=100, description='Number of records per page'),
    ) -> 'PageNumberPagination':
        return cls(page=page, size=size)

    def paginate(self, queryset: QuerySet[ModelType]) -> QuerySet[ModelType]:
        offset = (self.page - 1) * self.size
        return queryset.offset(offset).limit(self.size)

    async def fill_meta(self, queryset: QuerySet[ModelType], data: List[Any]) -> None:
        self.total = await queryset.count()
        self.pages = math.ceil(self.total / self.size) if self.size > 0 else 0
