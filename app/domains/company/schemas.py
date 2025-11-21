from app.domains.company.meta import CompanyMeta
from app.domains.company.models import Company
from fastapi_ronin.schemas import build_schema, rebuild_schema

CompanySchema = build_schema(Company, meta=CompanyMeta)
CompanyCreateSchema = rebuild_schema(CompanySchema, exclude_readonly=True)
