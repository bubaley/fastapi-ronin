---
title: FastAPI Ronin Filters — Query Parameters for Tortoise ORM
description: Build typed query parameters for FastAPI Ronin ViewSets and apply them to Tortoise ORM querysets with filters, lookups, custom methods, and ordering.
keywords: FastAPI filters, Tortoise ORM filters, FastAPI Ronin, query parameters, ordering, REST API filtering
---

# Filters

Filters turn query parameters into Tortoise ORM queryset operations. You define a
`FilterSet`, attach it to a ViewSet, and Ronin exposes typed FastAPI query
parameters automatically.

## Quick Example

```python
from tortoise.expressions import Q
from tortoise.queryset import QuerySet

from app.domains.company.models import Company
from fastapi_ronin.filters import CharFilter, DateTimeFilter, FilterSet, OrderingFilter, Parameter


class CompanyFilterSet(FilterSet):
    fields = [
        CharFilter(field_name='name', view_name='search_by_name', lookup_expr='icontains'),
        CharFilter(field_name='search', method='filter_by_search'),
        DateTimeFilter(field_name='created_at', lookups=['gte', 'lte', 'exact']),
        DateTimeFilter(field_name='updated_at', lookups=['gte', 'lte', 'exact']),
    ]
    ordering = OrderingFilter(
        fields=(
            'name',
            ('created', 'created_at'),
            ('updated', 'updated_at'),
        ),
        default=('-created',),
    )

    def filter_by_search(self, queryset: QuerySet[Company], value: str, parameter: Parameter):
        return queryset.filter(Q(name__icontains=value) | Q(full_name__icontains=value))

    class Meta:
        model = Company
```

Attach it to a ViewSet:

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema
    filterset_class = CompanyFilterSet
```

Example requests:

```text
GET /companies/?search_by_name=acme
GET /companies/?search=acme
GET /companies/?created_at__gte=2026-01-01T00:00:00
GET /companies/?ordering=-updated
```

## Filter Types

| Filter | Python Type | Common Lookups |
|--------|-------------|----------------|
| `CharFilter` | `str` | `exact`, `iexact`, `contains`, `icontains`, `startswith`, `istartswith`, `endswith`, `iendswith`, `in`, `isnull` |
| `IntegerFilter` | `int` | `exact`, `gt`, `gte`, `lt`, `lte`, `in`, `isnull` |
| `FloatFilter` | `float` | `exact`, `gt`, `gte`, `lt`, `lte`, `in`, `isnull` |
| `BooleanFilter` | `bool` | `exact`, `isnull` |
| `DateFilter` | `date` | `exact`, `gt`, `gte`, `lt`, `lte`, `in`, `isnull`, `year`, `month`, `day` |
| `DateTimeFilter` | `datetime` | date lookups plus `hour`, `minute`, `second` |
| `UUIDFilter` | `UUID` | `exact`, `in`, `isnull` |
| `ChoiceFilter` | enum | `exact` by default |

## Parameter Naming

By default, exact filters use the field name:

```python
CharFilter(field_name='name')
```

```text
GET /companies/?name=Acme
```

Multiple lookups add a suffix:

```python
IntegerFilter(field_name='id', lookups=['in', 'gte', 'lte'])
```

```text
GET /companies/?id__in=1,2,3
GET /companies/?id__gte=10
GET /companies/?id__lte=100
```

Use `view_name` to expose a different query parameter name:

```python
CharFilter(field_name='name', view_name='q', lookup_expr='icontains')
```

```text
GET /companies/?q=acme
```

`lookup_expr` is a convenience alias for the default lookup. It keeps the query
parameter short while applying a non-exact lookup. `default_lookup` is still
accepted for compatibility.

## Custom Filter Methods

Use `method` when one parameter needs custom queryset logic:

```python
class CompanyFilterSet(FilterSet):
    fields = [
        CharFilter(field_name='search', method='filter_by_search'),
    ]

    def filter_by_search(self, queryset: QuerySet[Company], value: str, parameter: Parameter):
        return queryset.filter(Q(name__icontains=value) | Q(full_name__icontains=value))

    class Meta:
        model = Company
```

The method receives the current queryset, the parsed value, and the generated
parameter metadata.

## Negation

Use `exclude=True` to invert a filter:

```python
BooleanFilter(field_name='archived', exclude=True)
```

```text
GET /companies/?archived__not_exact=true
```

For a shorter negated parameter, use `default_lookup='not_exact'`:

```python
BooleanFilter(field_name='archived', exclude=True, default_lookup='not_exact')
```

```text
GET /companies/?archived=true
```

## Ordering

`OrderingFilter` maps public ordering names to model fields.

```python
ordering = OrderingFilter(
    fields=(
        'name',
        ('created', 'created_at'),
        ('updated', 'updated_at'),
    ),
    default=('-created',),
)
```

```text
GET /companies/?ordering=name
GET /companies/?ordering=-updated
GET /companies/?ordering=name,-created
```

If no `ordering` parameter is provided, Ronin uses the filter default. If there
is no filter default, it falls back to the model `Meta.ordering` when available.

## Required Parameters

Set `required=True` when a filter must be present:

```python
CharFilter(field_name='tenant_id', required=True)
```

FastAPI will document and validate the required query parameter.

## Design Guidance

- Keep public query names stable even if model field names change.
- Use `lookup_expr` for the common “short parameter with non-exact lookup” case.
- Use explicit `lookups` when the API should expose several operators.
- Use custom methods for search boxes and business-specific filtering.
- Define filters in the same domain as the ViewSet that uses them.
