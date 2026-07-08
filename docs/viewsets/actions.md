---
title: FastAPI Ronin Actions — Custom Endpoints on ViewSets
description: Add collection and detail endpoints to FastAPI Ronin ViewSets with the @action decorator, typed parameters, response models, and route options.
keywords: FastAPI custom actions, FastAPI Ronin, ViewSet actions, custom endpoints, REST API
---

# Actions

Actions add non-CRUD endpoints to a ViewSet while keeping request context,
permissions, route ordering, and OpenAPI generation in the same system as the
standard CRUD routes.

```python
from pydantic import BaseModel
from fastapi_ronin.decorators import action


class StatsSchema(BaseModel):
    total: int


@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema

    @action(methods=['GET'], detail=False)
    async def stats(self) -> StatsSchema:
        return StatsSchema(total=await Company.all().count())
```

This creates:

```text
GET /companies/stats/
```

Ronin uses the return annotation as the response model when `response_model` is
not provided explicitly.

## Collection and Detail Actions

Collection actions operate on the resource collection:

```python
@action(methods=['GET'], detail=False)
async def stats(self) -> StatsSchema:
    return StatsSchema(total=await Company.all().count())
```

Detail actions include the lookup parameter:

```python
@action(methods=['POST'], detail=True)
async def activate(self, item_id: int) -> CompanySchema:
    company = await self.get_object(item_id)
    company.status = 'active'
    await company.save()
    return await CompanySchema.from_tortoise_orm(company)
```

```text
POST /companies/{item_id}/activate/
```

## Custom Paths

Use `path` when the URL should differ from the Python method name.

```python
@action(methods=['GET'], detail=False, path='company-statistics')
async def stats(self) -> StatsSchema:
    return StatsSchema(total=await Company.all().count())
```

```text
GET /companies/company-statistics/
```

Without `path`, underscores are converted to dashes.

## FastAPI Route Options

Extra keyword arguments are passed to `add_api_route()`.

```python
@action(
    methods=['POST'],
    detail=True,
    status_code=202,
    summary='Activate company',
)
async def activate(self, item_id: int) -> CompanySchema:
    ...
```

Use `response_model` explicitly when the return annotation is not enough:

```python
@action(methods=['GET'], detail=False, response_model=dict[str, int])
async def raw_stats(self):
    return {'total': await Company.all().count()}
```

## Overriding CRUD Routes

Define an action with the same name as a CRUD action to replace the generated
route.

```python
from fastapi import Depends, Query
from fastapi_ronin.pagination import PageNumberPagination
from fastapi_ronin.wrappers import PaginatedResponseDataWrapper


@action(
    methods=['GET'],
    response_model=PaginatedResponseDataWrapper[TaskReadSchema, PageNumberPagination],
)
async def list(
    self,
    pagination: PageNumberPagination = Depends(PageNumberPagination.build),
    project_id: int = Query(...),
):
    queryset = Task.filter(project_id=project_id)
    return await self.get_paginated_response(queryset=queryset, pagination=pagination)
```

## Guidance

- Keep resource-specific operations on the ViewSet as actions.
- Use return annotations for clean OpenAPI models.
- Use `detail=True` when the action operates on one object.
- Use FastAPI dependencies and query parameters normally in action signatures.
- Put reusable business logic in services; keep actions thin.
