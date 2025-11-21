import uuid
from contextvars import ContextVar
from typing import Any, Generic, Optional

from fastapi import Request

from fastapi_ronin.types import UserType

_mason_state: ContextVar['Optional[BaseStateManager[Any]]'] = ContextVar('_mason_state', default=None)


class BaseStateManager(Generic[UserType]):
    request: Optional[Request] = None
    user: Optional[UserType] = None
    action: Optional[str] = None
    validated_data: Any = None
    request_id: str
    _data: dict[str, Any]

    def __init__(self):
        self.request_id = str(uuid.uuid4())
        self._data = {}

    @classmethod
    def get_state(cls) -> 'BaseStateManager[UserType]':
        """Get the current request state."""
        state = _mason_state.get()
        if state is None:
            state = cls()
            _mason_state.set(state)
        return state

    @classmethod
    def set_user(cls, user: UserType) -> None:
        """Set the current request state."""
        state = cls.get_state()
        state.user = user

    def set(self, key: str, value: Any) -> None:
        """Set a value in the state."""
        self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the state."""
        return self._data.get(key, default)

    def has(self, key: str) -> bool:
        """Check if key exists in state."""
        return key in self._data

    def remove(self, key: str) -> None:
        """Remove a key from state."""
        self._data.pop(key, None)

    def clear(self) -> None:
        """Clear all custom data (keeps action and request)."""
        self._data.clear()

    @staticmethod
    def _clear_state() -> None:
        """Clear the current request state."""
        _mason_state.set(None)

    @staticmethod
    def _set_state(state: 'BaseStateManager[UserType] | None') -> None:
        """Set the current request state."""
        _mason_state.set(state)

    def __repr__(self):
        return f'<BaseStateManager state={self.__dict__}>'
