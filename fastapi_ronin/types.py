from typing import Any, TypeVar, Union

from pydantic import BaseModel
from tortoise.contrib.pydantic import PydanticModel
from tortoise.models import Model

from fastapi_ronin.defaults import _NotSet

T = TypeVar('T', bound=Any)
UserType = TypeVar('UserType')
SchemaType = TypeVar('SchemaType', bound=Union[PydanticModel, BaseModel])
ModelType = TypeVar('ModelType', bound=Model)

TTLType = Union[int, float, None, _NotSet]
