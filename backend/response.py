from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import Generic, TypeVar

from django.core.paginator import Page, Paginator
from ninja import Field, Schema
from pydantic import BaseModel

DataType = Mapping | BaseModel
T = TypeVar("T")
U = TypeVar("U", bound=DataType)


class D(Schema, Generic[T]):
    code: int = Field(..., examples=[200])
    msg: str = Field(..., examples=["OK"])
    data: T | None = None

    @staticmethod
    def ok(data: U | None = None, code: int = 200, msg: str = "OK") -> D[U]:
        return D[U](code=code, msg=msg, data=data)

    @staticmethod
    def error(msg: str, data: U | None = None, code: int = -1) -> D[U]:
        return D[U](code=code, msg=msg, data=data)


class L(Schema, Generic[T]):
    code: int = Field(..., examples=[200])
    msg: str = Field(..., examples=["OK"])
    data: list[T] | None = None
    total: int | None = None
    total_page: int | None = None

    @staticmethod
    def ok(data: list[U], total: int | None = None, total_page: int | None = None, code: int = 200, msg: str = "OK") -> L[U]:
        return L[U](code=code, msg=msg, data=data, total=total, total_page=total_page)

    @staticmethod
    def error(msg: str, data: list[U] | None = None, code: int = -1) -> L[U]:
        return L[U](code=code, msg=msg, data=data)

    @staticmethod
    def page(data: list[U], page: Page | Paginator, code: int = 200, msg: str = "OK") -> L[U]:
        if isinstance(page, Page):
            page = page.paginator
        return L[U](code=code, msg=msg, data=data, total=page.count, total_page=page.num_pages)


class Response:
    @classmethod
    def ok(cls):
        return {"code": 200, "msg": "OK"}

    @classmethod
    def success(cls, msg: str = "OK"):
        return {"code": 200, "msg": msg}

    @classmethod
    def error(cls, msg: str, data: DataType | None = None):
        return {"code": -1, "msg": msg, "data": data}

    @classmethod
    def data(cls, data: DataType):
        return {"code": 200, "msg": "OK", "data": data}

    @classmethod
    def list(cls, data: Collection[DataType]):
        return {"code": 200, "msg": "OK", "data": data}

    @classmethod
    def page_list(cls, data: Collection[DataType], total: int, total_page: int):
        return {"code": 200, "msg": "OK", "data": data, "total": total, "total_page": total_page}

    @classmethod
    def paginator_list(cls, data: Collection[DataType], page: Page | Paginator):
        if isinstance(page, Page):
            page = page.paginator
        total = page.count
        total_page = page.num_pages
        return cls.page_list(data=data, total=total, total_page=total_page)
