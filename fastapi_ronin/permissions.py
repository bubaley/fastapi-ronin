"""
Permission system for FastAPI Ronin viewsets.

Provides permission classes and utilities for access control.
"""

from typing import TYPE_CHECKING, Any, List, Optional

from fastapi import HTTPException, Request

SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')

if TYPE_CHECKING:
    from fastapi_ronin.generics import GenericViewSet


class BasePermission:
    """
    Base class for all permission classes.

    Permission classes are used to grant or deny access to viewset actions.
    They can check user authentication, authorization, object ownership, etc.
    """

    PERMISSION_DENIED_MESSAGE = 'Permission denied'
    OBJECT_PERMISSION_DENIED_MESSAGE = 'Object permission denied'

    async def has_permission(self, request: Request, view: 'GenericViewSet') -> bool:
        """Return `True` if permission is granted, `False` otherwise."""
        return True

    async def has_object_permission(self, request: Request, view: 'GenericViewSet', obj: Any) -> bool:
        """Return `True` if permission is granted for the specific object, `False` otherwise."""
        return True


class DenyAll(BasePermission):
    """Deny all permissions."""

    async def has_permission(self, request: Request, view: 'GenericViewSet') -> bool:
        return False

    async def has_object_permission(self, request: Request, view: 'GenericViewSet', obj: Any) -> bool:
        return False


class IsAuthenticated(BasePermission):
    """Allows access only to authenticated users."""

    async def has_permission(self, request: Request, view: 'GenericViewSet') -> bool:
        return bool(view.state.user)


class IsAuthenticatedOrReadOnly(BasePermission):
    """Allows read-only access to any user, and full access to authenticated users."""

    async def has_permission(self, request: Request, view: 'GenericViewSet') -> bool:
        return request.method in SAFE_METHODS or bool(view.state.user)


# Permission utilities


async def check_permissions(
    permission_classes: List[BasePermission], request: Optional[Request], view: 'GenericViewSet', obj: Any | None = None
) -> None:
    """Check all permissions and raise HTTP 403 if any permission is denied."""
    if not request:
        return

    for permission in permission_classes:
        # Check general permissions
        if not await permission.has_permission(request, view):
            raise HTTPException(status_code=403, detail=permission.PERMISSION_DENIED_MESSAGE)

        # Check object-level permissions if object is provided
        if obj is not None:
            if not await permission.has_object_permission(request, view, obj):
                raise HTTPException(status_code=403, detail=permission.OBJECT_PERMISSION_DENIED_MESSAGE)
