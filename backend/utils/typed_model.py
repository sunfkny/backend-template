from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import TYPE_CHECKING, Any, ClassVar, Generic, Literal, Self, overload

from django.db import models
from django.db.models import BaseConstraint, Index, OrderBy
from django.db.models.query import QuerySet
from typing_extensions import TypeVar

T = TypeVar("T")
AnnotationExpression = models.Value | models.F | models.Q | models.Expression

NOT_SET: Any = object()


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


class Annotation(Mapping, Generic[T]):
    def __init__(
        self,
        annotation: AnnotationExpression,
        *,
        default: T = NOT_SET,
    ):
        """
        Descriptor for defining annotated fields on Django models in a declarative way.

        :param annotation:
            The annotation expression to use
        :param default:
            The default value to return if not annotated

        Example:

        .. code-block:: python

            class User(models.Model):
                posts_count = Annotation[int](models.Count("post"))

            class Post(models.Model):
                user = models.ForeignKey(User, on_delete=models.CASCADE)

            qs = User.objects.annotate(Annotation.get_all(User))
            # qs = User.objects.annotate(**User.posts_count) # For exact annotation
            for user in qs:
                print(user.posts_count)
        """
        self.annotation = annotation
        self.default = default

    def __set_name__(self, owner: models.Model, name: str):
        self.owner = owner
        self.name = name

    @property
    def annotate_kwargs(self) -> dict[str, AnnotationExpression]:
        return {self.name: self.annotation}

    def __iter__(self):
        return iter(self.annotate_kwargs)

    def __getitem__(self, key: str) -> AnnotationExpression:
        return self.annotate_kwargs[key]

    def __len__(self):
        return len(self.annotate_kwargs)

    # class access
    @overload
    def __get__(self, obj: None, objtype: Any) -> Self: ...
    # Model instance access
    @overload
    def __get__(self, obj: models.Model, objtype: Any) -> T: ...

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        if self.default is NOT_SET:
            raise AttributeError(
                f"'{self.owner.__name__}.{self.name}' is not available. "
                + "Make sure to apply it using queryset.annotate(...) or provide a default value."
            )

        return self.default

    @classmethod
    def get_all(cls, model: type[models.Model]):
        return {f.name: f.annotation for f in model.__dict__.values() if isinstance(f, cls)}
