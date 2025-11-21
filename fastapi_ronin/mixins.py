"""
Mixins for FastAPI Ronin viewsets.

These mixins only add specific routes to the GenericViewSet.
They do not contain any business logic - all logic is in GenericViewSet.
"""

from typing import TYPE_CHECKING, Generic

from fastapi import Depends
from pydantic import BaseModel

from fastapi_ronin.lookups import BaseLookup
from fastapi_ronin.pagination import DisabledPagination, Pagination
from fastapi_ronin.routes import add_wrapped_route, build_route_path
from fastapi_ronin.types import ModelType

if TYPE_CHECKING:
    from fastapi_ronin.generics import GenericViewSet


class ListMixin(Generic[ModelType]):
    """Mixin that adds list endpoint to GenericViewSet."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_list_route()  # type: ignore

    def add_list_route(self: 'GenericViewSet'):  # type: ignore
        async def list_endpoint(
            pagination: Pagination[ModelType] = Depends(self.pagination.build),
            filters=Depends(self.filterset_class.get_build()),
        ):
            queryset = self.get_queryset()
            queryset = self.filter_queryset(queryset, filters)

            if not isinstance(pagination, DisabledPagination):
                return await self.get_paginated_response(queryset=queryset, pagination=pagination)

            results = await self.many_read_schema.from_queryset(queryset)  # type: ignore
            return self.get_list_response(results)

        add_wrapped_route(
            viewset=self,
            name='list',
            path=build_route_path(self, 'list'),
            endpoint=list_endpoint,
            methods=['GET'],
            response_model=self.get_list_response_model(),
        )


class RetrieveMixin(Generic[ModelType]):
    """Mixin that adds retrieve endpoint to GenericViewSet."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_retrieve_route()  # type: ignore

    def add_retrieve_route(self: 'GenericViewSet'):  # type: ignore
        async def retrieve_endpoint(lookup: BaseLookup = Depends(self.lookup_class.build)):
            obj: ModelType = await self.get_object(lookup.value)
            result = await self.read_schema.from_tortoise_orm(obj)  # type: ignore
            return self.get_sigle_response(result)

        add_wrapped_route(
            viewset=self,
            name='retrieve',
            path=build_route_path(self, 'retrieve', is_detail=True),
            endpoint=retrieve_endpoint,
            methods=['GET'],
            response_model=self.get_single_response_model(),
        )


class CreateMixin(Generic[ModelType]):
    """Mixin that adds create endpoint to GenericViewSet."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_create_route()  # type: ignore

    def add_create_route(self: 'GenericViewSet'):  # type: ignore
        async def create_endpoint(data: self.create_schema):  # type: ignore
            data = await self.validate_data(data)
            self.state.validated_data = data
            if isinstance(data, BaseModel):
                data = data.model_dump(exclude_unset=True)
            obj: ModelType = self.model()
            obj.update_from_dict(data)
            await self.before_save(obj)
            obj = await self.perform_create(obj)  # type: ignore
            await self.after_save(obj)
            result = await self.read_schema.from_tortoise_orm(obj)  # type: ignore
            return self.get_sigle_response(result)

        add_wrapped_route(
            viewset=self,
            name='create',
            path=build_route_path(self, 'create'),
            endpoint=create_endpoint,
            methods=['POST'],
            response_model=self.get_single_response_model(),
            status_code=201,
        )

    async def perform_create(self: 'GenericViewSet', obj: ModelType) -> ModelType:  # type: ignore
        """Perform the actual object creation."""
        return await self.perform_save(obj)


class UpdateMixin(Generic[ModelType]):
    """Mixin that adds update endpoint to GenericViewSet."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_update_route()  # type: ignore

    def add_update_route(self: 'GenericViewSet'):  # type: ignore
        async def update_endpoint(data: self.update_schema, lookup: BaseLookup = Depends(self.lookup_class.build)):  # type: ignore
            obj: ModelType = await self.get_object(lookup.value)

            data = await self.validate_data(data)
            self.state.validated_data = data
            if isinstance(data, BaseModel):
                data = data.model_dump(exclude_unset=True)
            obj.update_from_dict(data)

            await self.before_save(obj)
            obj = await self.perform_update(obj)  # type: ignore
            await self.after_save(obj)
            result = await self.read_schema.from_tortoise_orm(obj)  # type: ignore
            return self.get_sigle_response(result)

        add_wrapped_route(
            viewset=self,
            name='update',
            path=build_route_path(self, 'update', is_detail=True),
            endpoint=update_endpoint,
            methods=['PUT', 'PATCH'],
            response_model=self.get_single_response_model(),
        )

    async def perform_update(self: 'GenericViewSet', obj: ModelType) -> ModelType:  # type: ignore
        """Perform the actual object update."""
        return await self.perform_save(obj)


class DestroyMixin(Generic[ModelType]):
    """Mixin that adds destroy endpoint to GenericViewSet."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.add_destroy_route()  # type: ignore

    def add_destroy_route(self: 'GenericViewSet'):  # type: ignore
        async def destroy_endpoint(lookup: BaseLookup = Depends(self.lookup_class.build)):
            obj = await self.get_object(lookup.value)
            await self.perform_destroy(obj)  # type: ignore

        add_wrapped_route(
            viewset=self,
            name='destroy',
            path=build_route_path(self, 'destroy', is_detail=True),
            endpoint=destroy_endpoint,
            methods=['DELETE'],
            status_code=204,
        )

    async def perform_destroy(self, obj: ModelType) -> None:
        """Perform the actual object deletion."""
        await obj.delete()
