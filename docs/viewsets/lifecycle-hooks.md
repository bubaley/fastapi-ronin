---
title: FastAPI Ronin Lifecycle Hooks — Customize ViewSet Persistence
description: Customize FastAPI Ronin create, update, and delete flows with validate_data, before_save, after_save, perform_save, perform_create, perform_update, and perform_destroy.
keywords: FastAPI Ronin lifecycle hooks, ViewSet hooks, validation hooks, soft delete, CRUD customization
---

# Lifecycle Hooks

Lifecycle hooks let you add domain behavior around the generated CRUD routes
without rewriting the whole endpoint.

## Create and Update Flow

For `POST`, `PUT`, and `PATCH`, Ronin calls:

1. `validate_data(data)`
2. `self.state.validated_data = data`
3. `obj.update_from_dict(data.model_dump(exclude_unset=True))`
4. `before_save(obj)`
5. `perform_create(obj)` or `perform_update(obj)`
6. `perform_save(obj)`
7. `after_save(obj)`
8. serialize with `read_schema`

## Available Hooks

| Hook | Purpose |
|------|---------|
| `validate_data(data)` | Normalize or reject request data before it is applied. |
| `before_save(obj)` | Run checks or enrich the object before saving. |
| `perform_save(obj)` | Central save operation used by create and update. |
| `perform_create(obj)` | Customize create persistence. |
| `perform_update(obj)` | Customize update persistence. |
| `after_save(obj)` | Run side effects after persistence. |
| `perform_destroy(obj)` | Customize delete behavior. |

## Validation Example

```python
from fastapi import HTTPException


@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema

    async def validate_data(self, data: CompanyCreateSchema):
        if data.name.strip() == '':
            raise HTTPException(status_code=400, detail='Company name is required')
        return data
```

## Save Hooks

```python
@viewset(router)
class TaskViewSet(ModelViewSet[Task]):
    model = Task
    read_schema = TaskSchema
    create_schema = TaskCreateSchema

    async def before_save(self, obj: Task):
        await obj.fetch_related('project')
        if not obj.project.active:
            raise HTTPException(status_code=400, detail='Project is not active')

    async def after_save(self, obj: Task):
        await cache.delete(f'project:{obj.project_id}:stats')
```

## Soft Delete

```python
@viewset(router)
class ProjectViewSet(ModelViewSet[Project]):
    model = Project
    read_schema = ProjectSchema
    create_schema = ProjectCreateSchema

    def get_queryset(self):
        return Project.filter(active=True)

    async def perform_destroy(self, obj: Project):
        obj.active = False
        await obj.save()
```

## Access Validated Data

During create and update, Ronin stores the request model on state:

```python
async def before_save(self, obj: Company):
    data = self.state.validated_data
    if data.status == 'inactive':
        obj.deactivated_by = self.user['id']
```

## Guidance

- Use `validate_data()` for request-level checks.
- Use `before_save()` for object-level checks before persistence.
- Use `after_save()` for cache invalidation and other side effects.
- Use `perform_destroy()` for soft delete.
- Keep hooks focused; move larger domain workflows into service functions.
