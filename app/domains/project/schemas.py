from typing import TYPE_CHECKING

from tortoise.contrib.pydantic import PydanticModel

from app.domains.project.meta import get_project_with_tasks_meta, get_task_with_project_meta
from app.domains.project.models import Project, Task
from fastapi_ronin.schemas import ConfigSchemaMeta, build_schema, rebuild_schema

ProjectReadSchema = build_schema(
    Project,
    meta=get_project_with_tasks_meta(),
    config=ConfigSchemaMeta(allow_cycles=True),
)

ProjectCreateSchema = rebuild_schema(
    ProjectReadSchema,
    exclude_readonly=True,
)


TaskReadSchema = build_schema(Task, meta=get_task_with_project_meta())
TaskCreateSchema = rebuild_schema(TaskReadSchema, exclude_readonly=True)


if TYPE_CHECKING:
    ProjectReadSchema = type('ProjectCreateSchema', (Project, PydanticModel), {})
    ProjectCreateSchema = type('ProjectCreateSchema', (Project, PydanticModel), {})

    TaskReadSchema = type('TaskReadSchema', (Task, PydanticModel), {})
    TaskCreateSchema = type('TaskCreateSchema', (Task, PydanticModel), {})
