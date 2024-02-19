from __future__ import annotations

import typing
from typing import TYPE_CHECKING, Any, Sequence, TypeAlias

from django.core.exceptions import FieldError
from django.db.models import Manager, Model, QuerySet
from django.db.models.constants import LOOKUP_SEP
from django.db.models.fields import Field

__all__ = [
    "get_queryset_fields",
    "dunder_to_nest",
    "model_to_json",
]

JsonDict = dict[str, Any]
SequenceOrValuesJsonDict: TypeAlias = Sequence[JsonDict] | Sequence[dict]
SelectMask: TypeAlias = dict[Field, "SelectMask"]
FieldDict: TypeAlias = dict[str, "FieldDict"]


def select_mask_to_values_fields(
    select_mask: SelectMask,
    context: list[str] | None = None,
) -> list[str]:
    if context is None:
        context = []
    data = []

    for field, sub_select_mask in select_mask.items():
        if sub_select_mask:
            data.extend(
                select_mask_to_values_fields(
                    select_mask=sub_select_mask,
                    context=[*context, field.name],
                )
            )
        else:
            # if not field.is_relation:
            data.append(LOOKUP_SEP.join([*context, field.name]))

    return data


def flatten_select_related(
    field_dict: FieldDict,
    context: list[str] | None = None,
    data: list[str] | None = None,
) -> list[str]:
    if context is None:
        context = []
    if data is None:
        data = []

    for field, sub_field_dict in field_dict.items():
        if sub_field_dict:
            # not empty dict, go deeper
            flatten_select_related(
                field_dict=sub_field_dict,
                context=[*context, field],
                data=data,
            )
        else:
            # empty dict, append field
            data.append(LOOKUP_SEP.join([*context, field]))
    return data


def _get_defer_select_mask(self, opts, mask, select_mask=None):
    if select_mask is None:
        select_mask = {}
    select_mask[opts.pk] = {}
    # All concrete fields that are not part of the defer mask must be
    # loaded. If a relational field is encountered it gets added to the
    # mask for it be considered if `select_related` and the cycle continues
    # by recursively caling this function.
    for field in opts.concrete_fields:
        field_mask = mask.pop(field.name, None)
        field_att_mask = mask.pop(field.attname, None)
        if field_mask is None and field_att_mask is None:
            select_mask.setdefault(field, {})
        elif field_mask:
            if not field.is_relation:
                raise FieldError(next(iter(field_mask)))
            field_select_mask = select_mask.setdefault(field, {})
            related_model = field.remote_field.model._meta.concrete_model
            self._get_defer_select_mask(related_model._meta, field_mask, field_select_mask)
    # Remaining defer entries must be references to reverse relationships.
    # The following code is expected to raise FieldError if it encounters
    # a malformed defer entry.
    for field_name, field_mask in mask.items():
        if filtered_relation := self._filtered_relations.get(field_name):
            relation = opts.get_field(filtered_relation.relation_name)
            field_select_mask = select_mask.setdefault((field_name, relation), {})
            field = relation.field
        else:
            reverse_rel = opts.get_field(field_name)
            # While virtual fields such as many-to-many and generic foreign
            # keys cannot be effectively deferred we've historically
            # allowed them to be passed to QuerySet.defer(). Ignore such
            # field references until a layer of validation at mask
            # alteration time will be implemented eventually.
            if not hasattr(reverse_rel, "field"):
                continue
            field = reverse_rel.field
            field_select_mask = select_mask.setdefault(field, {})
        related_model = field.model._meta.concrete_model
        self._get_defer_select_mask(related_model._meta, field_mask, field_select_mask)
    return select_mask


