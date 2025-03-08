from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Literal

from django.db import models
from django.db.models import BaseConstraint, Index, OrderBy
from django.db.models.query import QuerySet
from typing_extensions import TypeVar

if TYPE_CHECKING:

    class TypedModelMeta:
        """
        Typed base class for Django Model `class Meta:` inner class. At runtime this is just an alias to `object`.

        Most attributes are the same as `django.db.models.options.Options`. Options has some additional attributes and
        some values are normalized by Django.
        """

        abstract: ClassVar[bool]  # default: False
        app_label: ClassVar[str]
        base_manager_name: ClassVar[str]
        db_table: ClassVar[str]
        db_table_comment: ClassVar[str]
        db_tablespace: ClassVar[str]
        default_manager_name: ClassVar[str]
        default_related_name: ClassVar[str]
        get_latest_by: ClassVar[str | Sequence[str]]
        managed: ClassVar[bool]  # default: True
        order_with_respect_to: ClassVar[str]
        ordering: ClassVar[Sequence[str | OrderBy]]
        permissions: ClassVar[list[tuple[str, str]]]
        default_permissions: ClassVar[Sequence[str]]  # default: ("add", "change", "delete", "view")
        proxy: ClassVar[bool]  # default: False
        required_db_features: ClassVar[list[str]]
        required_db_vendor: ClassVar[Literal["sqlite", "postgresql", "mysql", "oracle"]]
        select_on_save: ClassVar[bool]  # default: False
        indexes: ClassVar[list[Index]]
        unique_together: ClassVar[Sequence[Sequence[str]] | Sequence[str]]
        index_together: ClassVar[Sequence[Sequence[str]] | Sequence[str]]  # Deprecated in Django 4.2
        constraints: ClassVar[list[BaseConstraint]]
        verbose_name: ClassVar[str | Any]
        verbose_name_plural: ClassVar[str | Any]
else:
    TypedModelMeta = object


_To = TypeVar("_To", bound=models.Model)

if TYPE_CHECKING:
    from typing import type_check_only

    @type_check_only
    class RelatedManager(models.Manager[_To], Generic[_To]):
        related_val: tuple[int, ...]

        def add(self, *objs: _To | int, bulk: bool = ...) -> None: ...
        async def aadd(self, *objs: _To | int, bulk: bool = ...) -> None: ...
        def remove(self, *objs: _To | int, bulk: bool = ...) -> None: ...
        async def aremove(self, *objs: _To | int, bulk: bool = ...) -> None: ...
        def set(
            self,
            objs: QuerySet[_To] | Iterable[_To | int],
            *,
            bulk: bool = ...,
            clear: bool = ...,
        ) -> None: ...
        async def aset(
            self,
            objs: QuerySet[_To] | Iterable[_To | int],
            *,
            bulk: bool = ...,
            clear: bool = ...,
        ) -> None: ...
        def clear(self) -> None: ...
        async def aclear(self) -> None: ...
        def __call__(self, *, manager: str) -> RelatedManager[_To]: ...
