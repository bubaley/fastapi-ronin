"""
Decorators for FastAPI Ronin viewsets.

Provides decorators for automatic viewset registration and configuration.
"""

from typing import Any, Callable, Optional, Type

from fastapi import APIRouter
from tortoise import Model

from fastapi_ronin.viewsets import GenericViewSet


def viewset(router: APIRouter):
    """Decorator for automatic viewset registration with FastAPI router."""

    def decorator(cls: Type[GenericViewSet]):
        """Apply viewset decorator to class."""
        # Store router on the class
        cls.router = router

        try:
            # Create instance to trigger route registration
            cls()

        except Exception as e:
            raise RuntimeError(
                f'Failed to initialize viewset {cls.__name__}: {e}. Please check the configuration.'
            ) from e

        return cls

    return decorator


def action(
    methods: Optional[list[str]] = None,
    detail: bool = False,
    path: Optional[str] = None,
    name: Optional[str] = None,
    response_model: Any = None,
    **kwargs,
):
    """Decorator to mark a viewset method as a routable action."""
    if methods is None:
        methods = ['GET']

    def decorator(func: Callable) -> Callable:
        # Store action metadata on the function
        func._is_action = True
        func._action_methods = [method.upper() for method in methods]
        func._action_detail = detail
        func._action_path = path
        func._action_name = name
        func._action_response_model = response_model
        func._action_kwargs = kwargs

        return func

    return decorator


def schema(model: Type[Model], **kwargs):
    """Decorator to mark a viewset method as a routable action."""

    def _get_all_annotations(cls):
        annotations = {}
        for base in reversed(cls.__mro__):
            annotations.update(getattr(base, '__annotations__', {}))
        return annotations

    def decorator(cls):
        cls.model_config['orig_model'] = model  # type: ignore

        # Explicitly merge annotations from base classes.
        # Tortoise reads cls.__annotations__ directly and does not account for inheritance,
        # so we flatten the MRO annotations into the current class to make inherited
        # schema fields visible to Tortoise.
        # tortoise/contrib/pydantic/base.py, line 29
        cls.__annotations__ = _get_all_annotations(cls)
        return cls

    return decorator
