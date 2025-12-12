"""
Utility functions for FastAPI Ronin core functionality.
"""

import inspect
from typing import TYPE_CHECKING, Any, Callable, Dict, Literal

from fastapi import Request
from fastapi.routing import APIRoute

if TYPE_CHECKING:
    from .generics import GenericViewSet

BaseMethods = ('create', 'list', 'retrieve', 'update', 'destroy')

TrailingSlashMode = Literal['ignore', 'append', 'strip']


def register_action_route(viewset: 'GenericViewSet', method: Callable):
    """
    Register a single action method as a route.
    """
    # Get action metadata
    action_methods = method._action_methods
    is_detail = method._action_detail
    action_path = method._action_path
    action_name = method._action_name or method.__name__
    action_response_model = method._action_response_model
    action_kwargs = getattr(method, '_action_kwargs', {})

    # Get original method signature (used for both return annotation and parameters)
    original_sig = inspect.signature(method)

    # If response_model is not explicitly set, try to extract it from return annotation
    if action_response_model is None:
        return_annotation = original_sig.return_annotation
        if return_annotation != inspect.Signature.empty and return_annotation is not None:
            action_response_model = return_annotation

    path = build_route_path(viewset, action_name, is_detail, action_path)

    # Remove existing routes with same name/path
    routes_to_remove = []
    for route in viewset.router.routes:
        if isinstance(route, APIRoute):
            checks = [
                hasattr(route, 'name') and route.name == action_name,
                route.path_format == path and set(route.methods or []) & set(action_methods or []),
            ]
            if any(checks):
                routes_to_remove.append(route)

    for route in routes_to_remove:
        viewset.router.routes.remove(route)

    # Get parameters from original method signature and remove 'self'
    params = list(original_sig.parameters.values())[1:]  # Skip 'self'

    # Check if 'request' parameter exists in original method
    has_request_param = any(param.name == 'request' for param in params)

    # Create signature for FastAPI endpoint (without 'self')
    # If method doesn't have request param, add it for FastAPI
    endpoint_params = params.copy()
    if not has_request_param:
        request_param = inspect.Parameter('request', inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Request)
        endpoint_params.insert(0, request_param)

    new_signature = inspect.Signature(parameters=endpoint_params, return_annotation=original_sig.return_annotation)

    # Create endpoint function that properly handles method parameters
    async def action_endpoint(*args, **kwargs):
        """Action endpoint function."""
        # Get original method parameter names (excluding 'self')
        original_param_names = {param.name for param in original_sig.parameters.values() if param.name != 'self'}

        # Prepare kwargs for the original method
        method_kwargs = {}

        # If original method expects 'request' parameter, include it
        if has_request_param and 'request' in kwargs:
            method_kwargs['request'] = kwargs['request']

        # Add other parameters that the method expects
        for param_name, param_value in kwargs.items():
            if param_name in original_param_names and param_name != 'request':
                method_kwargs[param_name] = param_value

        # Call the original method with viewset instance and filtered kwargs
        return await method(viewset, **method_kwargs)

    # Set correct signature and metadata for FastAPI documentation
    action_endpoint.__signature__ = new_signature
    action_endpoint.__name__ = method.__name__
    action_endpoint.__doc__ = method.__doc__

    # Copy annotations from original method, remove 'self', add Request if needed
    annotations = getattr(method, '__annotations__', {}).copy()
    if 'self' in annotations:
        del annotations['self']
    if not has_request_param:
        annotations['request'] = Request
    action_endpoint.__annotations__ = annotations

    # Use add_wrapped_route to apply decorator
    add_wrapped_route(
        viewset=viewset,
        name=action_name,
        path=path,
        endpoint=action_endpoint,
        methods=action_methods,
        response_model=action_response_model,
        **action_kwargs,
    )


