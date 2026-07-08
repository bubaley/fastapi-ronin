---
title: FastAPI Ronin Pagination — Page and Limit-Offset Pagination
description: Configure FastAPI Ronin list endpoints with disabled, page-number, or limit-offset pagination and include metadata through response wrappers.
keywords: FastAPI pagination, FastAPI Ronin, Tortoise ORM pagination, page number pagination, limit offset pagination
---

# Pagination

Pagination is configured on a ViewSet. Ronin parses FastAPI query parameters,
applies pagination to the Tortoise queryset, then optionally includes metadata
through a paginated response wrapper.

## Available Strategies

| Class | Query Parameters | Use When |
|-------|------------------|----------|
| `DisabledPagination` | none | You want the full result set. |
| `PageNumberPagination` | `page`, `size` | You want common page-based navigation. |
| `LimitOffsetPagination` | `offset`, `limit` | You want API/client-driven offsets. |

## Page Number Pagination

```python
from fastapi_ronin.pagination import PageNumberPagination
from fastapi_ronin.wrappers import PaginatedResponseDataWrapper


@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema

    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
```

```text
GET /companies/?page=2&size=20
```

Response with `PaginatedResponseDataWrapper`:

```json
{
  "data": [
    {"id": 21, "name": "Company 21"}
  ],
  "meta": {
    "page": 2,
    "size": 20,
    "total": 41,
    "pages": 3
  }
}
```

`size` is constrained to `1..100` by default.

## Limit/Offset Pagination

```python
from fastapi_ronin.pagination import LimitOffsetPagination


@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = LimitOffsetPagination
    list_wrapper = PaginatedResponseDataWrapper
```

```text
GET /companies/?offset=40&limit=20
```

Response metadata:

```json
{
  "data": [
    {"id": 41, "name": "Company 41"}
  ],
  "meta": {
    "offset": 40,
    "limit": 20,
    "total": 41
  }
}
```

## Disable Pagination

```python
from fastapi_ronin.pagination import DisabledPagination


@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = DisabledPagination
    list_wrapper = None
```

This returns a plain list unless you use a non-paginated list wrapper.

## Pagination in Custom Actions

Use the same pagination class as a FastAPI dependency:

```python
from fastapi import Depends
from fastapi_ronin.pagination import PageNumberPagination
from fastapi_ronin.wrappers import PaginatedResponseDataWrapper


@action(
    methods=['GET'],
    response_model=PaginatedResponseDataWrapper[CompanySchema, PageNumberPagination],
)
async def active(
    self,
    pagination: PageNumberPagination = Depends(PageNumberPagination.build),
):
    queryset = Company.filter(active=True)
    return await self.get_paginated_response(
        queryset=queryset,
        pagination=pagination,
        wrapper=PaginatedResponseDataWrapper,
    )
```

## Custom Pagination

Create a pagination class by extending `Pagination`.

```python
import math
from typing import Any

from fastapi import Query
from tortoise.queryset import QuerySet

from fastapi_ronin.pagination import Pagination
from fastapi_ronin.types import ModelType


class SmallPagePagination(Pagination[ModelType]):
    page: int = 1
    size: int = 5
    total: int = 0
    pages: int = 0

    @classmethod
    def build(
        cls,
        page: int = Query(1, ge=1),
        size: int = Query(5, ge=1, le=25),
    ) -> 'SmallPagePagination':
        return cls(page=page, size=size)

    def paginate(self, queryset: QuerySet[ModelType]) -> QuerySet[ModelType]:
        return queryset.offset((self.page - 1) * self.size).limit(self.size)

    async def fill_meta(self, queryset: QuerySet[ModelType], data: list[Any]) -> None:
        self.total = await queryset.count()
        self.pages = math.ceil(self.total / self.size) if self.size else 0
```

## Guidance

- Use `PageNumberPagination` for most public APIs.
- Use `LimitOffsetPagination` when clients need direct offset control.
- Use `DisabledPagination` only for small bounded collections.
- Pair paginated strategies with `PaginatedResponseDataWrapper` when clients need metadata.
