import inspect
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Type
from uuid import UUID

from fastapi import Query
from tortoise.queryset import QuerySet

from fastapi_ronin.filters.lookups import ALLOWED_LOOKUPS_BY_TYPE, LOOKUP_EXPRESSIONS, LOOKUP_TYPES


@dataclass
class ParameterDefinition:
    param_name: str
    field_name: str
    lookup: str
    negate: bool
    filter: 'Filter'
    annotation: Type[Any]
    field_attrs: Dict[str, Any] = field(default_factory=dict)


class Filter:
    field_type: Type | None

    def __init__(
        self,
        field_name: str,
        lookups: Optional[List[str]] = None,
        required: bool = False,
        exclude: bool = False,
        view_name: Optional[str] = None,
        default: Any = None,
        default_lookup: Optional[str] = None,
        description: Optional[str] = None,
        _field_attrs: Optional[Dict[str, Any]] = None,
        _field_type: Optional[Type] = None,
        **kwargs,
    ):
        if not field_name:
            raise ValueError('field_name is required')

        self.field_name = field_name
        self.field_type = _field_type or self.field_type
        self.view_name = view_name or field_name.replace('.', '__')
        self.default_lookup = default_lookup
        self.lookups = lookups or [self.default_lookup or 'exact']
        self.required = required
        self.exclude = exclude
        self.field_attrs = {
            'description': description,
            'default': default or ... if (self.required and len(self.lookups) == 1) else None,
            **(_field_attrs or {}),
        }
        self.kwargs = kwargs

        self._validate()

    def _validate(self):
        invalid = set(self.lookups) - set(LOOKUP_EXPRESSIONS.keys())
        if invalid:
            raise ValueError(f'Unsupported lookups: {invalid}')
        if not self.field_type:
            raise ValueError('Invalid field type')

        allowed = ALLOWED_LOOKUPS_BY_TYPE.get(self.field_type)
        if allowed is not None:
            bad = set(self.lookups) - allowed
            if bad:
                raise ValueError(f'Lookups {bad} not allowed for {self.field_type}')

        if self.default_lookup:
            token = self.default_lookup.removeprefix('not_')
            if token not in self.lookups:
                raise ValueError(f"default_lookup '{self.default_lookup}' not in lookups {self.lookups}")

    def get_param_definitions(self) -> List[ParameterDefinition]:
        defs: List[ParameterDefinition] = []
        for lookup in self.lookups:
            display_token = f'not_{lookup}' if self.exclude else lookup
            annotation = LOOKUP_TYPES.get(lookup, self.field_type)
            param_name, negate_flag = self._resolve_param_name(lookup, display_token)
            param_def = ParameterDefinition(
                param_name=param_name,
                negate=negate_flag,
                annotation=Optional[annotation],  # type:ignore
                filter=self,
                field_attrs=self.field_attrs,
                field_name=self.field_name,
                lookup=lookup,
            )
            defs.append(param_def)
        return defs

    def _resolve_param_name(self, lookup: str, display_token: str) -> Tuple[str, bool]:
        if self.default_lookup:
            def_neg = self.default_lookup.startswith('not_')
            def_lookup = self.default_lookup.removeprefix('not_')
            if def_lookup == lookup and def_neg == self.exclude:
                return self.view_name, def_neg
        if lookup == 'exact' and not self.exclude:
            return self.view_name, False
        return f'{self.view_name}__{display_token}', self.exclude

    def _process_value(self, value: Any, lookup: str) -> Any:
        if value is None:
            return None
        if lookup == 'in' and isinstance(value, str):
            return [item.strip() for item in value.split(',') if item.strip()]
        return value


class CharFilter(Filter):
    field_type = str


class IntegerFilter(Filter):
    field_type = int


class FloatFilter(Filter):
    field_type = float


class BooleanFilter(Filter):
    field_type = bool


class DateFilter(Filter):
    field_type = date


class DateTimeFilter(Filter):
    field_type = datetime


class UUIDFilter(Filter):
    field_type = UUID


class ChoiceFilter(Filter):
    field_type = None

    def __init__(self, field_name: str, choices: Type[Enum], **kwargs):
        super().__init__(field_name, _field_type=choices, **kwargs)


class FilterSetMeta(Type):
    def __new__(mcs, name, bases, namespace, **kwargs):
        filters: List[Filter] = namespace.get('fields', [])
        if not isinstance(filters, list):
            raise ValueError('fields must be a list of Filter objects')

        param_map: Dict[str, ParameterDefinition] = {}
        for f in filters:
            if not isinstance(f, Filter):
                raise ValueError('All elements of fields must be Filter instances')
            for d in f.get_param_definitions():
                pname = d.param_name
                if pname in param_map:
                    raise ValueError(f'Duplicate query parameter: {pname}')
                param_map[pname] = d
        namespace['_param_map'] = param_map

        return super().__new__(mcs, name, bases, namespace)


class FilterSet(metaclass=FilterSetMeta):
    fields: List[Filter] = []

    def __init__(self, data: Optional[Dict[str, Any]] = None):
        self.data = data or {}
        self._validate_model()

    def _validate_model(self):
        meta = getattr(self, 'Meta', None)
        if (not meta or not getattr(meta, 'model', None)) and not isinstance(self, EmptyFilterSet):
            raise ValueError(f'Meta.model must be specified for {self.__class__.__name__}')

    @classmethod
    def get_build(cls):
        param_map: Dict[str, ParameterDefinition] = getattr(cls, '_param_map', {})

        def build(**kwargs):
            data = {k: v for k, v in kwargs.items() if v is not None}
            return cls(data=data)

        parameters = [
            inspect.Parameter(
                name=field_name,
                kind=inspect.Parameter.KEYWORD_ONLY,
                default=Query(**field.field_attrs),
                annotation=field.annotation,
            )
            for field_name, field in param_map.items()
        ]

        build.__signature__ = inspect.Signature(parameters)
        return build

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        param_map: Dict[str, ParameterDefinition] = getattr(self, '_param_map', {})

        for pname, raw_value in self.data.items():
            info: Optional[ParameterDefinition] = param_map.get(pname)
            if not info or raw_value is None:
                continue

            processed = info.filter._process_value(raw_value, info.lookup)
            if processed is None:
                continue

            kwargs = LOOKUP_EXPRESSIONS[info.lookup](info.field_name, processed)
            queryset = queryset.exclude(**kwargs) if info.negate else queryset.filter(**kwargs)
        return queryset


class EmptyFilterSet(FilterSet):
    pass
