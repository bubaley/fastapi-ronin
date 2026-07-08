---
title: FastAPI Ronin Response Wrappers — Consistent API Responses
description: Use FastAPI Ronin response wrappers to return consistent data envelopes and pagination metadata from ViewSet endpoints.
keywords: FastAPI response wrappers, FastAPI Ronin, API response envelope, pagination metadata
---

# Response Wrappers

Wrappers define the outer shape of API responses. They are optional, but they
make client code easier when every endpoint returns a predictable envelope.

## Built-In Wrappers

| Wrapper | Use For | Shape |
|---------|---------|-------|
| `ResponseDataWrapper` | single object responses | `{"data": {...}}` |
| `ListDataWrapper` | non-paginated list responses | `{"data": [...]}` |
| `PaginatedResponseDataWrapper` | paginated list responses | `{"data": [...], "meta": {...}}` |

## Single Object Wrapper

```python
from fastapi_ronin.wrappers import ResponseDataWrapper


@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema

    single_wrapper = ResponseDataWrapper
```

```json
{
  "data": {
    "id": 1,
    "name": "Acme"
  }
}
```

`single_wrapper` is used for retrieve, create, and update responses.

## Paginated List Wrapper

```python
from fastapi_ronin.pagination import PageNumberPagination
from fastapi_ronin.wrappers import PaginatedResponseDataWrapper


@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
```

```json
{
  "data": [
    {"id": 1, "name": "Acme"}
  ],
  "meta": {
    "page": 1,
    "size": 10,
    "total": 1,
    "pages": 1
  }
}
```

## Plain List Wrapper

Use `ListDataWrapper` when pagination is disabled but you still want a `data`
envelope.

```python
from fastapi_ronin.pagination import DisabledPagination
from fastapi_ronin.wrappers import ListDataWrapper


@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    pagination = DisabledPagination
    list_wrapper = ListDataWrapper
```

## Custom Single Wrapper

```python
from datetime import datetime

from fastapi_ronin.types import T
from fastapi_ronin.wrappers import ResponseWrapper


class ApiResponse(ResponseWrapper[T]):
    data: T
    success: bool
    timestamp: str

    @classmethod
    def wrap(cls, data: T, **kwargs) -> 'ApiResponse':
        return cls(data=data, success=True, timestamp=datetime.now().isoformat())
```

## Custom Paginated Wrapper

```python
from fastapi_ronin.pagination import PageNumberPagination
from fastapi_ronin.types import T
from fastapi_ronin.wrappers import PaginatedResponseWrapper


class ApiPage(PaginatedResponseWrapper[T, PageNumberPagination]):
    items: list[T]
    total: int
    page: int

    @classmethod
    def wrap(cls, data: list[T], pagination: PageNumberPagination, **kwargs) -> 'ApiPage':
        return cls(items=data, total=pagination.total, page=pagination.page)
```

## Guidance

- Use wrappers from the start if API consistency matters.
- Pair `PaginatedResponseDataWrapper` with a real pagination class.
- Use `ListDataWrapper` only for non-paginated lists.
- Keep wrapper fields stable; clients will depend on them.
