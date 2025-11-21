---
title: FastAPI Filters — Powerful QuerySet Filtering with FastAPI Ronin
description: Master FastAPI Ronin's advanced filtering system for building complex API queries. Leverage Django ORM-inspired lookups, custom filter types, and automatic query parameter generation for efficient data retrieval.
keywords: FastAPI filters, API filtering, QuerySet filtering, Django ORM lookups, FastAPI Ronin, Python API development, query parameters, REST API filtering, data filtering, search functionality
---

# API Filters: Advanced QuerySet Filtering

FastAPI Ronin provides a powerful filtering system that allows you to create sophisticated query interfaces for your API endpoints. The system is inspired by Django ORM lookups and provides automatic query parameter generation, type validation, and QuerySet filtering.

## Overview

The filtering system consists of:

1. **Filter Classes** - Define individual filter fields with specific types and behaviors
2. **FilterSet Classes** - Group multiple filters for a model
3. **Lookup Types** - Various comparison operators (exact, contains, gte, etc.)
4. **Automatic Integration** - Seamless integration with ViewSets and FastAPI

## Quick Start

Here's a simple example of creating and using filters:

```python
from fastapi_ronin import filters
from app.models import Company, CompanyStatusEnum

class CompanyFilterSet(filters.FilterSet):
    fields = [
        filters.CharFilter('name', view_name='search', default_lookup='icontains'),
        filters.IntegerFilter('id', lookups=['in', 'gte', 'lte']),
        filters.BooleanFilter('is_active', exclude=True),
        filters.ChoiceFilter('status', choices=CompanyStatusEnum),
    ]

    class Meta:
        model = Company
```

Then in your ViewSet:

```python
from fastapi_ronin.decorators import viewset
from fastapi_ronin.viewsets import ModelViewSet

@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema
    filterset_class = CompanyFilterSet
```

This automatically generates query parameters like:
- `?search=acme` (searches for companies containing "acme" in name)
- `?id__in=1,2,3` (companies with IDs 1, 2, or 3)
- `?id__gte=10` (companies with ID >= 10)
- `?is_active=true` (active companies only)
- `?status=active` (companies with active status)

## Filter Types

### CharFilter

For text-based filtering:

```python
filters.CharFilter('name', lookups=['exact', 'icontains', 'startswith'])
```

**Available lookups**: `exact`, `iexact`, `contains`, `icontains`, `startswith`, `istartswith`, `endswith`, `iendswith`, `in`, `isnull`

### IntegerFilter

For numeric filtering:

```python
filters.IntegerFilter('age', lookups=['gte', 'lte', 'in'])
```

**Available lookups**: `exact`, `gt`, `gte`, `lt`, `lte`, `in`, `isnull`

### FloatFilter

For decimal number filtering:

```python
filters.FloatFilter('price', lookups=['gte', 'lte'])
```

**Available lookups**: `exact`, `gt`, `gte`, `lt`, `lte`, `in`, `isnull`

### BooleanFilter

For boolean field filtering:

```python
filters.BooleanFilter('is_active', default_lookup='exact')
```

**Available lookups**: `exact`, `isnull`

### DateFilter & DateTimeFilter

For date and datetime filtering:

```python
filters.DateFilter('created_date', lookups=['gte', 'lte', 'year'])
filters.DateTimeFilter('updated_at', lookups=['gte', 'lte'])
```

**Available lookups**: `exact`, `gt`, `gte`, `lt`, `lte`, `in`, `isnull`, `year`, `month`, `day`

For DateTimeFilter also: `hour`, `minute`, `second`

### UUIDFilter

For UUID field filtering:

```python
filters.UUIDFilter('uuid', lookups=['exact', 'in'])
```

**Available lookups**: `exact`, `in`, `isnull`

### ChoiceFilter

For enum/choice field filtering:

```python
from enum import Enum

class CompanyStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    PENDING = "pending"

filters.ChoiceFilter('status', choices=CompanyStatus)
```

## Lookup Types Explained

### Text Lookups

