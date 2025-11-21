---
title: FastAPI Custom Actions — Extend ViewSet Endpoints with FastAPI Ronin
description: Enhance your FastAPI Ronin ViewSets by adding custom endpoints using the @action decorator. Implement complex business logic beyond CRUD with full context support.
keywords: FastAPI custom actions, ViewSet custom endpoints, FastAPI Ronin decorators, REST API custom methods, extend ViewSets, Python API development
---

# Custom Actions: Extend ViewSet Endpoints in FastAPI Ronin

FastAPI Ronin allows you to extend ViewSets by adding custom actions using the @action decorator. This lets you implement complex business logic and custom endpoints beyond standard CRUD operations, all with proper request context handling for seamless API functionality.


> **Important:** Always add custom routes to your ViewSets using the `@action` decorator. This ensures that you have access to the request context via `self`, and all lifecycle hooks and permission checks are properly handled. Defining routes outside of `@action` will break context and hook processing.

Actions allow you to add custom endpoints to your ViewSets beyond the standard CRUD operations. They're perfect for implementing business logic that doesn't fit into the standard create, read, update, delete pattern.

## What are Actions?

Actions are custom methods in your ViewSet that are automatically registered as API endpoints. They're decorated with the `@action` decorator and can handle various HTTP methods, accept parameters, and return custom responses.

## Basic Action Usage

```python
from fastapi_ronin.decorators import action

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema

    @action(methods=['GET'], detail=False, response_model=dict)
    async def stats(self):
        """Get company statistics"""
        total = await Company.all().count()
        active = await Company.filter(is_active=True).count()
        return {
            "total": total,
            "active": active,
            "inactive": total - active
        }
```

This creates a new endpoint: `GET /companies/stats/`

## Overriding Standard Methods

You can override standard CRUD methods (such as `list`, `retrieve`, etc.) using the `@action` decorator to add custom logic or parameters. This is useful when you need to extend or modify the default behavior of your ViewSet endpoints.

```python
@action(methods=["GET"], response_model=PaginatedResponseDataWrapper[TaskReadSchema, PageNumberPagination])
async def list(
    self,
    pagination: PageNumberPagination = Depends(PageNumberPagination.build),
    project_id: bool = Query(...),
):
    """Override list method"""
    queryset = self.get_queryset().filter(project_id=project_id)
    return await self.get_paginated_response(queryset=queryset, pagination=pagination)

@action(methods=["PUT"], detail=True)
async def update(self, item_id: int, data: TaskCreateSchema):
    """Override update method"""
    task = await self.get_object(item_id)
    await task.update_from_dict(data.model_dump(exclude_unset=True))
    await task.save()
    return task
```

## Action Parameters

The `@action` decorator accepts several parameters to customize the endpoint:

### methods

Specify which HTTP methods the action accepts:

```python
@action(methods=['GET'])  # Default
async def get_data(self):
    return {"data": "example"}

@action(methods=['POST'])
async def process_data(self):
    return {"status": "processed"}

@action(methods=['GET', 'POST'])
async def flexible_endpoint(self):
    if self.request.method == 'GET':
        return {"data": "viewing"}
    else:
        return {"data": "processing"}
```

### detail

Controls whether the action operates on a single instance or the collection:

```python
# Collection action: /companies/stats/
@action(methods=['GET'], detail=False, response_model=int)
async def stats(self):
    return await Company.all().count()

# Instance action: /companies/{item_id}/activate/
@action(methods=['POST'], detail=True, response_model=dict)
async def activate(self, item_id: int):
    company = await self.get_object(item_id)
    company.is_active = True
    await company.save()
    return {"message": "Company activated"}
```

### path

Customize the URL path for the action:

```python
@action(methods=['GET'], detail=False, path='company-statistics', response_model=dict)
async def stats(self):
    return {"total": await Company.all().count()}

# Creates endpoint: /companies/company-statistics/
```

### name

Set a custom name for the action (used internally):

```python
@action(methods=['GET'], detail=False, name='company_stats', response_model=dict)
async def statistics(self):
    return {"total": await Company.all().count()}
```

### response_model

Specify the response model for OpenAPI documentation:

```python
from pydantic import BaseModel

class StatsResponse(BaseModel):
    total: int
    active: int
    inactive: int

@action(methods=['GET'], detail=False, response_model=StatsResponse)
async def stats(self):
    total = await Company.all().count()
    active = await Company.filter(is_active=True).count()
    return StatsResponse(
        total=total,
        active=active,
        inactive=total - active
    )
```

### Additional FastAPI Parameters

You can pass any additional FastAPI route parameters:

```python
@action(
    methods=['POST'],
    detail=True,
    status_code=202,
    summary="Activate Company",
    description="Activate a company by setting is_active to True",
    tags=["company-management"]
)
async def activate(self, item_id: int):
    company = await self.get_object(item_id)
    company.is_active = True
    await company.save()
    return {"message": "Company activated"}
```

Actions provide a powerful way to extend your ViewSets with custom business logic while maintaining the clean, declarative style of FastAPI Ronin.
