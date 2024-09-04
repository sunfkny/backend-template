from collections.abc import Iterable
from typing import TypedDict, Union

from django.core.paginator import Page, Paginator
from pydantic import BaseModel

DataType = Union[dict, TypedDict, BaseModel]  # noqa: UP007


class Response:
    @classmethod
    def ok(cls):
        return {"code": 200, "msg": "OK"}

    @classmethod
    def success(cls, msg: str = "OK"):
        return {"code": 200, "msg": msg}

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
    def list(cls, data: Iterable):
        if not isinstance(data, list):
            data = list(data)
        return {"code": 200, "msg": "OK", "data": data}

    @classmethod
    def page_list(cls, data: Iterable, total: int, total_page: int):
        if not isinstance(data, list):
            data = list(data)
        return {"code": 200, "msg": "OK", "data": data, "total": total, "total_page": total_page}

    @classmethod
    def paginator_list(cls, data: Iterable, page: Page | Paginator):
        if isinstance(page, Page):
            page = page.paginator
        total = page.count
        total_page = page.num_pages
        return cls.page_list(data=data, total=total, total_page=total_page)
