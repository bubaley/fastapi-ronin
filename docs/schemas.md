---
title: FastAPI Ronin Schemas — Pydantic Models for Tortoise ORM
description: Build explicit request and response schemas for FastAPI Ronin with Tortoise ORM PydanticModel classes and the @schema decorator.
keywords: FastAPI schemas, Tortoise ORM, PydanticModel, FastAPI Ronin, API serialization, request validation, response models
---

# Schemas

FastAPI Ronin uses explicit Pydantic schemas. You write normal
`tortoise.contrib.pydantic.PydanticModel` classes, then bind each schema to a
Tortoise model with `@schema(Model)`.

This keeps the API contract visible in code, works well with type checkers, and
avoids hidden dynamic schema generation.

## Basic Schema

```python title="app/domains/company/schemas.py"
from datetime import datetime

from tortoise.contrib.pydantic import PydanticModel

from app.domains.company.models import Company
from fastapi_ronin.decorators import schema


@schema(Company)
class CompanyCreateSchema(PydanticModel):
    name: str
    full_name: str | None = None


@schema(Company)
class CompanyReadSchema(CompanyCreateSchema):
    id: int
    created_at: datetime
    updated_at: datetime
```

`CompanyCreateSchema` is used for request bodies. `CompanyReadSchema` is used
for responses and can inherit fields from the create schema.

## Why the Decorator Exists

Tortoise Pydantic models need a link back to the ORM model. The `@schema`
decorator sets that link and flattens inherited annotations so inherited fields
are visible to Tortoise.

```python
@schema(Project)
class ProjectReadSchema(ProjectCreateSchema):
    id: int
```

Without the decorator, `from_tortoise_orm()` and `from_queryset()` do not know
which ORM model to serialize.

## Using Schemas in ViewSets

```python
from fastapi_ronin.decorators import viewset
from fastapi_ronin.viewsets import ModelViewSet


@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    create_schema = CompanyCreateSchema
    read_schema = CompanyReadSchema
```

Schema fallbacks are handled by the viewset:

| Attribute | Used For | Fallback |
|-----------|----------|----------|
| `create_schema` | `POST` body | `update_schema` |
| `update_schema` | `PUT` and `PATCH` body | `create_schema` |
| `read_schema` | detail responses | `many_read_schema` |
| `many_read_schema` | list responses | `read_schema` |

Use `many_read_schema` when list responses should be smaller than detail
responses.

## List and Detail Schemas

```python
@schema(Project)
class ProjectCreateSchema(PydanticModel):
    name: str
    company_id: int


@schema(Project)
class ProjectListSchema(ProjectCreateSchema):
    id: int


@schema(Project)
class ProjectDetailSchema(ProjectListSchema):
    company: CompanyReadSchema
    created_at: datetime
    updated_at: datetime
```

```python
@viewset(router)
class ProjectViewSet(ModelViewSet[Project]):
    model = Project
    create_schema = ProjectCreateSchema
    many_read_schema = ProjectListSchema
    read_schema = ProjectDetailSchema
```

## Relationships

Use foreign key id fields for writes and nested schemas for reads.

```python title="models.py"
class Project(Model):
    name = fields.CharField(max_length=255)
    company = fields.ForeignKeyField('models.Company', related_name='projects')
```

```python title="schemas.py"
@schema(Project)
class ProjectCreateSchema(PydanticModel):
    name: str
    company_id: int


@schema(Project)
class ProjectReadSchema(ProjectCreateSchema):
    id: int
    company: CompanyReadSchema
```

When serializing related data, make sure the relation can be fetched by
Tortoise. For custom querysets, prefetch related objects when needed:

```python
def get_queryset(self):
    return Project.all().prefetch_related('company')
```

## Custom Response Schemas

Custom actions often return data that is not an ORM model. Use regular Pydantic
models from `pydantic.BaseModel`.

```python
from pydantic import BaseModel


class StatsSchema(BaseModel):
    total: int
    called_cache: int = 0


@action(methods=['GET'], detail=False)
async def stats(self) -> StatsSchema:
    return StatsSchema(total=await Company.all().count())
```

## Best Practices

- Keep schemas explicit. New model fields should not appear in the API until you
  add them to a schema.
- Use separate create/update schemas when writable fields differ.
- Use `many_read_schema` for compact list payloads and `read_schema` for richer
  detail payloads.
- Prefer nested read schemas and `*_id` write fields for relationships.
- Keep schema classes near the domain they describe, for example
  `app/domains/company/schemas.py`.

## Migrating from Dynamic Schemas

If your project still has a separate schema configuration file and dynamically
generated schema variables, replace them with explicit classes:

```python
@schema(Company)
class CompanyCreateSchema(PydanticModel):
    name: str
    full_name: str | None = None


@schema(Company)
class CompanyReadSchema(CompanyCreateSchema):
    id: int
    created_at: datetime
    updated_at: datetime
```
