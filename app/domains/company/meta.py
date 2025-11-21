from app.core.models import BASE_FIELDS
from fastapi_ronin.schemas import SchemaMeta


class CompanyMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,
        'name',
        'full_name',
        'status',
    )
