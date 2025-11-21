---
title: FastAPI ViewSet Lifecycle Hooks — Customize API Object Processing with FastAPI Ronin
description: Use FastAPI Ronin ViewSet lifecycle hooks to customize validation, before/after save actions, and custom create/update operations. Enhance your API with fine-grained control.
keywords: FastAPI lifecycle hooks, ViewSet hooks, Django REST Framework hooks, API customization, FastAPI Ronin advanced features, object validation, create update hooks, API processing
---

# FastAPI ViewSet Lifecycle Hooks: Advanced API Object Processing

FastAPI Ronin ViewSets support lifecycle hooks that let you customize object processing at key stages. Control validation, before and after save operations, and implement custom create or update logic to tailor your API behavior precisely.


| Method             | When it is called                                    |
|--------------------|-----------------------------------------------------|
| `validate_data`    | Before processing input data (create/update)         |
| `before_save`      | Before saving the object (create/update)             |
| `after_save`       | After saving the object (create/update)              |
| `perform_create`   | When creating an object (POST)                       |
| `perform_update`   | When updating an object (PUT/PATCH)                  |
| `perform_save`     | When creating or updating an object (PUT/PATCH/POST) |
| `perform_destroy`  | When deleting an object (DELETE)                     |

You can override any of these methods in your ViewSet to add custom logic. Example:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    # ...
    async def validate_data(self, data: CompanyCreateSchema):
        return data

    async def before_save(self, obj: Company):
        pass

    async def after_save(self, obj: Company):
        pass

    async def perform_create(self, obj: Company):
        return await self.perform_save(obj)

    async def perform_update(self, obj: Company):
        return await self.perform_save(obj)

    async def perform_save(self, obj: Company):
        await obj.save()
        return obj

    async def perform_destroy(self, obj: Company):
        obj.is_deleted = True
        await obj.save()
```

Call order for create/update:

1. `validate_data`
2. `before_save`
3. `perform_create` / `perform_update`
4. `perform_save`
5. `after_save`

For deletion, only `perform_destroy` is called.
