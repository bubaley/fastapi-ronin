from app.domains.company.models import Company, CompanyStatus
from fastapi_ronin import filters


class CompanyFilterSet(filters.FilterSet):
    fields = [
        filters.CharFilter('name', view_name='search', default_lookup='icontains'),
        filters.IntegerFilter('id', lookups=['in', 'gte', 'lte']),
        filters.BooleanFilter('name', default_lookup='isnull', exclude=True),
        filters.ChoiceFilter('status', choices=CompanyStatus),
    ]

    class Meta:
        model = Company
