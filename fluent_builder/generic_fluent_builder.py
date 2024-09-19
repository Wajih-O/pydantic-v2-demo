from collections.abc import Callable
from functools import wraps

from typing import Any, TypeVar

from pydantic import BaseModel

# Define a type variable for Pydantic models
T = TypeVar("T", bound=BaseModel)


def fluent_setter(attr_name: str):
    """fluent_setter"""

    def decorator(method: Callable[[T, Any], T]):
        @wraps(method)
        def wrapper(self: T, value: Any) -> T:
            setattr(self, attr_name, value)
            return self

        return wrapper

    return decorator


class FluentBaseModel(BaseModel):
    """A generic fluent builder enabled base class"""

    @classmethod
    def generate_fluent_setters(cls):
        """generate"""
        for field in cls.__annotations__:
            method_name = "_".join(["with", field])
            if not hasattr(cls, method_name):
                method = fluent_setter(field)(
                    lambda self, value, field=field: setattr(self, field, value) or self
                )
                setattr(cls, method_name, method)
