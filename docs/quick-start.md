---
title: FastAPI Ronin Tutorial — Quick Start Guide to Building REST APIs
description: Learn how to build a scalable FastAPI Ronin project in minutes with ViewSets, explicit schemas, filters, pagination, wrappers, cache, and Tortoise ORM.
keywords: FastAPI tutorial, FastAPI Ronin tutorial, REST API guide, Python REST API tutorial, Django REST Framework patterns, CRUD API FastAPI, ViewSets FastAPI, Python backend development
---

# FastAPI Ronin Quick Start: Build a Scalable API in Minutes

The root `main.py` shows a complete app in one file. This guide takes the same
ideas and turns them into a project layout you can keep growing: shared `core`
modules, domain modules, explicit schemas, filters, ViewSets, wrappers, cache,
and Tortoise ORM.

!!! tip "Start small, keep the shape"
    You can begin with one domain and one ViewSet. The structure below pays off
    when you add a second or third domain because every concern already has a
    clear place.

## 📦 Installation

Create a project and install the core dependencies:

```bash
mkdir project-api
cd project-api
uv init
uv add fastapi-ronin fastapi tortoise-orm uvicorn pydantic-settings
```

For Redis-backed cache:

```bash
uv add "fastapi-ronin[redis]"
```

## 🏗️ Recommended Project Structure

Use a domain-oriented layout. Business concepts live in `app/domains`, while
shared infrastructure lives in `app/core`.

```text
app/
├── core/
│   ├── database.py       # Tortoise configuration
│   ├── models.py         # Base model
│   ├── settings.py       # Application settings
│   └── viewsets.py       # Shared ViewSet defaults
├── domains/
│   └── project/
│       ├── filters.py    # Query parameters for this domain
│       ├── models.py     # Project and Task models
│       ├── schemas.py    # Explicit Pydantic schemas
│       └── views.py      # ViewSets and routers
└── main.py               # FastAPI app setup
```

Create structure:

```bash
mkdir -p app/core app/domains/project && \
touch app/__init__.py app/core/__init__.py app/domains/__init__.py app/domains/project/__init__.py && \
touch app/core/database.py app/core/models.py app/core/settings.py app/core/viewsets.py && \
touch app/domains/project/filters.py app/domains/project/models.py app/domains/project/schemas.py app/domains/project/views.py && \
touch app/main.py
```

## ⚙️ Project Setup

We will build a small project management API with projects and tasks:

- projects can be listed, created, updated, retrieved, and soft-deleted;
- tasks belong to projects;
- list endpoints support filters, ordering, wrappers, and pagination;
- project detail responses can include tasks;
- a custom stats action returns task counts;
- cache is initialized in the FastAPI lifespan.

### 1. Settings

```python title="app/core/settings.py"
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[2] / '.env'


class Settings(BaseSettings):
    database_url: str = Field(default='sqlite://db.sqlite3')
    redis_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=ROOT_ENV_FILE,
        env_file_encoding='utf-8',
        extra='allow',
    )


settings = Settings()
```

### 2. Base Model

```python title="app/core/models.py"
from datetime import datetime

from tortoise import fields
from tortoise.contrib.pydantic import PydanticModel
from tortoise.models import Model


class BaseModel(Model):
    id = fields.IntField(primary_key=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseCreateSchema(PydanticModel):
    pass


class BaseReadSchema(PydanticModel):
    id: int
    created_at: datetime
    updated_at: datetime
```

### 3. Database Configuration

```python title="app/core/database.py"
from fastapi import FastAPI
from tortoise import Tortoise
from tortoise.contrib.fastapi import register_tortoise

from app.core.settings import settings

MODELS = [
    'app.domains.project.models',
]

TORTOISE_ORM = {
    'connections': {'default': settings.database_url},
    'apps': {
        'models': {
            'models': MODELS,
            'default_connection': 'default',
            'migrations': 'migrations',
        }
    },
}


def register_database(app: FastAPI):
    register_tortoise(
        app,
        db_url=settings.database_url,
        modules={'models': MODELS},
        add_exception_handlers=True,
    )


Tortoise.init_models(MODELS, 'models')
```

!!! tip "Why init_models?"
    Tortoise needs relation metadata before Pydantic schemas are imported. Calling
    `Tortoise.init_models()` in your database module makes schema imports stable.

### 4. Shared ViewSet Defaults

```python title="app/core/viewsets.py"
from fastapi_ronin.pagination import PageNumberPagination
from fastapi_ronin.types import ModelType
from fastapi_ronin.viewsets import ModelViewSet
from fastapi_ronin.wrappers import PaginatedResponseDataWrapper, ResponseDataWrapper


class BaseModelViewSet(ModelViewSet[ModelType]):
    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
    single_wrapper = ResponseDataWrapper
```

### 5. Domain Models

```python title="app/domains/project/models.py"
from tortoise import fields

from app.core.models import BaseModel


class Project(BaseModel):
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    active = fields.BooleanField(default=True)
    tasks = fields.ReverseRelation['Task']

    class Meta:
        ordering = ['-created_at']


class Task(BaseModel):
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    completed = fields.BooleanField(default=False)
    project = fields.ForeignKeyField('models.Project', related_name='tasks')
```