def add_wrapped_route(
    viewset: 'GenericViewSet',
    name: str,
    path: str,
    endpoint: Any,
    methods: list[str],
    response_model: Any = None,
    **kwargs,
):
    """
    Add a wrapped route to the viewset router.

    This function applies the universal decorator to the endpoint before adding it to the router.
    It also automatically adds 'request' parameter if it's not present in the endpoint signature.
    """
    # Check if route already exists to prevent duplicates
    existing_route_names = {getattr(route, 'name', None) for route in viewset.router.routes}
    if name in existing_route_names:
        return  # Route already exists, skip

    # Get original function signature
    original_sig = inspect.signature(endpoint)
    params = list(original_sig.parameters.values())

    # Check if 'request' parameter exists
    has_request_param = any(param.name == 'request' for param in params)

    # If no request parameter, add it at the beginning (before any default parameters)
    if not has_request_param:
        request_param = inspect.Parameter('request', inspect.Parameter.POSITIONAL_OR_KEYWORD, annotation=Request)
        params.insert(0, request_param)

        # Create new signature with added request parameter
        new_signature = inspect.Signature(parameters=params, return_annotation=original_sig.return_annotation)

        # Create a wrapper that adds request but doesn't pass it to original function
        async def request_injected_endpoint(*args, **kwargs):
            """Endpoint with auto-injected request parameter."""
            # Remove 'request' from kwargs before calling original function
            filtered_kwargs = {k: v for k, v in kwargs.items() if k != 'request'}
            return await endpoint(*args, **filtered_kwargs)

        # Set the new signature and metadata
        request_injected_endpoint.__signature__ = new_signature
        request_injected_endpoint.__name__ = endpoint.__name__
        request_injected_endpoint.__doc__ = endpoint.__doc__

        # Copy annotations and add Request
        annotations = getattr(endpoint, '__annotations__', {}).copy()
        annotations['request'] = Request
        request_injected_endpoint.__annotations__ = annotations

        # Use the modified endpoint
        final_endpoint = request_injected_endpoint
    else:
        # Use original endpoint if it already has request parameter
        final_endpoint = endpoint

    # Apply universal decorator to the endpoint
    wrapped_endpoint = _create_endpoint_wrapper(
        viewset=viewset,
        endpoint=final_endpoint,
        name=name,
    )

    # Add the wrapped endpoint to the router
    viewset.router.add_api_route(
        path=path,
        endpoint=wrapped_endpoint,
        methods=methods,
        response_model=response_model,
        name=name,
        **kwargs,
    )


def sort_routes_by_specificity(routes: list[APIRoute]) -> list[APIRoute]:
    """
    Sort routes by specificity to ensure proper route matching.
    """
    method_priority: Dict[str, int] = {
        'GET': 0,
        'POST': 1,
        'PUT': 2,
        'PATCH': 2,
        'DELETE': 3,
    }

    def route_score(route: APIRoute) -> tuple:
        parts = route.path.strip('/').split('/')
        path_score = []

        for part in parts:
            if part.startswith('{') and part.endswith('}'):
                path_score.append(1)
            else:
                path_score.append(0)

        method_score = min(method_priority.get(method.upper(), 99) for method in route.methods)

        return (path_score, method_score)

    return sorted(routes, key=lambda route: route_score(route))


def build_route_path(
    viewset: 'GenericViewSet',
    action_name: str,
    is_detail: bool = False,
    action_path: str | None = None,
) -> str:
    """
    Build route path
    """
    parts = []
    if action_name in BaseMethods:
        action_path = None
    else:
        if action_path:
            action_path = action_path.strip('/')
        action_path = (action_path or action_name).replace('_', '-')
    if is_detail:
        parts.append(f'{{{viewset.lookup_class.lookup_url_kwarg}}}')
    if action_path:
        parts.append(action_path)
    path = '/' + '/'.join(parts)

    if viewset.trailing_slash == 'strip':
        path = path.rstrip('/')
        path = '/' if not path and not viewset.router.prefix else path
    elif viewset.trailing_slash == 'append' and not path.endswith('/'):
        path += '/'
    return path


def _create_endpoint_wrapper(
    viewset: 'GenericViewSet',
    endpoint: Callable,
    name: str,
) -> Callable:
    """
    Universal endpoint wrapper that applies to all methods.

    This wrapper ensures that all endpoints (both from mixins and @action)
    go through the same decorator pipeline.
    """
    # Get original function signature
    original_sig = inspect.signature(endpoint)

    async def wrapped_endpoint(*args, **kwargs):
        """Universal endpoint wrapper."""

        state = viewset.state
        setattr(state, 'request', _get_request(*args, **kwargs))
        setattr(state, 'action', name)
        await viewset.check_permissions()
        # Call original function
        try:
            return await endpoint(*args, **kwargs)
        finally:
            state._clear_state()

    # Preserve original function metadata
    wrapped_endpoint.__signature__ = original_sig
    wrapped_endpoint.__name__ = endpoint.__name__
    wrapped_endpoint.__doc__ = endpoint.__doc__
    wrapped_endpoint.__annotations__ = getattr(endpoint, '__annotations__', {})

    return wrapped_endpoint


def _get_request(*args, **kwargs):
    """
    Get the request from the arguments.
    """
    if 'request' in kwargs:
        return kwargs['request']
    else:
        for arg in args:
            if isinstance(arg, Request):
                return arg