- `exact` - Exact match (case-sensitive)
- `iexact` - Exact match (case-insensitive)
- `contains` - Contains substring (case-sensitive)
- `icontains` - Contains substring (case-insensitive)
- `startswith` - Starts with text (case-sensitive)
- `istartswith` - Starts with text (case-insensitive)
- `endswith` - Ends with text (case-sensitive)
- `iendswith` - Ends with text (case-insensitive)

### Comparison Lookups

- `gt` - Greater than
- `gte` - Greater than or equal
- `lt` - Less than
- `lte` - Less than or equal

### List & Null Lookups

- `in` - Value is in list (comma-separated for strings)
- `isnull` - Field is null (true) or not null (false)

### Date/Time Lookups

- `year` - Extract year from date/datetime
- `month` - Extract month from date/datetime
- `day` - Extract day from date/datetime
- `hour` - Extract hour from datetime
- `minute` - Extract minute from datetime
- `second` - Extract second from datetime

## Advanced Features

### Default Lookup

Set a default lookup to simplify parameter names:

```python
# Without default_lookup: ?name__icontains=acme
filters.CharFilter('name', lookups=['exact', 'icontains'])

# With default_lookup: ?search=acme (uses icontains by default)
filters.CharFilter('name', view_name='search', default_lookup='icontains', lookups=['exact', 'icontains'])
```

### Custom Parameter Names

Use `view_name` to customize query parameter names:

```python
filters.CharFilter('company_name', view_name='name')
# Creates parameter: ?name=acme instead of ?company_name=acme
```

### Exclude (Negation)

Use `exclude=True` to invert the filter logic:

```python
filters.BooleanFilter('is_deleted', exclude=True, default_lookup='exact')
# ?is_deleted=true will filter for records where is_deleted != true
```

### Required Filters

Make filters mandatory:

```python
filters.CharFilter('category', required=True)
# API will return error if category parameter is not provided
```

### Multiple Lookups

Enable multiple filtering options for the same field:

```python
filters.IntegerFilter('price', lookups=['exact', 'gte', 'lte', 'in'])
```

This generates parameters:
- `?price=100` (exact match)
- `?price__gte=50` (price >= 50)
- `?price__lte=200` (price <= 200)
- `?price__in=100,150,200` (price in list)

## Complex Filtering Examples

### E-commerce Product Filtering

```python
class ProductFilterSet(filters.FilterSet):
    fields = [
        # Text search in name and description
        filters.CharFilter('name', view_name='search', default_lookup='icontains'),

        # Price range filtering
        filters.FloatFilter('price', lookups=['gte', 'lte']),

        # Category selection
        filters.ChoiceFilter('category', choices=ProductCategory),

        # Availability filtering
        filters.BooleanFilter('in_stock'),

        # Date filtering
        filters.DateFilter('created_at', lookups=['gte', 'lte', 'year']),

        # Brand filtering (multiple selection)
        filters.IntegerFilter('brand_id', lookups=['in']),

        # Exclude out-of-stock items
        filters.BooleanFilter('is_available', exclude=True, default_lookup='isnull'),
    ]

    class Meta:
        model = Product
```

Usage examples:
- `?search=laptop` - Search for laptops
- `?price__gte=500&price__lte=2000` - Price between $500-$2000
- `?category=electronics&in_stock=true` - Electronics in stock
- `?brand_id__in=1,3,5` - Products from brands 1, 3, or 5
- `?created_at__year=2024` - Products created in 2024

### User Filtering with Relationships

```python
class UserFilterSet(filters.FilterSet):
    fields = [
        # Basic user info
        filters.CharFilter('email', lookups=['exact', 'icontains']),
        filters.CharFilter('first_name', view_name='name', default_lookup='icontains'),

        # Age filtering
        filters.IntegerFilter('age', lookups=['gte', 'lte']),

        # Status filtering
        filters.BooleanFilter('is_active'),
        filters.ChoiceFilter('role', choices=UserRole),

        # Registration date
        filters.DateTimeFilter('created_at', lookups=['gte', 'lte']),

        # Relationship filtering (requires proper model setup)
        filters.IntegerFilter('company_id', lookups=['exact', 'in']),
    ]

    class Meta:
        model = User
```

## Integration with ViewSets

### Basic Integration

```python
@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema
    filterset_class = CompanyFilterSet  # Add your FilterSet here
```
