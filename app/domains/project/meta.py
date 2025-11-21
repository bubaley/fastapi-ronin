from app.core.models import BASE_FIELDS
from app.domains.company.meta import CompanyMeta
from fastapi_ronin.schemas import SchemaMeta, build_schema_meta


class ProjectMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,
        'name',
        'description',
        'company_id',
    )


class TaskMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,
        'name',
        'project_id',
    )


def get_project_with_tasks_meta():
    return build_schema_meta(
        ProjectMeta,
        ('company', CompanyMeta),
        ('tasks', get_task_with_project_meta()),
    )


def get_task_with_project_meta():
    return build_schema_meta(TaskMeta, ('project', ProjectMeta))
