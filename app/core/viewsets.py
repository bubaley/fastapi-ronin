from fastapi_ronin.pagination import PageNumberPagination
from fastapi_ronin.types import ModelType
from fastapi_ronin.viewsets import ModelViewSet
from fastapi_ronin.wrappers import PaginatedResponseDataWrapper, ResponseDataWrapper


class BaseModelViewSet(ModelViewSet[ModelType]):
    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
    single_wrapper = ResponseDataWrapper
