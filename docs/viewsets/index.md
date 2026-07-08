---
title: FastAPI Ronin ViewSets — CRUD APIs with FastAPI and Tortoise ORM
description: Use FastAPI Ronin ViewSets to group CRUD routes, schemas, filters, permissions, pagination, wrappers, and custom actions around one Tortoise model.
keywords: FastAPI ViewSets, FastAPI Ronin, Tortoise ORM, CRUD APIs, Django REST Framework patterns
---

# ViewSets

ViewSets are the center of FastAPI Ronin. A ViewSet groups the API behavior for
one resource: model, schemas, queryset, filters, permissions, pagination,
wrappers, lifecycle hooks, and custom actions.

```python
from fastapi import APIRouter
from fastapi_ronin.decorators import viewset
from fastapi_ronin.pagination import PageNumberPagination
from fastapi_ronin.viewsets import ModelViewSet
from fastapi_ronin.wrappers import PaginatedResponseDataWrapper, ResponseDataWrapper


router = APIRouter(prefix='/companies', tags=['companies'])


@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    create_schema = CompanyCreateSchema
    read_schema = CompanySchema

    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
    single_wrapper = ResponseDataWrapper
    filterset_class = CompanyFilterSet
```

## What Routes Are Added

`ModelViewSet` adds a full CRUD surface:

| Action | Method | Path |
|--------|--------|------|
| `list` | `GET` | `/companies/` |
| `create` | `POST` | `/companies/` |
| `retrieve` | `GET` | `/companies/{item_id}/` |
| `update` | `PUT`, `PATCH` | `/companies/{item_id}/` |
| `destroy` | `DELETE` | `/companies/{item_id}/` |

`ReadOnlyViewSet` adds only `list` and `retrieve`.

## Core Configuration

| Attribute | Required | Description |
|-----------|----------|-------------|
| `model` | yes | Tortoise ORM model used by the ViewSet. |
| `create_schema` | for create/update | Pydantic model for request bodies. |
| `update_schema` | optional | Defaults to `create_schema`. |
| `read_schema` | for detail responses | Pydantic model for single object responses. |
| `many_read_schema` | optional | Defaults to `read_schema`; useful for smaller list payloads. |
| `filterset_class` | optional | `FilterSet` used by list endpoints. |
| `pagination` | optional | Defaults to `DisabledPagination`. |
| `list_wrapper` | optional | Wrapper for list responses. |
| `single_wrapper` | optional | Wrapper for detail/create/update responses. |
| `permission_classes` | optional | Permission classes instantiated per request. |
| `lookup_class` | optional | URL parameter type, default `IntegerLookup`. |
| `lookup_field` | optional | Model field used by `get_object()`, default `id`. |
| `trailing_slash` | optional | Route slash behavior: `strip`, `append`, or `ignore`. |

## Schema Fallbacks

Ronin fills missing schema pairs:

- `update_schema` defaults to `create_schema`;
- `create_schema` defaults to `update_schema`;
- `many_read_schema` defaults to `read_schema`;
- `read_schema` defaults to `many_read_schema`.

Use this to keep simple ViewSets compact, but define separate schemas when list,
detail, create, and update payloads differ.

## Querysets

Override `get_queryset()` for tenant filtering, soft deletes, or prefetching.

```python
def get_queryset(self):
    queryset = Company.filter(active=True)
    if self.user:
        return queryset.filter(owner_id=self.user['id'])
    return queryset.filter(public=True)
```

`get_queryset()` may be sync or async.

## Request Context

Inside a ViewSet you can access:

| Property | Description |
|----------|-------------|
| `self.request` | Current FastAPI request. |
| `self.user` | User stored in Ronin state. |
| `self.action` | Current action name, such as `list` or `create`. |
| `self.state` | Request-scoped state manager. |

## Extending Behavior

- Use [lifecycle hooks](lifecycle-hooks.md) for validation and save/delete behavior.
- Use [custom actions](actions.md) for endpoints outside CRUD.
- Use [lookups](lookups.md) for slug, UUID, or custom URL parameters.
- Use [generics and mixins](generics-mixins.md) to understand the internal composition.
