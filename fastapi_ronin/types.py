from typing import TYPE_CHECKING, Any, TypeVar, Union

from pydantic import BaseModel
from tortoise.contrib.pydantic import PydanticModel
from tortoise.models import Model

if TYPE_CHECKING:
    pass


T = TypeVar('T', bound=Any)
UserType = TypeVar('UserType')
SchemaType = TypeVar('SchemaType', bound=Union[PydanticModel, BaseModel])
ModelType = TypeVar('ModelType', bound=Model)
