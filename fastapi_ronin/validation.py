"""
Validation utilities for FastAPI Ronin viewsets.

Provides validation functions to ensure viewset configurations are correct
and catch common errors early.
"""

from typing import Any, Type

from tortoise.models import Model


class ViewSetConfigError(Exception):
    """Raised when viewset configuration is invalid."""

    pass


def validate_viewset_config(cls: Type[Any]) -> None:
    """
    Validate viewset configuration.

    Checks that all required attributes are properly configured
    and raises descriptive errors for common misconfigurations.
    """
    class_name = cls.__name__

    # Check if model is a Tortoise model
    if getattr(cls, 'model', None) and not issubclass(cls.model, Model):
        raise ViewSetConfigError(
            f'{class_name}.model must be a Tortoise ORM model class, got {type(cls.model).__name__}'
        )

    # Check pagination
    _validate_pagination(cls, class_name)

    # Check response wrappers
    _validate_response_wrappers(cls, class_name)


def _validate_pagination(cls: Type[Any], class_name: str) -> None:
    """Validate pagination configuration."""
    if hasattr(cls, 'pagination') and cls.pagination is not None:
        from .pagination import Pagination

        try:
            # Check if pagination is a Pagination class
            if not issubclass(cls.pagination, Pagination):
                raise ViewSetConfigError(
                    f'{class_name}.pagination must be a Pagination class, got {type(cls.pagination).__name__}'
                )
        except TypeError:
            raise ViewSetConfigError(
                f'{class_name}.pagination must be a Pagination class, got {type(cls.pagination).__name__}'
            )


def _validate_response_wrappers(cls: Type[Any], class_name: str) -> None:
    """Validate response wrapper configuration."""
    if hasattr(cls, 'list_wrapper') and cls.list_wrapper is not None:
        from .wrappers import PaginatedResponseWrapper, ResponseWrapper

        try:
            if not (
                issubclass(cls.list_wrapper, ResponseWrapper) or issubclass(cls.list_wrapper, PaginatedResponseWrapper)
            ):
                raise ViewSetConfigError(
                    f'{class_name}.list_wrapper must be a ResponseWrapper or '
                    f'PaginatedResponseWrapper class, got {type(cls.list_wrapper).__name__}'
                )
        except TypeError:
            raise ViewSetConfigError(
                f'{class_name}.list_wrapper must be a ResponseWrapper or '
                f'PaginatedResponseWrapper class, got {type(cls.list_wrapper).__name__}'
            )

    if hasattr(cls, 'single_wrapper') and cls.single_wrapper is not None:
        from .wrappers import ResponseWrapper

        try:
            if not issubclass(cls.single_wrapper, ResponseWrapper):
                raise ViewSetConfigError(
                    f'{class_name}.single_wrapper must be a ResponseWrapper class, '
                    f'got {type(cls.single_wrapper).__name__}'
                )
        except TypeError:
            raise ViewSetConfigError(
                f'{class_name}.single_wrapper must be a ResponseWrapper class, got {type(cls.single_wrapper).__name__}'
            )


def validate_action_method(func: Any, viewset_cls: Type[Any]) -> None:
    """
    Validate that an action method is properly configured.
    """
    if not hasattr(func, '_is_action'):
        return

    func_name = func.__name__
    class_name = viewset_cls.__name__

    # Check that methods are valid HTTP methods
    valid_methods = {'GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'}

    for method in func._action_methods:
        if method not in valid_methods:
            raise ViewSetConfigError(
                f"Invalid HTTP method '{method}' in action {class_name}.{func_name}. "
                f'Valid methods: {", ".join(sorted(valid_methods))}'
            )

    # Check URL path format
    url_path = func._action_path
    if url_path and not isinstance(url_path, str):
        raise ViewSetConfigError(
            f'Action {class_name}.{func_name} url_path must be a string, got {type(url_path).__name__}'
        )
