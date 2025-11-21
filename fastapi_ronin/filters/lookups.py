from datetime import date, datetime
from typing import Dict, List, Type
from uuid import UUID

LOOKUP_EXPRESSIONS = {
    'exact': lambda field, value: {field: value},
    'iexact': lambda field, value: {f'{field}__iexact': value},
    'contains': lambda field, value: {f'{field}__contains': value},
    'icontains': lambda field, value: {f'{field}__icontains': value},
    'startswith': lambda field, value: {f'{field}__startswith': value},
    'istartswith': lambda field, value: {f'{field}__istartswith': value},
    'endswith': lambda field, value: {f'{field}__endswith': value},
    'iendswith': lambda field, value: {f'{field}__iendswith': value},
    'gt': lambda field, value: {f'{field}__gt': value},
    'gte': lambda field, value: {f'{field}__gte': value},
    'lt': lambda field, value: {f'{field}__lt': value},
    'lte': lambda field, value: {f'{field}__lte': value},
    'in': lambda field, value: {f'{field}__in': value},
    'isnull': lambda field, value: {f'{field}__isnull': value},
    'year': lambda field, value: {f'{field}__year': value},
    'month': lambda field, value: {f'{field}__month': value},
    'day': lambda field, value: {f'{field}__day': value},
    'hour': lambda field, value: {f'{field}__hour': value},
    'minute': lambda field, value: {f'{field}__minute': value},
    'second': lambda field, value: {f'{field}__second': value},
}

LOOKUP_TYPES: Dict[str, Type] = {
    'isnull': bool,
    'in': str,
    'year': int,
    'month': int,
    'day': int,
    'hour': int,
    'minute': int,
    'second': int,
}

DEFAULT_ALLOWED_LOOKUPS: Dict[Type, List[str]] = {
    str: [
        'exact',
        'iexact',
        'contains',
        'icontains',
        'startswith',
        'istartswith',
        'endswith',
        'iendswith',
        'in',
        'isnull',
    ],
    int: [
        'exact',
        'gt',
        'gte',
        'lt',
        'lte',
        'in',
        'isnull',
    ],
    float: [
        'exact',
        'gt',
        'gte',
        'lt',
        'lte',
        'in',
        'isnull',
    ],
    UUID: [
        'exact',
        'in',
        'isnull',
    ],
    date: [
        'exact',
        'gt',
        'gte',
        'lt',
        'lte',
        'in',
        'isnull',
        'year',
        'month',
        'day',
    ],
    datetime: [
        'exact',
        'gt',
        'gte',
        'lt',
        'lte',
        'in',
        'isnull',
        'year',
        'month',
        'day',
        'hour',
        'minute',
        'second',
    ],
    bool: [
        'exact',
        'isnull',
    ],
}

ALLOWED_LOOKUPS_BY_TYPE: Dict[Type, set] = {k: set(v) for k, v in DEFAULT_ALLOWED_LOOKUPS.items()}
