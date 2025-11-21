---
title: FastAPI ViewSets — Django REST Framework Patterns with FastAPI Ronin
description: Master FastAPI Ronin ViewSets to build REST APIs using Django REST Framework-inspired patterns. Benefit from automatic CRUD, custom actions, and flexible configuration for scalable APIs.
keywords: FastAPI ViewSets, Django REST Framework ViewSets, REST API patterns, CRUD operations, FastAPI Ronin, Python API development, custom ViewSet actions, scalable REST APIs
---

# FastAPI ViewSets: Django REST Framework Patterns with FastAPI Ronin

ViewSets are central to FastAPI Ronin, offering a Django REST Framework-inspired approach to building REST APIs. They provide automatic CRUD operations, custom actions, and flexible configuration options, making it easy for Django developers to build high-performance APIs with FastAPI.

## What are ViewSets?

A ViewSet is a class-based view that groups related actions for a specific resource. Instead of writing separate functions for each HTTP operation, you define a single ViewSet class that handles all operations for your model.

## Basic ViewSet Structure

```python
from fastapi import APIRouter
from fastapi_ronin.decorators import viewset
from fastapi_ronin.viewsets import ModelViewSet

router = APIRouter(prefix='/companies', tags=['companies'])

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company                     # The Tortoise ORM model to use for this ViewSet
    read_schema = CompanyReadSchema     # Pydantic schema for serializing response data (read operations)
    create_schema = CompanyCreateSchema # Pydantic schema for validating and deserializing input data (create/update)

    # Optional configurations
    pagination = PageNumberPagination   # Pagination class to use for list endpoints (default: DisabledPagination)
    permission_classes = [IsAuthenticatedOrReadOnly] # List of permission classes for access control
    list_wrapper = PaginatedResponseDataWrapper      # Wrapper class for formatting paginated list responses
    single_wrapper = ResponseDataWrapper            # Wrapper class for formatting single object responses
```

## ViewSet Types

FastAPI Ronin provides two main ViewSet types:

### ModelViewSet

Provides full CRUD operations:

- **List** (`GET /resources/`) - Get paginated list of resources
- **Create** (`POST /resources/`) - Create new resource
- **Retrieve** (`GET /resources/{item_id}/`) - Get specific resource
- **Update** (`PUT /resources/{item_id}/`) - Update resource
- **Destroy** (`DELETE /resources/{item_id}/`) - Delete resource

```python
from fastapi_ronin.viewsets import ModelViewSet

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
```

### ReadOnlyViewSet

Provides only read operations:

- **List** (`GET /resources/`) - Get paginated list of resources
- **Retrieve** (`GET /resources/{item_id}/`) - Get specific resource

```python
from fastapi_ronin.viewsets import ReadOnlyViewSet

@viewset(router)
class CompanyViewSet(ReadOnlyViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
```

## ViewSet Configuration

### Required Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `model` | `Type[Model]` | The Tortoise ORM model class associated with this ViewSet. |
| `read_schema` | `Type[PydanticModel]` | Pydantic schema used for serializing response data (read operations). |

### Optional Attributes

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| `create_schema` | `Type[PydanticModel]` | `None` | Pydantic schema for validating and deserializing input data when creating resources. |
| `update_schema` | `Type[PydanticModel]` | `create_schema` | Pydantic schema for validating and deserializing input data when updating resources. Defaults to `create_schema` if not set. |
| `many_read_schema` | `Type[PydanticModel]` | `read_schema` | Pydantic schema for serializing list responses. Defaults to `read_schema`. |
| `pagination` | `Type[Pagination]` | `DisabledPagination` | Pagination strategy class for list endpoints. |
| `permission_classes` | `List[Type[BasePermission]]` | `[]` | List of permission classes for access control. |
| `list_wrapper` | `Type[ResponseWrapper]` | `None` | Wrapper class for formatting paginated list responses. |
| `single_wrapper` | `Type[ResponseWrapper]` | `None` | Wrapper class for formatting single object responses. |

## Schema Configuration

ViewSets use different schemas for different operations:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company

    # For reading data (GET operations)
    read_schema = CompanyReadSchema
    many_read_schema = CompanyListSchema  # Optional, defaults to read_schema

    # For writing data (POST/PUT operations)
    create_schema = CompanyCreateSchema
    update_schema = CompanyUpdateSchema  # Optional, defaults to create_schema
```

!!! tip "Schema Fallbacks"
    FastAPI Ronin provides sensible fallbacks:

    - `update_schema` defaults to `create_schema`
    - `create_schema` defaults to `update_schema`
    - `many_read_schema` defaults to `read_schema`

## Customizing Queries

Override the `get_queryset()` method to customize the base queryset:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema

    def get_queryset(self):
        # Filter based on user authentication
        if not self.user:
            return Company.filter(is_public=True)

        # Show user's own companies and public ones
        return Company.filter(
            Q(owner=self.user) | Q(is_public=True)
        )
```

## Accessing Request Context

ViewSets provide easy access to request context:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema

    def get_queryset(self):
        # Access current user
        user = self.user

        # Access current request
        request = self.request

        # Access current action
        action = self.action  # 'list', 'create', 'retrieve', etc.

        return Company.all()
```

## Next Steps

Now that you understand the basics of ViewSets, explore these advanced topics:

- **[Lifecycle Hooks](lifecycle-hooks.md)** - Customize object processing
- **[Actions](actions.md)** - Add custom endpoints to your ViewSets
- **[Generics & Mixins](generics-mixins.md)** - Learn about the underlying architecture
