from functools import wraps
from typing import Any, Callable, TypeVar

# Define a type variable for Pydantic models
T = TypeVar("T")


def fluent_setter(attr_name: str):
    """A fluent setter decorator for attr_name"""

    def decorator(method: Callable[[T, Any], T]):
        @wraps(method)
        def wrapper(self: T, value: Any) -> T:
            setattr(self, attr_name, value)
            return self

        return wrapper

    return decorator
