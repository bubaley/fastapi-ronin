---
title: FastAPI Object Lookups — Flexible URL Parameter Handling with FastAPI Ronin
description: Manage object retrieval in FastAPI Ronin using flexible lookup strategies. Support int, string, UUID, and custom lookups for precise REST API routing and parameter validation.
keywords: FastAPI lookups, URL parameters, object retrieval, FastAPI Ronin lookups, REST API routing, parameter validation, custom lookup methods, Python API development
---

# FastAPI Object Lookups: Flexible URL Parameter-Based Retrieval

FastAPI Ronin offers a flexible object lookup system that controls how items are retrieved from URL parameters. Supporting multiple strategies including int, string, UUID, and custom methods, it enables customizable and precise REST API routing.

## Overview

The lookup system consists of:

1. **Lookup Classes** — define how to extract and validate lookup values from the URL
2. **Automatic Resolution** — seamless integration with ViewSets for object retrieval
3. **Custom Lookups** — ability to create your own lookup logic

## Basic Usage

By default, a ViewSet uses `IntegerLookup` to retrieve objects by integer ID:

```python
from fastapi_ronin.viewsets import ModelViewSet

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
    # lookup_class = IntegerLookup (default)
```

This creates routes like `/companies/{item_id}/`, where `item_id` is an integer.

## Built-in Lookup Classes

- **IntegerLookup** — lookup by integer (default)
- **StringLookup** — lookup by string
- **UUIDLookup** — lookup by UUID

Example of explicitly setting a lookup class:

```python
from fastapi_ronin.lookups import StringLookup

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
    lookup_class = StringLookup
    lookup_field = 'slug'  # model field to search by
```

Now the route will be `/companies/{item_id}/`, where `item_id` is a string (e.g., a slug).

## Custom Lookup Classes

You can create your own lookup class to support special strategies or parameter names:

```python
from fastapi_ronin.lookups import build_lookup_class
from uuid import UUID

# Create a lookup by UUID with a custom parameter name
CustomUUIDLookup = build_lookup_class('CustomUUIDLookup', 'company_uuid', UUID)

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema
    lookup_class = CustomUUIDLookup
    lookup_field = 'uuid'  # model field
```

Now the route will be `/companies/{company_uuid}/`, where `company_uuid` is a UUID.

## Defining a Custom Lookup Class (Subclassing)

In addition to using the `build_lookup_class` factory, you can define your own lookup class by subclassing `BaseLookup`. This is useful if you need custom validation or decoding logic.

For example, let's create a lookup that decodes a base64-encoded token from the URL:

```python
import base64
from fastapi import Path, HTTPException
from fastapi_ronin.lookups import BaseLookup

class TokenLookup(BaseLookup):
    lookup_url_kwarg = 'token'

    @classmethod
    def build(cls, token: str = Path(..., alias='token')):
        try:
            decoded_bytes = base64.urlsafe_b64decode(token)
            return cls(value=decoded_bytes)
        except Exception:
            raise HTTPException(detail='Invalid base64 token', status_code=400)
```

You can then use this lookup in your ViewSet:

```python
@viewset(router)
class SecureResourceViewSet(ModelViewSet[SecureResource]):
    model = SecureResource
    read_schema = SecureResourceReadSchema
    create_schema = SecureResourceCreateSchema
    lookup_class = TokenLookup
    lookup_field = 'token_bytes'  # or whatever field you use
```

This will create a route like `/resources/{token}/`, where `token` is a base64-encoded string that will be decoded before lookup.

## Usage in Custom Actions

The lookup class can also be used in custom detail actions to preserve API consistency and ensure uniform object retrieval handling:

```python
from fastapi_ronin.decorators import action
from fastapi_ronin.lookups import IntegerLookup

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    # ...
    @action(methods=["POST"], detail=True)
    async def activate(self, lookup: IntegerLookup = Depends(IntegerLookup.build)):
        company = await self.get_object(lookup.value)
        company.is_active = True
        await company.save()
        return {"message": "Company activated"}
```

If you use a custom lookup class, the parameter will match its type and name.

## How It Works

- All lookup classes inherit from `BaseLookup`, which defines the common interface.
- To create a lookup class, use the `build_lookup_class` factory, which lets you specify the parameter name and value type.
- The ViewSet uses the `lookup_class` (lookup type) and `lookup_field` (model field to search by) attributes.

## Recommendations

- Use `IntegerLookup` for standard integer IDs
- Use `StringLookup` or a custom lookup for string-based fields (slug, username, etc.)
- Use `UUIDLookup` or a custom lookup for UUID fields
- For complex cases (composite keys, advanced validation), create your own lookup class with `build_lookup_class`
