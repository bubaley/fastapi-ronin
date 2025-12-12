from datetime import datetime

from tortoise.contrib.pydantic import PydanticModel

from app.domains.company.models import Company
from app.domains.project.models import Project, Task
from fastapi_ronin import decorators


class BaseModelSchema(PydanticModel):
    id: int
    created_at: datetime
    updated_at: datetime


# -------------------------------- Company schemas -------------------------------- #


@decorators.schema(model=Company)
class CompanySchema(BaseModelSchema):
    name: str


# -------------------------------- Project schemas -------------------------------- #


@decorators.schema(model=Project)
class ProjectCreateSchema(PydanticModel):
    name: str
    company_id: int


@decorators.schema(model=Project)
class ProjectReadSchema(BaseModelSchema, ProjectCreateSchema):
    company: CompanySchema


# -------------------------------- Task schemas -------------------------------- #


@decorators.schema(model=Task)
class TaskCreateSchema(PydanticModel):
    name: str
    project_id: int


@decorators.schema(model=Task)
class TaskReadSchema(BaseModelSchema, TaskCreateSchema):
    name: str
    project: ProjectReadSchema
