import inspect
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, Union
from uuid import UUID

from fastapi import Query
from tortoise.queryset import QuerySet

from fastapi_ronin.filters.lookups import ALLOWED_LOOKUPS_BY_TYPE, LOOKUP_EXPRESSIONS, LOOKUP_TYPES


@dataclass
class Parameter:
    param_name: str
    field_name: str
    view_name: str
    lookup: str
    negate: bool
    filter: 'Filter'
    annotation: Type[Any]
    field_attrs: Dict[str, Any] = field(default_factory=dict)


class Filter:
    field_type: Type | None

    def __init__(
        self,
        field_name: str | None = None,
        lookups: Optional[List[str]] = None,
        required: bool = False,
        exclude: bool = False,
        view_name: Optional[str] = None,
        default: Any = None,
        default_lookup: Optional[str] = None,
        description: Optional[str] = None,
        method: Optional[str] = None,
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
        self.method = method
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

    def get_param_definitions(self) -> List[Parameter]:
        defs: List[Parameter] = []
        for lookup in self.lookups:
            display_token = f'not_{lookup}' if self.exclude else lookup
            annotation = LOOKUP_TYPES.get(lookup, self.field_type)
            param_name, negate_flag = self._resolve_param_name(lookup, display_token)
            param_def = Parameter(
                param_name=param_name,
                negate=negate_flag,
                annotation=Optional[annotation],  # type:ignore
                filter=self,
                view_name=self.view_name,
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


OrderingFieldSpec = Union[str, Tuple[str, str]]


@dataclass
class OrderingField:
    param_name: str
    field_name: str


class OrderingFilter:
    """Ordering filter similar to django-filter's OrderingFilter.

    ``fields`` accepts field names or ``(param_name, field_name)`` tuples.
    Use a leading ``-`` in the query value for descending order, e.g.
    ``?ordering=name,-created``.
    """

    def __init__(
        self,
        fields: Sequence[OrderingFieldSpec],
        param_name: str = 'ordering',
        default: Optional[Sequence[str]] = None,
        description: Optional[str] = None,
    ):
        if not fields:
            raise ValueError('fields must contain at least one ordering field')

        self.param_name = param_name
        self.default = list(default) if default is not None else None
        self.description = description or 'Which field to use when ordering the results.'
        self._fields = self._normalize_fields(fields)
        self._param_to_field = {field.param_name: field.field_name for field in self._fields}

    @staticmethod
    def _normalize_fields(fields: Sequence[OrderingFieldSpec]) -> List[OrderingField]:
        normalized: List[OrderingField] = []

        for item in fields:
            if isinstance(item, str):
                normalized.append(OrderingField(param_name=item, field_name=item))
                continue

            if isinstance(item, (tuple, list)) and len(item) == 2:
                param_name, field_name = item
                if not isinstance(param_name, str) or not isinstance(field_name, str):
                    raise ValueError('Ordering field tuple must contain two strings')
                normalized.append(OrderingField(param_name=param_name, field_name=field_name))
                continue

            raise ValueError(
                'Ordering fields must be strings or (param_name, field_name) tuples'
            )

        param_names = [field.param_name for field in normalized]
        if len(param_names) != len(set(param_names)):
            raise ValueError('Duplicate ordering parameter names are not allowed')

        return normalized

    def get_query_attrs(self) -> Dict[str, Any]:
        allowed = ', '.join(sorted(self._param_to_field))
        return {
            'default': None,
            'description': f'{self.description} Allowed values: {allowed}. '
            'Prefix with "-" for descending order. Multiple fields may be comma-separated.',
        }

    def resolve_ordering(self, value: Optional[str], model: Optional[Type[Any]] = None) -> List[str]:
        if value:
            return self._resolve_value(value)

        if self.default is not None:
            return self._resolve_value(','.join(self.default))

        if model is not None:
            model_ordering = getattr(getattr(model, 'Meta', None), 'ordering', None)
            if model_ordering:
                return list(model_ordering)

        return []

    def _resolve_value(self, value: str) -> List[str]:
        order_by: List[str] = []

        for part in (item.strip() for item in value.split(',') if item.strip()):
            descending = part.startswith('-')
            param_name = part[1:] if descending else part

            field_name = self._param_to_field.get(param_name)
            if field_name is None:
                raise ValueError(
                    f"Invalid ordering field '{param_name}'. "
                    f'Allowed values: {", ".join(sorted(self._param_to_field))}'
                )

            order_by.append(f'-{field_name}' if descending else field_name)

        return order_by


class FilterSetMeta(Type):
    def __new__(mcs, name, bases, namespace, **kwargs):
        filters: List[Filter] = namespace.get('fields', [])
        if not isinstance(filters, list):
            raise ValueError('fields must be a list of Filter objects')

        param_map: Dict[str, Parameter] = {}
        ordering_filter: Optional[OrderingFilter] = namespace.get('ordering')

        for f in filters:
            if isinstance(f, OrderingFilter):
                if ordering_filter is not None:
                    raise ValueError('Only one OrderingFilter is allowed per FilterSet')
                ordering_filter = f
                continue

            if not isinstance(f, Filter):
                raise ValueError('All elements of fields must be Filter or OrderingFilter instances')

            for d in f.get_param_definitions():
                pname = d.param_name
                if pname in param_map:
                    raise ValueError(f'Duplicate query parameter: {pname}')
                param_map[pname] = d

        if ordering_filter is not None and ordering_filter.param_name in param_map:
            raise ValueError(f'Duplicate query parameter: {ordering_filter.param_name}')

        namespace['_param_map'] = param_map
        namespace['_ordering_filter'] = ordering_filter

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
        param_map: Dict[str, Parameter] = getattr(cls, '_param_map', {})

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

        ordering_filter: Optional[OrderingFilter] = getattr(cls, '_ordering_filter', None)
        if ordering_filter is not None:
            parameters.append(
                inspect.Parameter(
                    name=ordering_filter.param_name,
                    kind=inspect.Parameter.KEYWORD_ONLY,
                    default=Query(**ordering_filter.get_query_attrs()),
                    annotation=Optional[str],
                )
            )

        setattr(build, '__signature__', inspect.Signature(parameters))
        return build

    def _get_model(self) -> Optional[Type[Any]]:
        meta = getattr(self, 'Meta', None)
        return getattr(meta, 'model', None) if meta else None

    def filter_queryset(self, queryset: QuerySet) -> QuerySet:
        param_map: Dict[str, Parameter] = getattr(self, '_param_map', {})

        for pname, raw_value in self.data.items():
            parameter: Optional[Parameter] = param_map.get(pname)
            if not parameter or raw_value is None:
                continue

            processed = parameter.filter._process_value(raw_value, parameter.lookup)
            if processed is None:
                continue

            if parameter.filter.method:
                method = getattr(self, parameter.filter.method, None)
                if method and callable(method):
                    result = method(queryset=queryset, value=processed, parameter=parameter)
                    if isinstance(result, QuerySet):
                        queryset = result
            else:
                queryset = self.filter_by_parameter(queryset, processed, parameter)

        ordering_filter: Optional[OrderingFilter] = getattr(self.__class__, '_ordering_filter', None)
        if ordering_filter is not None:
            raw_ordering = self.data.get(ordering_filter.param_name)
            order_by = ordering_filter.resolve_ordering(raw_ordering, model=self._get_model())
            if order_by:
                queryset = queryset.order_by(*order_by)

        return queryset

    def filter_by_parameter(self, queryset: QuerySet, value: Any, parameter: Parameter) -> QuerySet:
        kwargs = LOOKUP_EXPRESSIONS[parameter.lookup](parameter.field_name, value)
        queryset = queryset.exclude(**kwargs) if parameter.negate else queryset.filter(**kwargs)
        return queryset


class EmptyFilterSet(FilterSet):
    pass
