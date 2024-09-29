import inspect
from collections.abc import Callable
from functools import wraps
from typing import ParamSpec, Protocol, TypeVar

from django.http import HttpRequest
from django.http.response import JsonResponse
from loguru import logger
from ninja.operation import Operation
from pydantic import BaseModel

from backend.renderer import CustomJsonEncoder

P = ParamSpec("P")
S = TypeVar("S", bound=BaseModel)
T = TypeVar("T", covariant=True)


class ViewFunc(Protocol[P, T]):
    def __call__(
        self,
        request: HttpRequest,
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> T: ...


def schema_response(func: ViewFunc[P, S]) -> ViewFunc[P, JsonResponse]:
    response = inspect.signature(func).return_annotation
    if response == inspect._empty:
        response = None
        logger.warning(f'View function "{func.__qualname__}" is missing a return type annotation.')

    def contribute_to_operation(operation: Operation):
        operation.response_models = {200: operation._create_response_model(response)}

    ninja_contribute_to_operation = "_ninja_contribute_to_operation"
    operation_callbacks = getattr(func, ninja_contribute_to_operation, [])
    operation_callbacks.append(contribute_to_operation)
    setattr(func, ninja_contribute_to_operation, operation_callbacks)

    @wraps(func)
    def wrapper(*args, **kwargs) -> JsonResponse:
        result = func(*args, **kwargs)
        return JsonResponse(result, safe=False, encoder=CustomJsonEncoder)

    return wrapper
