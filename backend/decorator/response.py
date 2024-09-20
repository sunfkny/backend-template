import inspect
import pathlib
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, TypeVar

from django.http.response import JsonResponse
from ninja.operation import Operation
from pydantic import BaseModel

from backend.renderer import CustomJsonEncoder

P = ParamSpec("P")
S = TypeVar("S", bound=BaseModel)


def schema_response(func: Callable[P, S]) -> Callable[P, JsonResponse]:
    response = inspect.signature(func).return_annotation
    if response == inspect._empty:
        raise Exception(f'View function "{func.__name__}" is missing a return type annotation.')

    def contribute_to_operation(operation: Operation):
        operation.response_models = {200: operation._create_response_model(response)}

    ninja_contribute_to_operation = "_ninja_contribute_to_operation"
    operation_callbacks = getattr(func, ninja_contribute_to_operation, [])
    operation_callbacks.append(contribute_to_operation)
    setattr(func, ninja_contribute_to_operation, operation_callbacks)

    @wraps(func)
    def wrapper(*args, **kwargs) -> JsonResponse:
        result = func(*args, **kwargs)
        return JsonResponse(result, encoder=CustomJsonEncoder)

    return wrapper
