---
title: FastAPI Pagination — Efficient Data Management with FastAPI Ronin
description: Improve your FastAPI application's performance with Mason's advanced API pagination. Supports multiple strategies like limit-offset and cursor-based pagination for scalable REST APIs.
keywords: FastAPI pagination, API pagination, Django REST Framework pagination, REST API performance, limit-offset pagination, cursor pagination, FastAPI Ronin, scalable APIs, data pagination, Python REST API
---

# API Pagination: Efficient Data Management with FastAPI Ronin

FastAPI Ronin provides multiple pagination strategies to efficiently handle large datasets. Each strategy is designed for different use cases and offers various trade-offs between performance, consistency, and user experience.

## Overview

FastAPI Ronin supports four pagination strategies:

1. **DisabledPagination** - No pagination (returns all results)
2. **LimitOffsetPagination** - Traditional limit/offset pagination
3. **PageNumberPagination** - Page-based pagination
4. **CursorPagination** - Cursor-based pagination for consistent results

## Pagination in ViewSets

Set pagination on your ViewSet class:

```python
from fastapi_ronin.pagination import PageNumberPagination
from fastapi_ronin.viewsets import ModelViewSet
from fastapi_ronin.wrappers import PaginatedResponseDataWrapper

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema

    # Configure pagination
    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper  # Include pagination metadata
```

## Disabled Pagination

Use when you want to return all results without pagination:

```python
from fastapi_ronin.pagination import DisabledPagination

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = DisabledPagination
    list_wrapper = None  # No pagination metadata needed
```

**Response:**
```json
[
  {"id": 1, "name": "Company A"},
  {"id": 2, "name": "Company B"},
  {"id": 3, "name": "Company C"}
]
```

## Page Number Pagination

The most common pagination strategy, using page numbers and page size:

```python
from fastapi_ronin.pagination import PageNumberPagination

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = PageNumberPagination  # Default: 10 items per page
```

**Query Parameters**

- `page` (int, default=1): Page number to retrieve
- `size` (int, default=10, max=100): Number of items per page

**API Usage**

```bash
GET /companies/?page=2&size=5
```

**Response Format**

```json
{
  "data": [
    {"id": 6, "name": "Company F"},
    {"id": 7, "name": "Company G"},
    {"id": 8, "name": "Company H"},
    {"id": 9, "name": "Company I"},
    {"id": 10, "name": "Company J"}
  ],
  "meta": {
    "page": 2,
    "size": 5,
    "total": 25,
    "pages": 5
  }
}
```

**Metadata Fields**

| Field | Description |
|-------|-------------|
| `page` | Current page number |
| `size` | Number of items per page |
| `total` | Total number of items |
| `pages` | Total number of pages |

## Limit/Offset Pagination

Traditional pagination using offset and limit:

```python
from fastapi_ronin.pagination import LimitOffsetPagination

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = LimitOffsetPagination
```

**Query Parameters**

- `offset` (int, default=0): Number of items to skip
- `limit` (int, default=10, max=100): Number of items to return

**API Usage**

```bash
GET /companies/?offset=10&limit=5
```

**Response Format**

```json
{
  "data": [
    {"id": 11, "name": "Company K"},
    {"id": 12, "name": "Company L"},
    {"id": 13, "name": "Company M"},
    {"id": 14, "name": "Company N"},
    {"id": 15, "name": "Company O"}
  ],
  "meta": {
    "offset": 10,
    "limit": 5,
    "total": 25
  }
}
```

## Pagination in Custom Actions

Use pagination in your custom actions:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = PageNumberPagination

    @action(methods=["GET"], response_model=List[ProjectReadSchema])
    async def paginated_list(self, pagination: PageNumberPagination = Depends(PageNumberPagination.build)):
        queryset = self.get_queryset()
        return await self.get_paginated_response(queryset=queryset, pagination=pagination)

    @action(methods=["GET"], response_model=PaginatedResponseDataWrapper[ProjectReadSchema, PageNumberPagination[Company]])
    async def wrapped_paginated_list(self, pagination: PageNumberPagination = Depends(PageNumberPagination.build)):
        queryset = self.get_queryset()
        return await self.get_paginated_response(queryset=queryset, pagination=pagination, wrapper=PaginatedResponseDataWrapper)
```
## Override Pagination

You can create a custom pagination class by inheriting from the `Pagination` abstract base class and implementing the required abstract methods. This allows you to define a tailored pagination strategy to meet specific requirements, such as custom query parameters or pagination logic.

### Expansion of existing
```python
from fastapi_ronin.pagination import PageNumberPagination
from fastapi import Query

from fastapi_ronin.types import ModelType


class CustomPageNumberPagination(PageNumberPagination[ModelType]):
    """Custom pagination implementation with flexible page size and offset."""

    @classmethod
    def build(
        cls,
        page: int = Query(1, ge=1, description="Page number"),
        size: int = Query(20, ge=1, le=1000, description="Number of records per page"),
    ) -> "CustomPageNumberPagination":
        return cls(page=page, size=size)
```

### Custom
```python
from typing import Any, List
from fastapi_ronin.pagination import Pagination
from fastapi import Query
import math
from tortoise.queryset import QuerySet

from fastapi_ronin.types import ModelType


class CustomPagination(Pagination[ModelType]):
    """Custom pagination implementation with flexible page size and offset."""

    page: int = 1
    size: int = 10
    total: int = 0
    pages: int = 0

    @classmethod
    def build(
        cls,
        page: int = Query(1, ge=1, description="Page number to retrieve"),
        size: int = Query(10, ge=1, le=50, description="Number of records per page"),
    ) -> "CustomPagination":
        """Create pagination instance from query parameters."""
        return cls(page=page, size=size)

    def paginate(self, queryset: QuerySet[ModelType]) -> QuerySet[ModelType]:
        """Apply pagination to a queryset."""
        offset = (self.page - 1) * self.size
        return queryset.offset(offset).limit(self.size)

    async def fill_meta(self, queryset: QuerySet[ModelType], data: List[Any]) -> None:
        """Fill pagination metadata (like total count, pages, etc.)."""
        self.total = await queryset.count()
        self.pages = math.ceil(self.total / self.size) if self.size > 0 else 0
```

**Explanation**

- `build`: Defines how query parameters are parsed into the pagination instance. In this example, it uses page and size with constraints (e.g., size capped at 50).
- `paginate`: Applies the pagination logic to the queryset, calculating the offset based on the page and size, then limiting the results.
- `fill_meta`: Computes metadata like the total item count and number of pages, ensuring accurate pagination information in the response.
