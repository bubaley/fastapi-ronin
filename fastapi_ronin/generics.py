"""
Generic ViewSet class providing base functionality for FastAPI Ronin library.

This is the core class that contains all the base methods and setup logic.
Mixins will only add routes to this generic viewset.
"""

from typing import Any, Generic, List, Optional, Type

from fastapi import APIRouter, HTTPException, Request
from tortoise.contrib.pydantic import PydanticModel
from tortoise.queryset import QuerySet

from fastapi_ronin.filters import EmptyFilterSet, FilterSet
from fastapi_ronin.lookups import BaseLookup, IntegerLookup
from fastapi_ronin.pagination import DisabledPagination, Pagination
from fastapi_ronin.permissions import BasePermission, check_permissions
from fastapi_ronin.routes import TrailingSlashMode, register_action_route, sort_routes_by_specificity
from fastapi_ronin.state import BaseStateManager
from fastapi_ronin.types import ModelType
from fastapi_ronin.wrappers import PaginatedResponseWrapper, ResponseWrapper


class GenericViewSet(Generic[ModelType]):
    """
    Generic ViewSet providing base functionality for API endpoints.

    This class contains all the core logic for working with models, schemas,
    pagination, response formatting, permissions, and filtering.
    Mixins will add specific routes to this base class.
    """

    # Model and schema configuration
    model: Type[ModelType]
    create_schema: Optional[type[PydanticModel]] = None
    update_schema: Optional[type[PydanticModel]] = None
    read_schema: Optional[type[PydanticModel]] | None = None
    many_read_schema: Optional[type[PydanticModel]] = None

    # Lookups
    lookup_field: str = 'id'
    lookup_class: Type[BaseLookup] = IntegerLookup

    # Pagination and response wrappers
    pagination: type[Pagination[ModelType]] = DisabledPagination[ModelType]
    list_wrapper: Optional[type[PaginatedResponseWrapper] | type[ResponseWrapper]] = None
    single_wrapper: Optional[type[ResponseWrapper]] = None

    # Permission configuration
    permission_classes: List[Type[BasePermission]] = []

    # Filtering configuration
    filterset_class: Type[FilterSet] = EmptyFilterSet

    # Router configuration
    router: APIRouter
    trailing_slash: TrailingSlashMode = 'strip'

    # State configuration
    state_class: type[BaseStateManager[Any]] = BaseStateManager

    # Internal state
    __routes_added: bool = False

    def __init__(self, *args, **kwargs):
        # Validate configuration before setup
        from .validation import validate_viewset_config

        validate_viewset_config(self.__class__)

        self.setup_schemas()
        super().__init__(*args, **kwargs)

        # Register routes
        self._register_actions()
        self._finalize_routes()

    @property
    def state(self) -> BaseStateManager[Any]:
        """Get the current request state."""
        return self.state_class.get_state()

    @property
    def request(self) -> Optional[Request]:
        """Get the current request."""
        return self.state.request

    @property
    def user(self) -> Any:
        """Get the current user."""
        return self.state.user

    @property
    def action(self) -> Optional[str]:
        """Get the current action."""
        return self.state.action

    def setup_schemas(self):
        """Setup default schemas if not provided."""

        # Setup create/update schemas with fallbacks
        self.create_schema = self.create_schema or self.update_schema
        self.update_schema = self.update_schema or self.create_schema

        # Setup read schemas with fallbacks
        self.many_read_schema = self.many_read_schema or self.read_schema
        self.read_schema = self.read_schema or self.many_read_schema

    async def check_permissions(self, obj: Any = None) -> None:
        """Check permissions for the current request."""
        await check_permissions(self.get_permissions(), self.request, self, obj)

    def get_permissions(self) -> List[BasePermission]:
        """Get permission instances for this viewset."""
        return [permission() for permission in self.permission_classes]

    def get_queryset(self) -> QuerySet[ModelType]:
        """Get base queryset for the model."""
        if not self.model:
            raise ValueError(f'Model must be provided for {self.__class__.__name__}')
        return self.model.all()

    def get_filter_class(self) -> Optional[Type['FilterSet']]:
        """Get filter class for this viewset."""
        return self.filterset_class

    def filter_queryset(
        self, queryset: QuerySet[ModelType], filter_instance: Optional['FilterSet'] = None
    ) -> QuerySet[ModelType]:
        """Apply filters to the queryset."""
        if filter_instance and hasattr(filter_instance, 'filter_queryset'):
            return filter_instance.filter_queryset(queryset)
        return queryset

    async def get_object(self, value: Any) -> ModelType:
        """Get single object by ID with permission check."""
        queryset = self.get_queryset()
        obj = await queryset.get_or_none(**{self.lookup_field: value})
        if not obj:
            raise HTTPException(status_code=404, detail='Not found')

        # Check object-level permissions if request is provided
        await self.check_permissions(obj)
        return obj

    async def validate_data(self, data: PydanticModel) -> PydanticModel | dict:
        """Validate data."""
        return data

    async def before_save(self, obj: ModelType) -> None:
        """Perform before save actions."""
        pass

    async def after_save(self, obj: ModelType):
        """Perform after save actions."""
        pass

    async def perform_save(self, obj: ModelType) -> ModelType:
        """Perform the actual object save."""
        await obj.save()
        return obj

    def get_list_response_model(self) -> Any:
        """Get response model for list endpoint."""
        if not self.many_read_schema:
            raise ValueError(f'Read schema must be provided for {self.__class__.__name__}')
        if self.list_wrapper:
            if self.list_wrapper and issubclass(self.list_wrapper, ResponseWrapper):
                return self.list_wrapper[self.many_read_schema]  # type: ignore
            elif self.list_wrapper and issubclass(self.list_wrapper, PaginatedResponseWrapper):
                return self.list_wrapper[self.many_read_schema, self.pagination]  # type: ignore
        return list[self.many_read_schema]

    def get_sigle_response(self, data: PydanticModel):
        if self.single_wrapper:
            return self.single_wrapper.wrap(data=data)
        return data

    def get_list_response(self, data: List[PydanticModel]):
        if self.list_wrapper:
            return self.list_wrapper.wrap(data=data)
        return data

    def get_single_response_model(self) -> Any:
        """Get response model for single endpoint."""
        if not self.read_schema:
            raise ValueError(f'Read schema must be provided for {self.__class__.__name__}')
        if self.single_wrapper:
            if self.single_wrapper and issubclass(self.single_wrapper, ResponseWrapper):
                return self.single_wrapper[self.read_schema]  # type: ignore
        return self.read_schema

    async def get_paginated_response(
        self,
        queryset: QuerySet[ModelType],
        pagination: Pagination[ModelType],
        wrapper: Optional[type[PaginatedResponseWrapper]] = None,
    ):
        """Get paginated response for queryset."""

        _wrapper = wrapper or self.list_wrapper
        paginated_query = pagination.paginate(queryset)
        if not self.many_read_schema:
            raise ValueError(f'Many read schema must be provided for {self.__class__.__name__}')

        results = await self.many_read_schema.from_queryset(paginated_query)
        await pagination.fill_meta(queryset=queryset, data=results)

        if _wrapper:
            return _wrapper.wrap(data=results, pagination=pagination)

        return results

    def _register_actions(self) -> None:
        """Register custom actions defined with @action decorator."""
        from .validation import validate_action_method

        # Get all methods from the class
        for method_name in dir(self.__class__):
            method = getattr(self.__class__, method_name)

            # Check if method is marked as action
            if hasattr(method, '_is_action') and method._is_action:
                # Validate action configuration
                validate_action_method(method, self.__class__)

                # Register the action as a route
                register_action_route(self, method)

    def _finalize_routes(self) -> None:
        """Finalize routes after all mixins have added their routes."""
        if not self.__routes_added:
            setattr(self.router, 'routes', sort_routes_by_specificity(self.router.routes))  # type: ignore
            self.__routes_added = True
