from __future__ import annotations

from collections.abc import Mapping
from typing import Generic, TypeVar

from django.core.paginator import Page, Paginator
from ninja import Field, Schema
from pydantic import BaseModel

DataType = Mapping | BaseModel
T = TypeVar("T")
U = TypeVar("U")


class D(Schema, Generic[T]):
    code: int = Field(..., examples=[200])
    msg: str = Field(..., examples=["OK"])
    data: T

    @staticmethod
    def ok(data: U, code: int = 200, msg: str = "OK") -> D[U]:
        return D[U](code=code, msg=msg, data=data)

    @staticmethod
    def success(msg: str = "OK") -> D[None]:
        return D(code=200, msg=msg, data=None)


class L(Schema, Generic[T]):
    code: int = Field(..., examples=[200])
    msg: str = Field(..., examples=["OK"])
    data: list[T]
    total: int = Field(..., examples=[10])
    total_page: int = Field(..., examples=[1])

    @staticmethod
    def ok(data: list[U], code: int = 200, msg: str = "OK", total: int | None = None, total_page: int = 1) -> L[U]:
        if total is None:
            total = len(data)
        return L[U](code=code, msg=msg, data=data, total=total, total_page=total_page)

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
    def list(cls, data: list[DataType]):
        return {"code": 200, "msg": "OK", "data": data}

    @classmethod
    def page_list(cls, data: list[DataType], total: int, total_page: int):
        return {"code": 200, "msg": "OK", "data": data, "total": total, "total_page": total_page}

    @classmethod
    def paginator_list(cls, data: list[DataType], page: Page | Paginator):
        if isinstance(page, Page):
            page = page.paginator
        total = page.count
        total_page = page.num_pages
        return cls.page_list(data=data, total=total, total_page=total_page)
