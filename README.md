# FastAPI Ronin

<p align="center">
  <h1 align="center">FastAPI Ronin</h1>
</p>
<p align="center">
  <img align="center" src="docs/assets/logo.png" alt="FastAPI Ronin - Django REST Framework patterns for FastAPI" width="250"/>
</p>
<p align="center">
  <span>Build REST APIs with Django REST Framework patterns in FastAPI</span>
</p>
<p align="center">
<a href="https://pypi.org/project/fastapi-ronin/">
  <img src="https://img.shields.io/pypi/v/fastapi-ronin?color=%2334D058&label=version" alt="Version"/>
</a>
<a href="https://pypi.org/project/fastapi-ronin/">
  <img src="https://img.shields.io/pypi/pyversions/fastapi-ronin.svg?color=%2334D058" alt="Python versions"/>
</a>
<a href="https://github.com/bubaley/fastapi-ronin/blob/main/LICENSE">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License"/>
</a>
</p>

---

**Transform your FastAPI development with familiar Django REST Framework patterns.**

FastAPI Ronin gives FastAPI + Tortoise ORM projects a clean class-based API
layer: ViewSets, explicit schemas, filters, pagination, permissions, response
wrappers, custom actions, request state, and cache.

It is small enough to understand quickly, but structured enough to grow from a
single-file prototype into a domain-oriented production app.

<p align="center">
  <a href="https://bubaley.github.io/fastapi-ronin/quick-start/">
    <strong>🚀 Get Started in 5 Minutes</strong>
  </a>
</p>

## 📦 Installation

```bash
uv add fastapi-ronin fastapi tortoise-orm uvicorn
```

For Redis-backed cache:

```bash
uv add "fastapi-ronin[redis]"
```

## 🚀 Complete App in One File

The root [`main.py`](main.py) is a complete runnable application. It includes
database setup, a model, explicit schemas, filters, ordering, pagination,
response wrappers, cache, and a custom action.

```python
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel
from tortoise import fields
from tortoise.contrib.fastapi import register_tortoise
from tortoise.contrib.pydantic import PydanticModel
from tortoise.expressions import Q
from tortoise.models import Model
from tortoise.queryset import QuerySet

from fastapi_ronin.cache import cache
from fastapi_ronin.decorators import action, schema, viewset
from fastapi_ronin.filters import CharFilter, DateTimeFilter, FilterSet, OrderingFilter, Parameter
from fastapi_ronin.pagination import PageNumberPagination
from fastapi_ronin.viewsets import ModelViewSet
from fastapi_ronin.wrappers import PaginatedResponseDataWrapper, ResponseDataWrapper


def register_database(app: FastAPI):
    register_tortoise(
        app,
        db_url='sqlite://db.sqlite3',
        modules={'models': ['main']},
        generate_schemas=True,
        add_exception_handlers=True,
    )


class Company(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)
    full_name = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


@schema(Company)
class CompanyCreateSchema(PydanticModel):
    name: str
    full_name: str | None


@schema(Company)
class CompanyReadSchema(CompanyCreateSchema):
    id: int
    created_at: datetime
    updated_at: datetime


class StatsSchema(BaseModel):
    total: int
    called_cache: int = 0


class CompanyFilterSet(FilterSet):
    fields = [
        CharFilter(field_name='name', view_name='search_by_name', lookup_expr='icontains'),
        CharFilter(field_name='search', method='filter_by_search'),
        DateTimeFilter(field_name='created_at', lookups=['gte', 'lte', 'exact']),
        DateTimeFilter(field_name='updated_at', lookups=['gte', 'lte', 'exact']),
    ]
    ordering = OrderingFilter(
        fields=(
            'name',
            ('created', 'created_at'),
            ('updated', 'updated_at'),
        ),
        default=('-created',),
    )

    def filter_by_search(self, queryset: QuerySet[Company], value: str, parameter: Parameter):
        return queryset.filter(Q(name__icontains=value) | Q(full_name__icontains=value))

    class Meta:
        model = Company


router = APIRouter(prefix='/companies', tags=['companies'])


@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    create_schema = CompanyCreateSchema
    read_schema = CompanyReadSchema

    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
    single_wrapper = ResponseDataWrapper
    filterset_class = CompanyFilterSet

    @action(methods=['GET'], detail=False)
    async def stats(self) -> StatsSchema:
        called = (await cache.get('stats:call') or 0) + 1
        await cache.set('stats:call', called)
        return StatsSchema(total=await Company.all().count(), called_cache=called)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await cache.init(None)
    yield
    await cache.close()


app = FastAPI(title='My API', lifespan=lifespan)
register_database(app)
app.include_router(router)
```

