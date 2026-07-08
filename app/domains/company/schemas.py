from datetime import datetime

from tortoise.contrib.pydantic import PydanticModel

from app.domains.company.models import Company
from fastapi_ronin.decorators import schema


@schema(model=Company)
class CompanyCreateSchema(PydanticModel):
    name: str
    full_name: str | None = None
    status: str | None = None


@schema(model=Company)
class CompanySchema(CompanyCreateSchema):
    id: int
    created_at: datetime
    updated_at: datetime