### 6. Explicit Schemas

```python title="app/domains/project/schemas.py"
from fastapi_ronin.decorators import schema
from pydantic import BaseModel

from app.core.models import BaseCreateSchema, BaseReadSchema
from app.domains.project.models import Project, Task


@schema(Task)
class TaskCreateSchema(BaseCreateSchema):
    name: str
    description: str | None = None
    project_id: int


@schema(Task)
class TaskReadSchema(TaskCreateSchema, BaseReadSchema):
    completed: bool


@schema(Project)
class ProjectCreateSchema(BaseCreateSchema):
    name: str
    description: str | None = None


@schema(Project)
class ProjectReadSchema(ProjectCreateSchema, BaseReadSchema):
    active: bool


@schema(Project)
class ProjectDetailSchema(ProjectReadSchema):
    tasks: list[TaskReadSchema] = []


class ProjectStatsSchema(BaseModel):
    project_id: int
    completed: int = 0
    incomplete: int = 0
```

!!! tip "Explicit is safer"
    New ORM fields do not leak into your API until you add them to a schema.
    This is especially important for internal flags, ownership fields, tokens,
    and audit data.

### 7. Filters

```python title="app/domains/project/filters.py"
from tortoise.expressions import Q
from tortoise.queryset import QuerySet

from app.domains.project.models import Project, Task
from fastapi_ronin.filters import BooleanFilter, CharFilter, DateTimeFilter, FilterSet, OrderingFilter, Parameter


class ProjectFilterSet(FilterSet):
    fields = [
        CharFilter(field_name='search', method='filter_by_search'),
        BooleanFilter(field_name='active'),
        DateTimeFilter(field_name='created_at', lookups=['gte', 'lte', 'exact']),
    ]
    ordering = OrderingFilter(
        fields=(
            'name',
            ('created', 'created_at'),
            ('updated', 'updated_at'),
        ),
        default=('-created',),
    )

    def filter_by_search(self, queryset: QuerySet[Project], value: str, parameter: Parameter):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))

    class Meta:
        model = Project


class TaskFilterSet(FilterSet):
    fields = [
        CharFilter(field_name='search', method='filter_by_search'),
        BooleanFilter(field_name='completed'),
    ]

    def filter_by_search(self, queryset: QuerySet[Task], value: str, parameter: Parameter):
        return queryset.filter(Q(name__icontains=value) | Q(description__icontains=value))

    class Meta:
        model = Task
```

### 8. ViewSets

```python title="app/domains/project/views.py"
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_ronin.cache import cache
from fastapi_ronin.decorators import action, viewset
from fastapi_ronin.pagination import PageNumberPagination
from fastapi_ronin.wrappers import PaginatedResponseDataWrapper

from app.core.viewsets import BaseModelViewSet
from app.domains.project.filters import ProjectFilterSet, TaskFilterSet
from app.domains.project.models import Project, Task
from app.domains.project.schemas import (
    ProjectCreateSchema,
    ProjectDetailSchema,
    ProjectReadSchema,
    ProjectStatsSchema,
    TaskCreateSchema,
    TaskReadSchema,
)

projects_router = APIRouter(prefix='/projects', tags=['projects'])
tasks_router = APIRouter(prefix='/tasks', tags=['tasks'])


@viewset(projects_router)
class ProjectViewSet(BaseModelViewSet[Project]):
    model = Project
    read_schema = ProjectDetailSchema
    many_read_schema = ProjectReadSchema
    create_schema = ProjectCreateSchema
    filterset_class = ProjectFilterSet

    def get_queryset(self):
        return Project.filter(active=True).prefetch_related('tasks')

    async def perform_destroy(self, obj: Project):
        obj.active = False
        await obj.save()

    @action(methods=['GET'], detail=True)
    async def stats(self, item_id: int) -> ProjectStatsSchema:
        cache_key = f'project:{item_id}:stats'
        cached = await cache.get(cache_key)
        if cached:
            return ProjectStatsSchema(**cached)

        project = await self.get_object(item_id)
        tasks = Task.filter(project=project)
        result = ProjectStatsSchema(
            project_id=project.id,
            completed=await tasks.filter(completed=True).count(),
            incomplete=await tasks.filter(completed=False).count(),
        )
        await cache.set(cache_key, result.model_dump(), ttl=60)
        return result


@viewset(tasks_router)
class TaskViewSet(BaseModelViewSet[Task]):
    model = Task
    read_schema = TaskReadSchema
    create_schema = TaskCreateSchema
    filterset_class = TaskFilterSet

    @action(methods=['GET'])
    async def list(
        self, pagination: PageNumberPagination = Depends(PageNumberPagination.build), project_id: int = Query(...)
    ) -> PaginatedResponseDataWrapper[TaskReadSchema, PageNumberPagination]:
        queryset = Task.filter(project_id=project_id)
        return await self.get_paginated_response(queryset=queryset, pagination=pagination)

    async def before_save(self, obj: Task):
        await obj.fetch_related('project')
        if obj.project.active is False:
            raise HTTPException(status_code=400, detail='Project is not active')
```

