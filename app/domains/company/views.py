from fastapi import APIRouter

from app.core.viewsets import BaseModelViewSet
from app.domains.company.filters import CompanyFilterSet
from app.domains.company.models import Company
from app.domains.company.schemas import CompanyCreateSchema, CompanySchema
from fastapi_ronin.decorators import action, viewset
from fastapi_ronin.permissions import IsAuthenticated

router = APIRouter(prefix='/companies', tags=['companies'])


@viewset(router)
class CompanyViewSet(BaseModelViewSet[Company]):
    model = Company
    read_schema = CompanySchema
    create_schema = CompanyCreateSchema
    filterset_class = CompanyFilterSet

    # permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not self.user:
            return Company.filter(id__lte=3)
        return Company.all()

    def get_permissions(self):
        if self.action in ('stats', 'list'):
            return []
        return [IsAuthenticated()]

    async def perform_save(self, obj):
        return await super().perform_save(obj)

    @action(methods=['GET'], detail=False)
    async def stats(self):
        return 'Hello World!'
