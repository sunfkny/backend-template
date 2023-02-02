from pydantic import BaseModel
from typing import Dict, List, Union, Optional

DataType = Union[Dict, BaseModel]


class BaseResponse(BaseModel):
    code: int = 200
    msg: str = "OK"


class ErrorResponse(BaseModel):
    code: int = -1
    msg: str


class ErrorDataResponse(BaseResponse):
    code: int = -1
    data: DataType


class Response(BaseResponse):
    data: DataType


class ListResponse(BaseResponse):
    data: List


class PageResponse(BaseResponse):
    data: List
    total_page: int
    total: int
