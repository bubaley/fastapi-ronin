from datetime import datetime

from tortoise.contrib.pydantic import PydanticModel

from app.domains.company.models import Company
from app.domains.project.models import Project, Task
from fastapi_ronin.decorators import schema


class BaseModelSchema(PydanticModel):
    id: int
    created_at: datetime
    updated_at: datetime


# -------------------------------- Company schemas -------------------------------- #


@schema(model=Company)
class CompanySchema(BaseModelSchema):
    name: str


# -------------------------------- Project schemas -------------------------------- #


@schema(model=Project)
class ProjectCreateSchema(PydanticModel):
    name: str
    company_id: int


@schema(model=Project)
class ProjectReadSchema(BaseModelSchema, ProjectCreateSchema):
    company: CompanySchema


# -------------------------------- Task schemas -------------------------------- #


@schema(model=Task)
class TaskCreateSchema(PydanticModel):
    name: str
    project_id: int


@schema(model=Task)
class TaskReadSchema(BaseModelSchema, TaskCreateSchema):
    name: str
    project: ProjectReadSchema