### 9. FastAPI Application

```python title="app/main.py"
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi_ronin.cache import cache

from app.core.database import register_database
from app.core.settings import settings
from app.domains.project.views import projects_router, tasks_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await cache.init(redis_url=settings.redis_url)
    yield
    await cache.close()


app = FastAPI(
    title='Project Management API',
    description='A project management API built with FastAPI Ronin',
    version='1.0.0',
    lifespan=lifespan,
)

register_database(app)
app.include_router(projects_router)
app.include_router(tasks_router)
```

### 10. Run your app


```toml title="Add to pyproject.toml"
[tool.tortoise]
tortoise_orm = "app.core.database.TORTOISE_ORM"
```

```bash title="Run migrations"
tortoise makemigrations
tortoise migrate
```

```bash
uv run uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs`.

## 🎉 What You Get

### Project Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/projects/` | List active projects with filters, ordering, pagination, and wrappers |
| `POST` | `/projects/` | Create a project |
| `GET` | `/projects/{item_id}/` | Get project details with tasks |
| `PUT` | `/projects/{item_id}/` | Update a project |
| `PATCH` | `/projects/{item_id}/` | Partially update a project |
| `DELETE` | `/projects/{item_id}/` | Soft-delete a project |
| `GET` | `/projects/{item_id}/stats/` | Get cached project stats |

### Task Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/tasks/?project_id=1` | List tasks for one project |
| `POST` | `/tasks/` | Create a task |
| `GET` | `/tasks/{item_id}/` | Get task details |
| `PUT` | `/tasks/{item_id}/` | Update a task |
| `PATCH` | `/tasks/{item_id}/` | Partially update a task |
| `DELETE` | `/tasks/{item_id}/` | Delete a task |

## 📋 API Response Examples

### List Projects

```json title="GET /projects/?page=1&size=10&search=website"
{
  "data": [
    {
      "id": 1,
      "name": "Website Redesign",
      "description": "Complete overhaul of company website",
      "active": true,
      "created_at": "2026-01-15T11:00:00Z",
      "updated_at": "2026-01-15T11:00:00Z"
    }
  ],
  "meta": {
    "page": 1,
    "size": 10,
    "total": 1,
    "pages": 1
  }
}
```

### Project Detail

```json title="GET /projects/1/"
{
  "data": {
    "id": 1,
    "name": "Website Redesign",
    "description": "Complete overhaul of company website",
    "active": true,
    "tasks": [
      {
        "id": 1,
        "name": "Design mockups",
        "description": "Create UI/UX mockups",
        "project_id": 1,
        "completed": false,
        "created_at": "2026-01-15T12:00:00Z",
        "updated_at": "2026-01-15T12:00:00Z"
      }
    ],
    "created_at": "2026-01-15T11:00:00Z",
    "updated_at": "2026-01-15T11:00:00Z"
  }
}
```

### Project Stats

```json title="GET /projects/1/stats/"
{
  "project_id": 1,
  "completed": 3,
  "incomplete": 7
}
```

## 👋 Adding Authentication

Ronin does not force an auth system. Use FastAPI dependencies and put the user
into Ronin state.

```python title="app/core/auth.py"
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_ronin.state import BaseStateManager

security = HTTPBearer(auto_error=False)


async def get_current_user(credentials: HTTPAuthorizationCredentials | None = Depends(security)):
    if credentials and credentials.credentials == 'token':
        user = {'id': 1, 'email': 'admin@example.com'}
        BaseStateManager.set_user(user)
        return user
    return None
```

Apply it globally:

```python title="app/main.py"
from fastapi import Depends, FastAPI
from app.core.auth import get_current_user

app = FastAPI(dependencies=[Depends(get_current_user)])
```

## 🛡️ Adding Permissions

```python title="app/domains/project/views.py"
from fastapi_ronin.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly


@viewset(projects_router)
class ProjectViewSet(BaseModelViewSet[Project]):
    # permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        if self.action in ('stats', 'list', 'retrieve'):
            return []
        return [IsAuthenticated()]
```

## 💡 Tips

!!! tip "Domains Architecture"
    Keep each domain focused: models, schemas, filters, and views for one
    business concept should live together.

!!! tip "Base ViewSets"
    Put shared defaults in `app/core/viewsets.py`: pagination, wrappers,
    permission defaults, or shared helper methods.

## 🎯 Next Steps

- [ViewSets](viewsets/index.md) - learn the core ViewSet model
- [Schemas](schemas.md) - design explicit request and response contracts
- [Filters](filters.md) - add query parameters and ordering
- [Cache](cache.md) - configure in-memory or Redis-backed cache
- [Permissions](permissions.md) - protect write operations
- [Pagination](pagination.md) - tune list endpoints
- [Response Wrappers](wrappers.md) - standardize API responses
