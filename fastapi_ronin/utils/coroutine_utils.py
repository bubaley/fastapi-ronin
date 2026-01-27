import inspect
from typing import Any, Coroutine, TypeVar, Union

T = TypeVar('T')


async def await_if_coroutine(obj: Union[T, Coroutine[Any, Any, T]]) -> T:
    if inspect.iscoroutine(obj):
        return await obj
    return obj  # type: ignore
