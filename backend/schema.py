from typing import Annotated, TypeVar

from pydantic import ValidationError, WrapValidator
from pydantic_core import PydanticUseDefault

T = TypeVar("T")


def empty_str_to_default(v, handler):
    if isinstance(v, str) and v.strip() == "":
        raise PydanticUseDefault
    return handler(v)


EmptyStrToDefault = Annotated[T, WrapValidator(empty_str_to_default)]


def validation_error_to_default(v, handler):
    try:
        return handler(v)
    except ValidationError:
        raise PydanticUseDefault


ValidationErrorToDefault = Annotated[T, WrapValidator(validation_error_to_default)]
