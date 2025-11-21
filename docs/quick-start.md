---
title: FastAPI Ronin Tutorial — Quick Start Guide to Building REST APIs
description: Learn how to build REST APIs quickly with FastAPI Ronin. Follow this step-by-step tutorial to use ViewSets, permissions, and automatic CRUD operations.
keywords: FastAPI tutorial, FastAPI Ronin tutorial, REST API guide, Python REST API tutorial, Django REST Framework patterns, CRUD API FastAPI, ViewSets FastAPI, Python backend development, API development tutorial
---

# FastAPI Ronin Quick Start: Build REST APIs in Minutes

Get started with FastAPI Ronin and build your first REST API fast! This step-by-step guide shows how to install FastAPI Ronin and structure your project using familiar patterns like ViewSets, permissions, and automatic CRUD operations.

## 📦 Installation

Install FastAPI Ronin using pip:

```bash
uv add fastapi-ronin
```

You'll also need FastAPI and an ORM. FastAPI Ronin works great with Tortoise ORM:

```bash
uv add fastapi tortoise-orm
```

## 🏗️ Recommended Project Structure

Before diving into code, we **recommend using a domains architecture** for your FastAPI projects. This approach organizes your code by business domains rather than technical layers, making it more maintainable and scalable.

Here's the recommended structure:

```
your_project/
├── app/
│   ├── core/                 # Shared utilities and base classes
│   │   ├── models.py         # BaseModel and common fields
│   │   ├── database.py       # Database configuration
│   │   ├── viewsets.py       # The main viewsets for the entire application
│   │   └── settings.py       # Application settings
│   ├── domains/              # Business domains
│   │   └── project/
│   │       ├── models.py     # Business models
│   │       ├── meta.py       # Schema metadata
│   │       ├── schemas.py    # Pydantic schemas
│   │       └── views.py      # API endpoints
│   └── main.py               # FastAPI application setup
```

This structure provides:

- **Clear separation** of business concerns
- **Easy navigation** and understanding
- **Better testability** and maintainability
- **Natural scaling** as your project grows

## ⚙️ Project Setup

Let's build a project management API with related tasks to demonstrate FastAPI Ronin's capabilities with linked models.

### 1. Create Base Model

First, create a base model with common fields:

```python title="app/core/models.py"
from tortoise import fields
from tortoise.models import Model

class BaseModel(Model):
    id = fields.IntField(primary_key=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        abstract = True

BASE_FIELDS = ('id', 'created_at', 'updated_at')
```

### 2. Basic viewset for easy reuse

```python title="app/core/viewsets.py"
from fastapi_ronin.pagination import PageNumberPagination
from fastapi_ronin.viewsets import ModelViewSet
from fastapi_ronin.types import ModelType
from fastapi_ronin.wrappers import PaginatedResponseDataWrapper, ResponseDataWrapper


class BaseViewSet(ModelViewSet[ModelType]):
    pagination = PageNumberPagination
    list_wrapper = PaginatedResponseDataWrapper
    single_wrapper = ResponseDataWrapper
```

### 3. Define Your Models

Create your Tortoise ORM models with ForeignKey relationships:

```python title="app/domains/project/models.py"
from tortoise import fields
from app.core.models import BaseModel

class Project(BaseModel):
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    active = fields.BooleanField(default=True)
    # Reverse relation to tasks will be available as 'tasks' automaticly

class Task(BaseModel):
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    completed = fields.BooleanField(default=False)
    project: fields.ForeignKeyRelation[Project] = fields.ForeignKeyField("models.Project", related_name="tasks")
```

### 4. Create Schema Meta Classes

Define which fields to include in your API schemas and how to handle relationships:

```python title="app/domains/project/meta.py"
from app.core.models import BASE_FIELDS
from fastapi_ronin.schemas import SchemaMeta, build_schema_meta


class ProjectMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,
        "name",
        "description",
    )


class TaskMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,
        "name",
        "description",
        "completed",
        "project_id",  # Include foreign key ID
    )


# Create meta for nested schemas with relationships
def get_project_with_tasks_meta():
    """Project schema with embedded tasks"""
    return build_schema_meta(
        ProjectMeta,
        ("tasks", get_task_with_project_meta()),
    )


def get_task_with_project_meta():
    """Task schema with embedded project data"""
    return build_schema_meta(TaskMeta, ("project", ProjectMeta))
```

### 5. Generate Schemas

Use FastAPI Ronin's schema generation to create Pydantic models for related data:

