from fastapi import APIRouter

from app.core.viewsets import BaseModelViewSet
from app.domains.project.models import Project, Task
from app.domains.project.schemas import (
    ProjectCreateSchema,
    ProjectReadSchema,
    TaskCreateSchema,
    TaskReadSchema,
)
from fastapi_ronin import decorators
from fastapi_ronin.pagination import DisabledPagination
from fastapi_ronin.viewsets import ModelViewSet

router = APIRouter(prefix='/projects', tags=['projects'])


@decorators.viewset(router)
class ProjectViewSet(BaseModelViewSet[Project]):
    model = Project
    read_schema = ProjectReadSchema
    create_schema = ProjectCreateSchema


task_router = APIRouter(prefix='/tasks', tags=['tasks'])


@decorators.viewset(task_router)
class TaskViewSet(ModelViewSet[Task]):
    model = Task
    read_schema = TaskReadSchema
    create_schema = TaskCreateSchema

    pagination = DisabledPagination
    list_wrapper = None
    single_wrapper = None

    @decorators.action(response_model=list[TaskReadSchema])
    async def list(self, project_id: int):
        queryset = Task.filter(project_id=project_id)
        return await TaskReadSchema.from_queryset(queryset)
