---
title: FastAPI Generics & Mixins — Flexible ViewSet Architecture in FastAPI Ronin
description: Learn how FastAPI Ronin uses generics and mixins to build flexible, reusable ViewSet components. Customize and extend your APIs with modular architecture inspired by REST API patterns.
keywords: FastAPI generics, ViewSet mixins, FastAPI Ronin architecture, API design patterns, Python mixins, REST API architecture, reusable components, modular API design
---

# Generics & Mixins: Flexible ViewSet Architecture in FastAPI Ronin

FastAPI Ronin's architecture leverages generics and mixins to create flexible, reusable ViewSet components. This modular design enables you to build powerful and customizable APIs by composing specific functionalities tailored to your application’s needs.

## Architecture Overview

FastAPI Ronin uses a layered architecture:

```
ModelViewSet / ReadOnlyViewSet
        ↓
    GenericViewSet (core functionality)
        ↓
    Mixins (add specific routes)
```

### GenericViewSet - The Foundation

`GenericViewSet` contains all the core business logic:

- **Schema handling** - Converting between models and Pydantic schemas
- **Permission checking** - Applying access control
- **State management** - Managing request context
- **Response formatting** - Applying wrappers and pagination

### Mixins - Route Providers

Mixins only add specific routes to the GenericViewSet. They contain no business logic:

- `ListMixin` - Adds `GET /resources/` endpoint
- `RetrieveMixin` - Adds `GET /resources/{item_id}/` endpoint
- `CreateMixin` - Adds `POST /resources/` endpoint
- `UpdateMixin` - Adds `PUT /resources/{item_id}/` endpoint
- `DestroyMixin` - Adds `DELETE /resources/{item_id}/` endpoint
