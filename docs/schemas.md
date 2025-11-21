---
title: FastAPI Schema Generation — Build Secure APIs with Tortoise ORM and Mason
description: Generate flexible, secure API schemas in FastAPI Ronin using Tortoise ORM models and meta class configurations. Control your API fields easily and streamline Python API development.
keywords: FastAPI schemas, Tortoise ORM, API schema generation, Pydantic models, FastAPI serialization, API field control, Python backend development, REST API schemas, schema customization FastAPI, FastAPI Ronin
---

# Schemas & Meta: FastAPI Ronin Schema Generation with Tortoise ORM

FastAPI Ronin offers a powerful schema generation system based on your Tortoise ORM models. Using meta class configurations, you can precisely control which fields appear in your API schemas, making it easy to build secure, flexible, and well-structured REST APIs.

FastAPI Ronin extends the functionality of `pydantic_model_creator` from Tortoise ORM, providing more flexible and secure schema generation for FastAPI.

The `config` parameter uses `PydanticMetaData`, allowing you to apply all standard Tortoise options. For more details on available features and configurations, refer to the [official Tortoise documentation](https://tortoise.github.io/contrib/pydantic.html).

## Overview

The schema system consists of three main components:

1. **SchemaMeta** - Defines which fields to include/exclude
2. **build_schema()** - Creates Pydantic models from Tortoise models
3. **rebuild_schema()** - Modifies existing schemas for different use cases

## SchemaMeta Classes

SchemaMeta classes define the field configuration for your schemas:

```python
from fastapi_ronin.schemas import SchemaMeta

class ProjectMeta(SchemaMeta):
    include = (
        'id',
        'name',
        'description',
        'created_at',
        'updated_at',
    )
    optional = ('description',)
```

### SchemaMeta Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `include` | `Tuple[str, ...]` | Fields to include in the schema |
| `exclude` | `Tuple[str, ...]` | Fields to exclude from the schema |
| `optional` | `Tuple[str, ...]` | Fields that should be optional |
| `computed` | `Tuple[str, ...]` | Computed/derived fields |

!!! tip "Best Practice: Use include instead of exclude"
    Always prefer `include` over `exclude` for better control when adding new fields to your models. This prevents accidentally exposing sensitive data when new fields are added.

## Basic Schema Generation

### Simple Schema

```python title="app/domains/project/models.py"
from tortoise import fields
from app.core.models import BaseModel

class Project(BaseModel):
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    active = fields.BooleanField(default=True)
```


```python title="app/domains/project/meta.py"
from app.core.models import BASE_FIELDS
from fastapi_ronin.schemas import SchemaMeta

class ProjectMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,  # id, created_at, updated_at
        'name',
        'description',
        'active',
    )
```

```python title="app/domains/project/schemas.py"
from fastapi_ronin.schemas import build_schema, rebuild_schema
from app.domains.project.models import Project
from app.domains.project.meta import ProjectMeta

# Generate read schema (includes all fields)
ProjectReadSchema = build_schema(Project, meta=ProjectMeta)

# Generate create schema (excludes readonly fields)
ProjectCreateSchema = rebuild_schema(
    ProjectReadSchema,
    exclude_readonly=True
)
```

## Handling Relationships

### Models with ForeignKey

```python title="app/domains/project/models.py"
class Project(BaseModel):
    name = fields.CharField(max_length=255)
    description = fields.TextField(null=True)

class Task(BaseModel):
    name = fields.CharField(max_length=255)
    completed = fields.BooleanField(default=False)
    project = fields.ForeignKeyField('models.Project', related_name='tasks')
```

### Meta Classes for Relationships

```python title="app/domains/project/meta.py"
from fastapi_ronin.schemas import SchemaMeta, build_schema_meta

class ProjectMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,
        'name',
        'description',
    )

class TaskMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,
        'name',
        'completed',
        'project_id',  # Include foreign key ID
    )

# Create meta for nested schemas with relationships
def get_project_with_tasks_meta():
    """Project schema with embedded tasks"""
    return build_schema_meta(
        ProjectMeta,
        ('tasks', get_task_with_project_meta()),
    )

def get_task_with_project_meta():
    """Task schema with embedded project data"""
    return build_schema_meta(TaskMeta, ('project', ProjectMeta))
```

### Schema Generation with Relationships

```python title="app/domains/project/schemas.py"
from fastapi_ronin.schemas import ConfigSchemaMeta, build_schema, rebuild_schema

# Simple schemas
ProjectReadSchema = build_schema(Project, meta=ProjectMeta)
TaskReadSchema = build_schema(Task, meta=get_task_with_project_meta())

# Detailed project schema with tasks (handles circular references)
ProjectDetailSchema = build_schema(
    Project,
    meta=get_project_with_tasks_meta(),
    config=ConfigSchemaMeta(allow_cycles=True),  # Handle circular references
)

# Create schemas (exclude readonly fields)
ProjectCreateSchema = rebuild_schema(ProjectReadSchema, exclude_readonly=True)
TaskCreateSchema = rebuild_schema(TaskReadSchema, exclude_readonly=True)
```

## Schema Rebuilding

The `rebuild_schema()` function allows you to create variations of existing schemas:

```python
# Original schema includes all fields
ProjectReadSchema = build_schema(Project, meta=ProjectMeta)

# Create schema excludes readonly fields like id, created_at, updated_at
ProjectCreateSchema = rebuild_schema(
    ProjectReadSchema,
    exclude_readonly=True
)

# Create schema with different meta
ProjectMinimalSchema = rebuild_schema(
    ProjectReadSchema,
    meta=MinimalProjectMeta,
    name="ProjectMinimalSchema"
)
```

## Configuration Options

### ConfigSchemaMeta

Use `ConfigSchemaMeta` for advanced configuration:

```python
from fastapi_ronin.schemas import ConfigSchemaMeta

# Allow circular references in relationships
config = ConfigSchemaMeta(allow_cycles=True)

# Custom configuration
config = ConfigSchemaMeta(
    allow_cycles=True,
    exclude=('internal_field',),
    include=('custom_field',),
)

schema = build_schema(
    Project,
    meta=ProjectMeta,
    config=config
)
```

## Type Hints for IDE Support

Improve IDE support with type hints:

```python
from typing import TYPE_CHECKING
from tortoise.contrib.pydantic import PydanticModel

# Runtime schema generation
ProjectSchema = build_schema(Project, meta=ProjectMeta)

# Type hints for IDE
if TYPE_CHECKING:
    ProjectSchema = type('ProjectSchema', (Project, PydanticModel), {})
```

## Best Practices

### 1. Use Base Field Sets

```python
# Define common field sets
BASE_FIELDS = ('id', 'created_at', 'updated_at')

class ProjectMeta(SchemaMeta):
    include = (
        *BASE_FIELDS,
        'name',
        'description',
    )
```

### 2. Prefer include over exclude

```python
# ✅ Good: Explicit control over exposed fields
class ProjectMeta(SchemaMeta):
    include = (
        'id',
        'name',
        'description',
        'created_at',
    )

# ❌ Avoid: May accidentally expose new fields
class ProjectMeta(SchemaMeta):
    exclude = ('password', 'secret_key')
```

### 3. Organize by Use Case

```python
# Different schemas for different API responses
class ProjectMetas:
    class List(SchemaMeta):
        include = ('id', 'name', 'created_at')

    class Detail(SchemaMeta):
        include = ('id', 'name', 'description', 'created_at', 'updated_at')

    class Create(SchemaMeta):
        include = ('name', 'description')

# Use specific meta for different contexts
ProjectListSchema = build_schema(Project, meta=ProjectMetas.List)
ProjectDetailSchema = build_schema(Project, meta=ProjectMetas.Detail)
```

## Common Patterns

### API Response Schemas

```python
# Different schemas for different API responses
ProjectListSchema = build_schema(Project, meta=ProjectListMeta)  # Minimal fields
ProjectDetailSchema = build_schema(Project, meta=ProjectDetailMeta)  # Full fields
ProjectCreateSchema = rebuild_schema(ProjectDetailSchema, exclude_readonly=True)
```

### Schema Naming

```python
# Explicit naming for better OpenAPI documentation
ProjectReadSchema = build_schema(
    Project,
    meta=ProjectMeta,
    name="ProjectResponse"
)

ProjectCreateSchema = rebuild_schema(
    ProjectReadSchema,
    exclude_readonly=True,
    name="ProjectCreateRequest"
)
```

The schema system in FastAPI Ronin provides the flexibility to create exactly the API schemas you need while maintaining clean separation between your data models and API contracts.
