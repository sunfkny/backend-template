from __future__ import annotations

from pydantic import BaseModel
from typing import Dict, Iterable, List, Union, NoReturn
from typing_extensions import TypedDict
from ninja.errors import HttpError


DataType = Union[Dict, TypedDict, BaseModel]


class Response:
    @staticmethod
    def ok():
        return {"code": 200, "msg": "OK"}

    @staticmethod
    def error(msg: str):
        return {"code": 200, "msg": msg}

    @staticmethod
    def error_data(msg: str, data: DataType):
        return {"code": 200, "msg": msg, "data": data}

    @staticmethod
    def data(data: DataType):
        return {"code": 200, "msg": "OK", "data": data}

    @staticmethod
    def list(data: List | Iterable):
        return {"code": 200, "msg": "OK", "data": data}

    @staticmethod
    def page_list(data: List | Iterable, total: int, total_page: int):
        return {"code": 200, "msg": "OK", "data": data, "total": total, "total_page": total_page}
