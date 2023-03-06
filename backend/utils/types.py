from __future__ import annotations

from pydantic import BaseModel
from typing import Dict, Iterable, List, Union, NoReturn
from typing_extensions import TypedDict
from ninja.errors import HttpError


DataType = Union[Dict, TypedDict, BaseModel]


class BaseResponse(BaseModel):
    code: int = 200
    msg: str = "OK"


class ErrorResponse(BaseModel):
    code: int = -1
    msg: str


class ErrorDataResponse(ErrorResponse):
    code: int = -1
    msg: str
    data: DataType


class DataResponse(BaseResponse):
    data: DataType


class ListResponse(BaseResponse):
    data: List


class PageResponse(BaseResponse):
    data: List
    total_page: int
    total: int


class Response:
    @staticmethod
    def ok():
        return BaseResponse()

    @staticmethod
    def error(msg: str):
        return ErrorResponse(msg=msg)

    @staticmethod
    def error_data(msg: str, data: DataType):
        return ErrorDataResponse(msg=msg, data=data)

    @staticmethod
    def data(data: DataType):
        return DataResponse(data=data)

    @staticmethod
    def list(data: List | Iterable):
        data = list(data)
        return ListResponse(data=data)

    @staticmethod
    def page_list(data: List | Iterable, total: int, total_page: int):
        data = list(data)
        return PageResponse(data=data, total=total, total_page=total_page)

    @staticmethod
    def http_error(message: str, status_code=400) -> NoReturn:
        raise HttpError(status_code=status_code, message=message)
