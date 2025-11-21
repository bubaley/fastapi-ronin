"""
Base viewset classes for FastAPI Ronin library.

These classes inherit from GenericViewSet and use mixins to add specific routes.
They are simple classes that combine the generic functionality with route mixins.
"""

from fastapi_ronin.generics import GenericViewSet
from fastapi_ronin.mixins import (
    CreateMixin,
    DestroyMixin,
    ListMixin,
    RetrieveMixin,
    UpdateMixin,
)
from fastapi_ronin.types import ModelType


class ModelViewSet(
    GenericViewSet[ModelType],
    ListMixin[ModelType],
    RetrieveMixin[ModelType],
    CreateMixin[ModelType],
    UpdateMixin[ModelType],
    DestroyMixin[ModelType],
):
    """Base viewset providing full CRUD operations."""

    pass


class ReadOnlyViewSet(
    GenericViewSet[ModelType],
    ListMixin[ModelType],
    RetrieveMixin[ModelType],
):
    """Read-only viewset providing list and retrieve operations."""

    pass