Start server:

```bash
uvicorn main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

## 📋 What You Get

This creates the following endpoints:

- `GET /companies/` - list companies with filters, ordering, pagination, and wrapper metadata
- `POST /companies/` - create a new company
- `GET /companies/{item_id}/` - retrieve a company
- `PUT /companies/{item_id}/` - update a company
- `PATCH /companies/{item_id}/` - partially update a company
- `DELETE /companies/{item_id}/` - delete a company
- `GET /companies/stats/` - custom cached stats endpoint

Example requests:

```text
GET /companies/?search=acme
GET /companies/?search_by_name=corp
GET /companies/?created_at__gte=2026-01-01T00:00:00
GET /companies/?ordering=-updated
```

Example list response:

```json
{
  "data": [
    {
      "id": 1,
      "name": "Acme Corp",
      "full_name": "Acme Corporation Ltd.",
      "created_at": "2026-01-01T10:00:00Z",
      "updated_at": "2026-01-01T10:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "size": 10,
    "total": 47,
    "pages": 5
  }
}
```

Example detail response:

```json
{
  "data": {
    "id": 1,
    "name": "Acme Corp",
    "full_name": "Acme Corporation Ltd.",
    "created_at": "2026-01-01T10:00:00Z",
    "updated_at": "2026-01-01T10:00:00Z"
  }
}
```

Example custom action response:

```json
{
  "total": 123,
  "called_cache": 4
}
```

## ✨ Key Features

<div class="feature-card">
  <h3>🎯 ViewSets</h3>
  Django-like ViewSets with automatic CRUD routes and custom actions. Keep API behavior close to the resource it belongs to.
</div>

<div class="feature-card">
  <h3>📋 Explicit Schemas</h3>
  Write normal Pydantic models and bind them to Tortoise ORM models with <code>@schema(Model)</code>. Your API contract stays visible in code.
</div>

<div class="feature-card">
  <h3>🔍 Filters & Ordering</h3>
  Expose typed FastAPI query parameters and turn them into Tortoise queryset filters.
</div>

<div class="feature-card">
  <h3>📄 Pagination</h3>
  Use page-number or limit-offset pagination with response metadata.
</div>

<div class="feature-card">
  <h3>🔄 Response Wrappers</h3>
  Standardize response shapes for list, detail, create, and update endpoints.
</div>

<div class="feature-card">
  <h3>🔒 Permissions & State</h3>
  Use request-scoped state and permission classes for authentication-aware APIs.
</div>

<div class="feature-card">
  <h3>⚡ Cache</h3>
  Use in-memory cache locally and Redis-backed cache when you need shared storage.
</div>

## 🎯 Philosophy

FastAPI Ronin is designed with these principles:

- **Familiar**: If you know Django REST Framework, ViewSets and permissions will feel natural.
- **Explicit**: Schemas are real Python classes, not hidden dynamic output.
- **Flexible**: Use only the pieces you need: ViewSets, filters, wrappers, permissions, cache, or state.
- **Fast**: Built on FastAPI, async Python, and Tortoise ORM.
- **Modular**: Start in one file, then move to a domain architecture when the app grows.

## 📚 Getting Started

Ready to build a scalable project layout? Start with the
[Quick Start guide](https://bubaley.github.io/fastapi-ronin/quick-start/).

Want to dive deeper?

- [ViewSets](https://bubaley.github.io/fastapi-ronin/viewsets/) - core ViewSet concepts
- [Schemas](https://bubaley.github.io/fastapi-ronin/schemas/) - explicit request and response models
- [Filters](https://bubaley.github.io/fastapi-ronin/filters/) - query parameters and lookup expressions
- [Cache](https://bubaley.github.io/fastapi-ronin/cache/) - in-memory and Redis-backed cache
- [Permissions](https://bubaley.github.io/fastapi-ronin/permissions/) - authentication-aware access rules
- [Pagination](https://bubaley.github.io/fastapi-ronin/pagination/) - page-number and limit-offset pagination
- [State Management](https://bubaley.github.io/fastapi-ronin/state/) - request-scoped state
- [Response Wrappers](https://bubaley.github.io/fastapi-ronin/wrappers/) - consistent API responses

## 🤝 Community

FastAPI Ronin is open source. Issues, ideas, documentation improvements, and
pull requests all help shape the library.

- **GitHub**: [github.com/bubaley/fastapi-ronin](https://github.com/bubaley/fastapi-ronin)
- **Issues**: Report bugs or request features
- **Discussions**: Ask questions and share patterns

## 📄 License

FastAPI Ronin is released under the [MIT License](https://github.com/bubaley/fastapi-ronin/blob/main/LICENSE).
