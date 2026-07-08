# main.py - Complete FastAPI Ronin application
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import APIRouter, FastAPI
from pydantic import BaseModel
from tortoise import fields
from tortoise.contrib.fastapi import register_tortoise
from tortoise.contrib.pydantic import PydanticModel
from tortoise.expressions import Q
from tortoise.models import Model
from tortoise.queryset import QuerySet

from fastapi_ronin.cache import cache
from fastapi_ronin.decorators import action, schema, viewset
from fastapi_ronin.filters import CharFilter, DateTimeFilter, FilterSet, OrderingFilter, Parameter
from fastapi_ronin.pagination import PageNumberPagination
from fastapi_ronin.viewsets import ModelViewSet
from fastapi_ronin.wrappers import PaginatedResponseDataWrapper, ResponseDataWrapper


# Database setup
def register_database(app: FastAPI):
    register_tortoise(
        app,
        db_url='sqlite://db.sqlite3',
        modules={'models': ['main']},
        generate_schemas=True,
        add_exception_handlers=True,
    )


# Models
class Company(Model):
    id = fields.IntField(primary_key=True)
    name = fields.CharField(max_length=255)
    full_name = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)


# Schemas
@schema(Company)
class CompanyCreateSchema(PydanticModel):
    name: str
    full_name: str | None


@schema(Company)
class CompanyReadSchema(CompanyCreateSchema):
    id: int
    created_at: datetime
    updated_at: datetime


class StatsSchema(BaseModel):
    total: int
    called_cache: int = 0


# Filters


class CompanyFilterSet(FilterSet):
    fields = [
        CharFilter(field_name='name', view_name='search_by_name', lookup_expr='icontains'),
        CharFilter(field_name='search', method='filter_by_search'),
        DateTimeFilter(field_name='created_at', lookups=['gte', 'lte', 'exact']),
        DateTimeFilter(field_name='updated_at', lookups=['gte', 'lte', 'exact']),
    ]
    ordering = OrderingFilter(
        fields=(
            'name',
            ('created', 'created_at'),
            ('updated', 'updated_at'),
        ),
        default=('-created',),
    )

    def filter_by_search(self, queryset: QuerySet[Company], value: str, parameter: Parameter):
        return queryset.filter(Q(name__icontains=value) | Q(full_name__icontains=value))

    class Meta:
        model = Company


# Views
router = APIRouter(prefix='/companies', tags=['companies'])


@viewset(router)
class CompanyViewSet(ModelViewSet[Company]):
    model = Company
    create_schema = CompanyCreateSchema
    read_schema = CompanyReadSchema

    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
    single_wrapper = ResponseDataWrapper
    filterset_class = CompanyFilterSet

    @action(methods=['GET'], detail=False)
    async def stats(self) -> StatsSchema:
        called = (await cache.get('stats:call') or 0) + 1
        await cache.set('stats:call', called)
        return StatsSchema(total=await Company.all().count(), called_cache=called)


# Application


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""

    await cache.init(None)
    # await cache.init(redis_url='redis://localhost:6379/0') # for redis cache
    yield
    await cache.close()


app = FastAPI(title='My API', lifespan=lifespan)
register_database(app)
app.include_router(router)
