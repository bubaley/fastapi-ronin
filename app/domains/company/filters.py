from app.domains.company.models import Company, CompanyStatus
from fastapi_ronin import filters


class CompanyFilterSet(filters.FilterSet):
    fields = [
        filters.CharFilter('name', view_name='search', default_lookup='icontains'),
        filters.IntegerFilter('id', lookups=['in', 'gte', 'lte']),
        filters.BooleanFilter('name', default_lookup='isnull', exclude=True),
        filters.ChoiceFilter('status', choices=CompanyStatus, lookups=['exact', 'isnull'], method='by_status'),
    ]

    class Meta:
        model = Company

    def by_status(self, queryset, value: CompanyStatus, parameter: filters.Parameter):
        return self.filter_by_parameter(queryset, value, parameter)
