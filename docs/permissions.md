---
title: FastAPI Permissions — Secure API Access Control with FastAPI Ronin
description: Strengthen your FastAPI application's security using Mason's flexible permission system. Supports view-level and object-level permissions inspired by Django REST Framework for precise API access control.
keywords: FastAPI permissions, API security, access control, Django REST Framework permissions, FastAPI authentication, object-level permissions, view-level permissions, Python API security, REST API protection, FastAPI Ronin
---

# API Permissions: FastAPI Ronin Security System

FastAPI Ronin provides a robust permission system that allows you to control access to your API endpoints. The system is inspired by Django REST Framework and provides both view-level and object-level permissions, ensuring your FastAPI applications are secure and properly protected.

## Overview

The permission system consists of:

1. **Permission Classes** - Define access rules
2. **Permission Checking** - Automatic verification on each request
3. **Custom Permissions** - Create your own access logic
4. **Object-Level Permissions** - Fine-grained control per object

## Basic Permission Usage

Set permissions on your ViewSet:

```python
from fastapi_ronin.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from fastapi_ronin.viewsets import ModelViewSet

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanyReadSchema
    create_schema = CompanyCreateSchema

    # Apply permissions to all actions
    permission_classes = [IsAuthenticatedOrReadOnly]
```

## Built-in Permission Classes

### IsAuthenticated

Allows access only to authenticated users:

```python
from fastapi_ronin.permissions import IsAuthenticated

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticated]

    # All endpoints require authentication
```

### IsAuthenticatedOrReadOnly

Allows read access to everyone, write access only to authenticated users:

```python
from fastapi_ronin.permissions import IsAuthenticatedOrReadOnly

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticatedOrReadOnly]

    # GET requests: anyone can access
    # POST/PUT/DELETE: only authenticated users
```

### DenyAll

Denies all access (useful for disabled endpoints):

```python
from fastapi_ronin.permissions import DenyAll

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [DenyAll]

    # All requests will be denied with 403
```

## Conditional Permissions

Apply different permissions based on the action:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticatedOrReadOnly]  # Default permissions

    def get_permissions(self):
        """Customize permissions per action"""
        if self.action in ('stats', 'public_info'):
            return []  # No permissions required

        if self.action == 'sensitive_data':
            return [IsAuthenticated()]  # Require authentication

        if self.action in ('create', 'update', 'destroy'):
            return [IsOwnerOrAdmin()]  # Custom permission

        return super().get_permissions()  # Use default or return []
```

## Custom Permission Classes

Create your own permission classes by inheriting from `BasePermission`:

### IsOwner Permission

```python
from fastapi_ronin.permissions import BasePermission
from fastapi import HTTPException

class IsOwner(BasePermission):
    """Allow access only to object owners"""

    async def has_object_permission(self, request, view, obj):
        """Check if user owns the object"""
        if not view.user:
            return False

        # Assuming obj has an 'owner' field
        return hasattr(obj, 'owner') and obj.owner == view.user.id

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticated, IsOwner]
```

### Role-Based Permission

```python
class HasRole(BasePermission):
    """Check if user has specific role"""

    def __init__(self, required_role: str):
        self.required_role = required_role

    async def has_permission(self, request, view):
        """Check user role"""
        if not view.user:
            return False

        return getattr(view.user, 'role', None) == self.required_role

class IsAdmin(HasRole):
    """Shortcut for admin role"""

    def __init__(self):
        super().__init__('admin')

class IsManager(HasRole):
    """Shortcut for manager role"""

    def __init__(self):
        super().__init__('manager')

# Usage
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    permission_classes = [IsAuthenticated, IsAdmin]
```


### Method-Based Permissions

```python
from fastapi_ronin.permissions import SAFE_METHODS

class ReadOnlyUnlessOwner(BasePermission):
    """Read-only for everyone, write access for owners"""

    async def has_object_permission(self, request, view, obj):
        # Read permissions for everyone
        if request.method in SAFE_METHODS:  # GET, HEAD, OPTIONS
            return True

        # Write permissions only for owners
        if not view.user:
            return False

        return hasattr(obj, 'owner') and obj.owner == view.user.id
```

## Permission Error Handling

Customize error messages:

```python
class CustomPermission(BasePermission):
    PERMISSION_DENIED_MESSAGE = "You don't have permission to access this resource"
    OBJECT_PERMISSION_DENIED_MESSAGE = "You don't have permission to access this specific object"

    async def has_permission(self, request, view):
        # Your logic here
        return True
```