```python title="app/domains/project/schemas.py"
from typing import TYPE_CHECKING
from pydantic import BaseModel
from tortoise import Tortoise
from tortoise.contrib.pydantic import PydanticModel

from app.domains.project.meta import (
    ProjectMeta,
    get_project_with_tasks_meta,
    get_task_with_project_meta,
)
from app.domains.project.models import Project, Task
from fastapi_ronin.schemas import ConfigSchemaMeta, build_schema, rebuild_schema

"""
https://tortoise.github.io/examples/pydantic.html?h=init_models#early-model-init
Set up models in advance here or place them in database.py (example)
https://github.com/bubaley/fastapi-ronin/blob/main/app/core/database.py
"""
Tortoise.init_models(["app.domains.project.models"], "models")

# Simple project schema
ProjectReadSchema = build_schema(Project, meta=ProjectMeta)

# Detailed project schema with tasks (handles circular references)
ProjectDetailSchema = build_schema(
    Project,
    meta=get_project_with_tasks_meta(),
    config=ConfigSchemaMeta(allow_cycles=True),  # Handle circular references
)

# Create schemas (exclude readonly fields)
ProjectCreateSchema = rebuild_schema(ProjectReadSchema, exclude_readonly=True)


class ProjectStatsSchema(BaseModel):
    project_id: int
    completed: int = 0
    incomplete: int = 0


# Task schemas
TaskReadSchema = build_schema(Task, meta=get_task_with_project_meta())
TaskCreateSchema = rebuild_schema(TaskReadSchema, exclude_readonly=True)

# Type checking support
if TYPE_CHECKING:
    ProjectReadSchema = type("ProjectReadSchema", (Project, PydanticModel), {})
    ProjectCreateSchema = type("ProjectCreateSchema", (Project, PydanticModel), {})
    ProjectDetailSchema = type("ProjectDetailSchema", (Project, PydanticModel), {})
    TaskReadSchema = type("TaskReadSchema", (Task, PydanticModel), {})
    TaskCreateSchema = type("TaskCreateSchema", (Task, PydanticModel), {})
```

### 6. Create Your ViewSets

Now create ViewSets for both models with relationship handling:

```python title="app/domains/project/views.py"
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi_ronin.decorators import action, viewset
from fastapi_ronin.pagination import PageNumberPagination
from fastapi_ronin.wrappers import PaginatedResponseDataWrapper

from app.core.viewsets import BaseViewSet
from app.domains.project.models import Project, Task
from app.domains.project.schemas import (
    ProjectDetailSchema,
    ProjectReadSchema,
    ProjectCreateSchema,
    ProjectStatsSchema,
    TaskCreateSchema,
    TaskReadSchema,
)

projects_router = APIRouter(prefix="/projects", tags=["projects"])
tasks_router = APIRouter(prefix="/tasks", tags=["tasks"])


@viewset(projects_router)
class ProjectViewSet(BaseViewSet[Project]):
    model = Project
    read_schema = ProjectDetailSchema
    many_read_schema = ProjectReadSchema
    create_schema = ProjectCreateSchema

    def get_queryset(self):
        """Override get_queryset method"""
        return Project.filter(active=True)

    async def perform_destroy(self, obj: Project):
        """Override perform_destroy method"""
        obj.active = False
        await obj.save()
        return obj

    @action(methods=["GET"], detail=True, response_model=ProjectStatsSchema)
    async def stats(self, item_id: int):
        """Get stats for a project"""
        project = await self.get_object(item_id)
        tasks = Task.filter(project=project)
        return ProjectStatsSchema(
            project_id=project.id,
            completed=await tasks.filter(completed=True).count(),
            incomplete=await tasks.filter(completed=False).count(),
        )


@viewset(tasks_router)
class TaskViewSet(BaseViewSet[Task]):
    model = Task
    read_schema = TaskReadSchema
    create_schema = TaskCreateSchema

    @action(methods=["GET"], response_model=PaginatedResponseDataWrapper[TaskReadSchema, PageNumberPagination])
    async def list(
        self,
        pagination: PageNumberPagination = Depends(PageNumberPagination.build),
        project_id: bool = Query(...),
    ):
        """Override list method"""
        queryset = self.get_queryset().filter(project_id=project_id)
        return await self.get_paginated_response(queryset=queryset, pagination=pagination)

    async def before_save(self, obj: Task):
      """Before save hook"""
        await obj.fetch_related("project")
        if obj.project.active is False:
            raise HTTPException(status_code=400, detail="Project is not active")
```

### 7. Setup FastAPI Application

Wire everything together in your main application:

```python title="app/main.py"
from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from app.domains.project.views import router as projects_router, tasks_router

app = FastAPI(
    title="Project Management API",
    description="A project management API built with FastAPI Ronin",
    version="1.0.0"
)

# Register database here or in database.py
register_tortoise(
    app,
    db_url="sqlite://db.sqlite3",
    modules={"models": ["app.domains.project.models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

# Include ViewSet router
app.include_router(projects_router)
app.include_router(tasks_router)
```

### 8. Run Your API

Start the development server:

```bash
uvicorn app.main:app --reload
```

## 🎉 What You Get

Check Your API `http://localhost:8000/docs` with these endpoints:

### Project Endpoints

