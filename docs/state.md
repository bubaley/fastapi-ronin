---
title: FastAPI Request State Management — Context Handling with FastAPI Ronin
description: Manage request-scoped state efficiently in FastAPI Ronin. Use isolated, concurrency-safe context handling to share data across middleware, ViewSets, and components throughout the request lifecycle.
keywords: FastAPI state management, request context, FastAPI middleware state, Python contextvars, FastAPI Ronin, request lifecycle management, concurrent-safe state, request-scoped context, Python API development, FastAPI architecture
---

# Request State Management in FastAPI Ronin

FastAPI Ronin offers a request-scoped state management system that lets you safely share data across middleware, ViewSets, and other components during a single request lifecycle. Built with concurrency safety in mind, this system is ideal for passing user data, request context, and other runtime information throughout your FastAPI application.

## Overview

The state management system uses Python's `contextvars` to maintain request-scoped data that persists throughout the request lifecycle but is isolated between concurrent requests.

Key features:

- **Request-scoped**: Data is isolated per request
- **Thread-safe**: Works correctly with FastAPI's async nature
- **Automatic cleanup**: State is cleared after each request
- **Flexible storage**: Store any type of data

## Basic Usage

### Setting User Information

The most common use case is storing the current user:

```python
from typing import Optional
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_ronin.state import BaseStateManager


class OptionalHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        credentials: Optional[HTTPAuthorizationCredentials] = None
        try:
            credentials = await super().__call__(request)
        except HTTPException:
            # No credentials provided — allow anonymous
            return None
        return credentials


async def get_current_user(token: Optional[HTTPAuthorizationCredentials] = Depends(OptionalHTTPBearer())):
    if token and token.credentials == "token":  # Your logic
        user = {"id": 1, "username": "john"}
        BaseStateManager.set_user(user)
        return user
    return None


# Apply to app
app = FastAPI(dependencies=[Depends(get_current_user)])
```

### Accessing State in ViewSets

ViewSets automatically have access to the current state:

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
        action = self.action

        if user:
            return Company.filter(owner=user.id)
        return Company.filter(is_public=True)
```

## State Properties

The state manager provides several built-in properties:

### user

The current authenticated user:

```python
def get_queryset(self):
    if self.user:
        # User is authenticated
        return Company.filter(owner=self.user.id)
    else:
        # Anonymous user
        return Company.filter(is_public=True)
```

### request

The current FastAPI Request object:

```python
def get_queryset(self):
    # Access request details
    client_ip = self.request.client.host
    user_agent = self.request.headers.get('user-agent')

    # Log request details
    logger.info(f"Request from {client_ip}: {user_agent}")

    return Company.all()
```

### action

The current ViewSet action being executed:

```python
def get_permissions(self):
    # Different permissions based on action
    if self.action in ('list', 'retrieve'):
        return []  # Public read access
    elif self.action in ('create', 'update'):
        return [IsAuthenticated()]
    elif self.action == 'destroy':
        return [IsAuthenticated(), IsOwner()]

    return super().get_permissions()
```

### request_id

Request id in uuid4 format

### validated_data

The validated request data for create/update operations:

```python
async def perform_save(self, obj):
    # Access validated data that was submitted
    validated_data: <create_schema / update_schema> = self.state.validated_data
```

This property is only available during create and update operations and contains the validated data that was submitted in the request.


## Custom State Data

Store custom data in the state:

```python
# In middleware or dependency
state = BaseStateManager.get_state()
state.set('organization_id', user.organization_id)
state.set('request_start_time', time.time())
state.set('feature_flags', {'new_ui': True, 'beta_feature': False})

# In ViewSet
def get_queryset(self):
    state = self.state

    # Get custom data
    org_id = state.get('organization_id')
    feature_flags = state.get('feature_flags', {})

    queryset = Company.filter(organization_id=org_id)

    if feature_flags.get('new_filtering'):
        queryset = queryset.filter(is_featured=True)

    return queryset
```

## State Management Methods

### Setting Data

```python
state = BaseStateManager.get_state()

# Set individual values
state.set('key', 'value')
state.set('user_preferences', {'theme': 'dark', 'language': 'en'})

# Set user (shortcut)
BaseStateManager.set_user(user)
```

### Getting Data

```python
state = BaseStateManager.get_state()

# Get with default
value = state.get('key', 'default_value')

# Check if key exists
if state.has('user_preferences'):
    prefs = state.get('user_preferences')

# Direct property access
user = state.user
request = state.request
action = state.action
```

### Removing Data

```python
state = BaseStateManager.get_state()

# Remove specific key
state.remove('temporary_data')

# Clear all custom data (keeps request, user, action)
state.clear()
```

## Custom State Manager

Create your own state manager for additional functionality:

```python
from fastapi_ronin.state import BaseStateManager
from typing import Optional

class CustomStateManager(BaseStateManager):
    """Custom state manager with additional properties"""

    @property
    def organization_id(self) -> Optional[int]:
        """Get current user's organization ID"""
        if self.user:
            return getattr(self.user, 'organization_id', None)
        return None

    @property
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        if self.user:
            return getattr(self.user, 'is_admin', False)
        return False

    @property
    def permissions(self) -> list:
        """Get cached user permissions"""
        return self.get('cached_permissions', [])

    def cache_permissions(self, permissions: list):
        """Cache user permissions for this request"""
        self.set('cached_permissions', permissions)

    def log_activity(self, action: str, details: dict = None):
        """Log user activity"""
        activity = {
            'user_id': self.user.id if self.user else None,
            'action': action,
            'details': details or {},
            'timestamp': time.time(),
            'ip_address': self.request.client.host if self.request else None,
        }

        activities = self.get('activities', [])
        activities.append(activity)
        self.set('activities', activities)

# Use custom state manager in ViewSets
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    state_class = CustomStateManager  # Use custom state manager

    def get_queryset(self):
        # Access custom properties
        org_id = self.state.organization_id
        is_admin = self.state.is_admin

        if is_admin:
            return Company.all()
        elif org_id:
            return Company.filter(organization_id=org_id)
        else:
            return Company.filter(is_public=True)

    async def perform_create(self, obj):
        # Log activity
        self.state.log_activity('company_created', {
            'company_name': obj.name
        })

        return await super().perform_create(obj)
```

State management in FastAPI Ronin provides a clean way to share request-scoped data across your application while maintaining thread safety and proper isolation between requests.
