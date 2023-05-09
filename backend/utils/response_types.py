from __future__ import annotations

from pydantic import BaseModel
from typing import Dict, Iterable, List, Union
from typing_extensions import TypedDict
from django.core.paginator import Page, Paginator

DataType = Union[Dict, TypedDict, BaseModel]


class Response:
    @classmethod
    def ok(cls):
        return {"code": 200, "msg": "OK"}

    @classmethod
    def error(cls, msg: str):
        return {"code": -1, "msg": msg}

    @classmethod
    def error_data(cls, msg: str, data: DataType):
        return {"code": -1, "msg": msg, "data": data}

    @classmethod
    def data(cls, data: DataType):
        return {"code": 200, "msg": "OK", "data": data}

    @classmethod
    def list(cls, data: List | Iterable):
        return {"code": 200, "msg": "OK", "data": data}

    @classmethod
    def page_list(cls, data: List | Iterable, total: int, total_page: int):
        return {"code": 200, "msg": "OK", "data": data, "total": total, "total_page": total_page}

    @classmethod
    def paginator_list(cls, data: List | Iterable, page: Union[Page, Paginator]):
        if isinstance(page, Page):
            page = page.paginator
        total = page.count
        total_page = page.num_pages
        return cls.page_list(data=data, total=total, total_page=total_page)