| Method   | Endpoint                   | Description               |
| -------- | -------------------------- | ------------------------- |
| `GET`    | `/projects/`               | List projects (paginated) |
| `POST`   | `/projects/`               | Create new project        |
| `GET`    | `/projects/{item_id}/`          | Get project with tasks    |
| `PUT`    | `/projects/{item_id}/`          | Update project            |
| `DELETE` | `/projects/{item_id}/`          | Delete project            |
| `GET`    | `/projects/{item_id}/stats/`    | Get stats for project |

And tasks endpoints.

## 📋 API Response Examples

### List Projects

```json title="GET /projects/?page=1&size=10"
{
  "data": [
    {
      "id": 1,
      "name": "Website Redesign",
      "description": "Complete overhaul of company website",
      "created_at": "2024-01-15T11:00:00Z",
      "updated_at": "2024-01-15T11:00:00Z"
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

### Get Project Details (with tasks)

```json title="GET /projects/1/"
{
  "data": {
    "id": 1,
    "name": "Website Redesign",
    "description": "Complete overhaul of company website",
    "tasks": [
      {
        "id": 1,
        "name": "Design mockups",
        "description": "Create UI/UX mockups for the new website",
        "completed": false,
        "project": {
          "id": 1,
          "name": "Website Redesign",
          "description": "Complete overhaul of company website",
        },
        "created_at": "2024-01-15T12:00:00Z",
        "updated_at": "2024-01-15T12:00:00Z"
      }
    ],
    "created_at": "2024-01-15T11:00:00Z",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

## 🔧 Key Features Demonstrated

### 1. **Relationship Handling**

- ForeignKey and related objects are automatically included in schemas using `build_schema_meta`.
- Nested object serialization (e.g., project with tasks, task with project).
- Circular reference support with `ConfigSchemaMeta(allow_cycles=True)`.

### 2. **Flexible Schema Generation**

- Different schemas for list and detail views.
- Customizable field inclusion through meta classes (`SchemaMeta`, `build_schema_meta`).
- Generation of nested schemas for related models.

### 3. **Base and Custom ViewSets**

- Rapid creation of CRUD endpoints using `ModelViewSet` and `BaseViewSet`.
- Overriding methods (`get_queryset`, `perform_destroy`, `before_save`) for business logic.
- Built-in pagination and response wrappers (`PageNumberPagination`, `PaginatedResponseDataWrapper`).

### 4. **Custom Actions and Routes**

- Easy addition of custom endpoints with the `@action` decorator.
- Automatic routing and OpenAPI documentation for custom and overiding methods (e.g., `stats` for project, `list` with project_id filter for tasks).

## 👋 Adding Authentication

Want to add authentication? It's easy with state management:

```python title="app/core/auth.py"
from typing import Optional
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi_ronin.state import BaseStateManager


class OptionalHTTPBearer(HTTPBearer):
    async def __call__(self, request: Request) -> Optional[HTTPAuthorizationCredentials]:
        credentials: Optional[HTTPAuthorizationCredentials] = None
        try:
            credentials = await super().__call__(request)
        except HTTPException:
            # No credentials provided — allow anonymous
            return None
        return credentials


async def get_current_user(token: Optional[HTTPAuthorizationCredentials] = Depends(OptionalHTTPBearer())):
    if token and token.credentials == "token":  # Your logic
        user = {"id": 1, "username": "john"}
        BaseStateManager.set_user(user)
        return user
    return None
```

Then add it as app dependency or or to the required routers:

```python title="app/main.py"
from app.core.auth import get_current_user

app = FastAPI(dependencies=[Depends(get_current_user)])
```

## 🛡️ Adding Permissions

Protect your endpoints with permission classes:

```python title="app/domains/project/views.py"
from fastapi_ronin.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

@viewset(router)
class ProjectViewSet(ModelViewSet[Project]):
    # ... other configuration ...

    # permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        # Custom permissions per action
        if self.action in ['add_task', 'tasks', 'complete']:
            return [IsAuthenticated()]
        return []
```

## 🎯 Next Steps

Congratulations! You've built a complete REST API with related models using FastAPI Ronin. Here's what to explore next:

- **[ViewSets](viewsets/index.md)** - Learn about advanced ViewSet features
- **[Meta & Schemas](schemas.md)** - Master schema generation and relationships
- **[Permissions](permissions.md)** - Implement complex authorization rules
- **[Pagination](pagination.md)** - Explore different pagination strategies
- **[State Management](state.md)** - Share data across your application
- **[Response Wrappers](wrappers.md)** - Customize API response formatting

## 💡 Tips

!!! tip "Domains Architecture"
    Keep your domains focused and cohesive. Each domain should represent a clear business concept with its own models, meta, schemas, and views.

!!! tip "Schema Flexibility"
    Use different meta classes for different use cases - simple schemas for lists, detailed schemas for single items, and minimal schemas for creation.
