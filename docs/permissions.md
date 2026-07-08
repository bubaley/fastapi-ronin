---
title: FastAPI Ronin Permissions — ViewSet Access Control
description: Protect FastAPI Ronin ViewSets with built-in and custom permission classes, action-specific rules, and object-level permission checks.
keywords: FastAPI permissions, FastAPI Ronin, access control, ViewSet permissions, object permissions
---

# Permissions

Permissions decide whether a request may execute a ViewSet action. They are
small async classes with two hooks:

- `has_permission(request, view)` for view-level checks;
- `has_object_permission(request, view, obj)` for object-level checks.

Ronin checks view-level permissions for routed actions and checks object-level
permissions when `get_object()` retrieves a model instance.

## Built-In Permissions

| Class | Behavior |
|-------|----------|
| `IsAuthenticated` | Allows requests only when `view.state.user` is set. |
| `IsAuthenticatedOrReadOnly` | Allows `GET`, `HEAD`, `OPTIONS`; write methods require `view.state.user`. |
| `DenyAll` | Denies every request. |

## Basic Usage

```python
from fastapi_ronin.permissions import IsAuthenticatedOrReadOnly


@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema

    permission_classes = [IsAuthenticatedOrReadOnly]
```

Permissions are instantiated per request by `get_permissions()`.

## Set the Current User

Ronin does not prescribe authentication. Use a FastAPI dependency or middleware
to authenticate the request and put the user into request state.

```python
from fastapi import Depends, FastAPI
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_ronin.state import BaseStateManager


security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if credentials and credentials.credentials == 'token':
        user = {'id': 1, 'email': 'admin@example.com'}
        BaseStateManager.set_user(user)
        return user
    return None


app = FastAPI(dependencies=[Depends(get_current_user)])
```

## Action-Specific Permissions

Override `get_permissions()` when different actions need different rules.

```python
from fastapi_ronin.permissions import IsAuthenticated


@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'stats'):
            return []
        return [IsAuthenticated()]
```

`self.action` is set by Ronin while handling a route.

## Custom Permissions

```python
from fastapi_ronin.permissions import BasePermission


class IsOwner(BasePermission):
    PERMISSION_DENIED_MESSAGE = 'Authentication required'
    OBJECT_PERMISSION_DENIED_MESSAGE = 'Only the owner can access this object'

    async def has_permission(self, request, view) -> bool:
        return bool(view.user)

    async def has_object_permission(self, request, view, obj) -> bool:
        return getattr(obj, 'owner_id', None) == view.user['id']
```

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsOwner]
```

## Read-Only Custom Permission

```python
from fastapi_ronin.permissions import BasePermission, SAFE_METHODS


class ReadOnlyOrStaff(BasePermission):
    async def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return bool(view.user and view.user.get('is_staff'))
```

## Guidance

- Keep authentication in FastAPI dependencies or middleware.
- Keep authorization in permission classes.
- Use `get_permissions()` for action-specific policy.
- Put object ownership checks in `has_object_permission()`.
- Customize `PERMISSION_DENIED_MESSAGE` and `OBJECT_PERMISSION_DENIED_MESSAGE` for API-friendly errors.
