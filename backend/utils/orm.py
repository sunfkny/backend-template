import functools
from typing import Generic, TypeVar

from django.db.models import F, Field, ForeignObjectRel, Model, Q, QuerySet
from django.db.models.base import ModelBase
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields.related_descriptors import (
    ForeignKeyDeferredAttribute,
    ForwardManyToOneDescriptor,
    ReverseManyToOneDescriptor,
    ReverseOneToOneDescriptor,
)
from django.db.models.query_utils import DeferredAttribute

FieldLike = (
    ForwardManyToOneDescriptor
    | ReverseManyToOneDescriptor
    | DeferredAttribute
    | ReverseOneToOneDescriptor
    | Field
    | str
    | int
    | ModelBase
    | None
)
FieldOrFieldsLike = FieldLike | tuple[FieldLike, ...]

TModelType = TypeVar("TModelType", bound=type[Model])
TModel = TypeVar("TModel", bound=Model)
NOT_SET = object()


@functools.cache
def get_field_name(field: FieldOrFieldsLike) -> str:
    if isinstance(field, list | tuple):
        return LOOKUP_SEP.join([get_field_name(f) for f in field])
    if isinstance(field, str):
        return field

    if isinstance(field, ModelBase):
        return field.__name__.lower()

    if isinstance(field, ForeignKeyDeferredAttribute):
        return str(field.field).split(".")[-1] + "_id"

    if isinstance(
        field,
        (
            ForwardManyToOneDescriptor,
            ReverseManyToOneDescriptor,
            DeferredAttribute,
        ),
    ):
        # return str(field.field).split(".")[-1]
        return field.field.name

    if isinstance(field, ReverseOneToOneDescriptor):
        # return str(field.related).split(".")[-1]
        return field.related.name

    if isinstance(field, ReverseManyToOneDescriptor):
        # return str(field.rel).split(".")[-1]
        return field.rel.name

    if field == Model.pk:
        return "pk"

    raise RuntimeError(f"Unknown field type {type(field)} {repr(field)}")


@functools.cache
def get_accessor_name(self_model: type[Model], model: type[Model]) -> str:
    for related_object in self_model._meta.related_objects:
        related_object: ForeignObjectRel
        if related_object.related_model == model:
            accessor_name = related_object.get_accessor_name()
            if accessor_name:
                return accessor_name
    raise ValueError(f"{model!r} is not a related model to {self_model!r}")


class ColQ:
    """
    Like django Q, but accept field and named args instead of kwargs
    """

    def __init__(self, field: FieldOrFieldsLike):
        self.field = field
        self.name = get_field_name(field)

    def filter(
        self,
        eq=NOT_SET,
        *,
        isnull=NOT_SET,
        gt=NOT_SET,
        lt=NOT_SET,
        gte=NOT_SET,
        lte=NOT_SET,
        ne=NOT_SET,
        range_=NOT_SET,
        in_=NOT_SET,
        like=NOT_SET,
        startswith=NOT_SET,
        istartswith=NOT_SET,
        endswith=NOT_SET,
        iendswith=NOT_SET,
        contains=NOT_SET,
        icontains=NOT_SET,
    ):
        q = Q()
        if eq is not NOT_SET:
            q &= Q(**{self.name: eq})
        if isnull is not NOT_SET:
            q &= Q(**{self.name + "__isnull": isnull})
        if gt is not NOT_SET:
            q &= Q(**{self.name + "__gt": gt})
        if lt is not NOT_SET:
            q &= Q(**{self.name + "__lt": lt})
        if gte is not NOT_SET:
            q &= Q(**{self.name + "__gte": gte})
        if lte is not NOT_SET:
            q &= Q(**{self.name + "__lte": lte})
        if ne is not NOT_SET:
            q &= ~Q(**{self.name: ne})
        if range_ is not NOT_SET:
            q &= Q(**{self.name + "__range": range_})
        if in_ is not NOT_SET:
            q &= Q(**{self.name + "__in": in_})
        if like is not NOT_SET:
            q &= Q(**{self.name + "__like": like})
        if startswith is not NOT_SET:
            q &= Q(**{self.name + "__startswith": startswith})
        if istartswith is not NOT_SET:
            q &= Q(**{self.name + "__istartswith": istartswith})
        if endswith is not NOT_SET:
            q &= Q(**{self.name + "__endswith": endswith})
        if iendswith is not NOT_SET:
            q &= Q(**{self.name + "__iendswith": iendswith})
        if contains is not NOT_SET:
            q &= Q(**{self.name + "__contains": contains})
        if icontains is not NOT_SET:
            q &= Q(**{self.name + "__icontains": icontains})
        return q


class ColF:
    """
    Like django F, but accept field instead of kwargs
    """

    def __init__(self, field: FieldOrFieldsLike):
        self.field = field
        self.name = get_field_name(field)
        self.f = F(self.name)

    def order_by(
        self,
        descending: bool = False,
        nulls_first: bool | None = None,
        nulls_last: bool | None = None,
    ):
        if descending:
            return self.f.desc(nulls_first=nulls_first, nulls_last=nulls_last)
        else:
            return self.f.asc(nulls_first=nulls_first, nulls_last=nulls_last)

    def select_related(self) -> str:
        return get_field_name(self.field)

    @staticmethod
    def get_prefetch_related(self_model: type[Model], model: type[Model]) -> str:
        return get_accessor_name(self_model, model)


class ColQuerySet(Generic[TModel]):
    """
    Like django QuerySet, but accept field instead of kwargs
    """

    def __init__(self, model: type[TModel], qs: QuerySet[TModel] | None = None):
        self.model = model
        self._qs = model.objects.all() if qs is None else qs

    def filter_col(
        self,
        field: FieldOrFieldsLike,
        eq=NOT_SET,
        *,
        isnull=NOT_SET,
        gt=NOT_SET,
        lt=NOT_SET,
        gte=NOT_SET,
        lte=NOT_SET,
        ne=NOT_SET,
        range_=NOT_SET,
        in_=NOT_SET,
        like=NOT_SET,
        startswith=NOT_SET,
        istartswith=NOT_SET,
        endswith=NOT_SET,
        iendswith=NOT_SET,
        contains=NOT_SET,
        icontains=NOT_SET,
    ):
        q = ColQ(field).filter(
            eq=eq,
            isnull=isnull,
            gt=gt,
            lt=lt,
            gte=gte,
            lte=lte,
            ne=ne,
            range_=range_,
            in_=in_,
            like=like,
            startswith=startswith,
            istartswith=istartswith,
            endswith=endswith,
            iendswith=iendswith,
            contains=contains,
            icontains=icontains,
        )
        return ColQuerySet(self.model, self._qs.filter(q))

    def order_by_col(self, field: FieldOrFieldsLike, desc: bool = False):
        return ColQuerySet(self.model, self._qs.order_by(ColF(field).order_by(desc)))

    def select_related_col(self, *fields: FieldOrFieldsLike):
        paths = [ColF(f).select_related() for f in fields]
        return ColQuerySet(self.model, self._qs.select_related(*paths))

    def prefetch_related_col(self, *related_models: type[Model]):
        paths = [ColF.get_prefetch_related(self.model, m) for m in related_models]
        return ColQuerySet(self.model, self._qs.prefetch_related(*paths))

    def qs(self) -> QuerySet:
        return self._qs

    def first(self):
        return self._qs.first()

    def count(self):
        return self._qs.count()

    def all(self):
        return self._qs.all()