def _get_only_select_mask(self, opts, mask, select_mask=None):
    if select_mask is None:
        select_mask = {}
    select_mask[opts.pk] = {}
    # Only include fields mentioned in the mask.
    for field_name, field_mask in mask.items():
        field = opts.get_field(field_name)
        # Retrieve the actual field associated with reverse relationships
        # as that's what is expected in the select mask.
        if field in opts.related_objects:
            field_key = field.field
        else:
            field_key = field
        field_select_mask = select_mask.setdefault(field_key, {})
        if field_mask:
            if not field.is_relation:
                raise FieldError(next(iter(field_mask)))
            related_model = field.remote_field.model._meta.concrete_model
            self._get_only_select_mask(related_model._meta, field_mask, field_select_mask)
    return select_mask


def get_select_mask(self):
    """
    Convert the self.deferred_loading data structure to an alternate data
    structure, describing the field that *will* be loaded. This is used to
    compute the columns to select from the database and also by the
    QuerySet class to work out which fields are being initialized on each
    model. Models that have all their fields included aren't mentioned in
    the result, only those that have field restrictions in place.
    """
    field_names, defer = self.deferred_loading
    if not field_names:
        return {}
    mask = {}
    for field_name in field_names:
        part_mask = mask
        for part in field_name.split(LOOKUP_SEP):
            part_mask = part_mask.setdefault(part, {})
    opts = self.get_meta()
    if defer:
        return self._get_defer_select_mask(opts, mask)
    return self._get_only_select_mask(opts, mask)


def get_queryset_select_mask(queryset: QuerySet) -> SelectMask:
    queryset = queryset.defer("id")
    field_dict = queryset.query.select_related
    if isinstance(field_dict, dict):
        queryset = queryset.defer(*[f"{i}__id" for i in flatten_select_related(field_dict=field_dict)])

    # backport django 4.2 get_select_mask
    if not hasattr(queryset.query, "get_select_mask"):
        queryset.query.get_select_mask = get_select_mask.__get__(queryset.query)  # type: ignore
        queryset.query._get_defer_select_mask = _get_defer_select_mask.__get__(queryset.query)  # type: ignore
        queryset.query._get_only_select_mask = _get_only_select_mask.__get__(queryset.query)  # type: ignore

    return queryset.query.get_select_mask()  # type: ignore


@typing.overload
def dunder_to_nest(
    data: JsonDict,
) -> JsonDict:
    pass


@typing.overload
def dunder_to_nest(
    data: SequenceOrValuesJsonDict,
) -> Sequence[JsonDict]:
    pass


def dunder_to_nest(
    data: SequenceOrValuesJsonDict | JsonDict,
) -> Sequence[JsonDict] | JsonDict:
    if not isinstance(data, dict):
        return [dunder_to_nest(i) for i in data]

    dunder_key_list = [k for k in data if LOOKUP_SEP in k]
    for dunder_key in dunder_key_list:
        dender_value = data.pop(dunder_key)
        d = data
        dunder_key_split = dunder_key.split(LOOKUP_SEP)
        for i, part in enumerate(dunder_key_split):
            if i == len(dunder_key_split) - 1:
                d[part] = dender_value
            else:
                d = d.setdefault(part, {})
    return data


def get_queryset_fields(queryset: QuerySet):
    select_mask = get_queryset_select_mask(queryset)
    values_fields = select_mask_to_values_fields(select_mask=select_mask)
    return values_fields


@typing.overload
def model_to_json(
    model: Model,
    fields: list[str],
) -> JsonDict:
    pass


@typing.overload
def model_to_json(
    model: Sequence[Model],
    fields: list[str],
) -> list[JsonDict]:
    pass


def model_to_json(
    model: Model | Sequence[Model],
    fields: list[str],
) -> JsonDict | Sequence[JsonDict]:
    if isinstance(model, Sequence):
        return [model_to_json(i, fields) for i in model]

    data = {}
    for field in fields:
        parts = field.split(LOOKUP_SEP)
        _value = model
        for part in parts:
            _value = getattr(_value, part, None)
            if _value is None:
                break

        if isinstance(_value, Model):
            data[f"{field}_id"] = _value.pk
        else:
            data[field] = _value

    return data
