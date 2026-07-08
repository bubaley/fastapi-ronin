import inspect
from typing import Any, Coroutine, TypeVar, Union, cast, overload

T = TypeVar('T')


@overload
async def await_if_coroutine(obj: Coroutine[Any, Any, T]) -> T: ...


@overload
async def await_if_coroutine(obj: T) -> T: ...


async def await_if_coroutine(obj: Union[T, Coroutine[Any, Any, T]]) -> T:
    if inspect.iscoroutine(obj):
        return cast(T, await obj)
    return cast(T, obj)
